import QtQuick 2.0
import "functions.js" as F
import UC 1.0
import "modrana_components"
import QtSensors 5.0 as Sensors

Page {
    id: tabMap
    property int buttonSize: 72
    property int mapTileScale : rWin.get(
    "mapScale", 1, function(v){mapTileScale=v})

    property bool showCompass : rWin.get("showQt5GUIMapCompass", true,
                                         function(v){tabMap.showCompass=v})
    property real compassOpacity : rWin.get("qt5GUIMapCompassOpacity", 0.7,
                                         function(v){tabMap.compassOpacity=v})

    function showOnMap(lat, lon) {
        pinchmap.setCenterLatLon(lat, lon);
        // show on map moves map center and
        // and thus disables centering
        center = false
    }

    property bool center : true
    property bool showModeOnMenuButton : rWin.get("showModeOnMenuButton", false,
    function(v){showModeOnMenuButton=v})

    property var pinchmap

    property alias layers : pinchmap.layers

    // routing related stuff
    property alias routing : routing
    property bool selectRoutingStart : false
    property bool selectRoutingDestination : false
    property bool routingStartSet: false
    property bool routingDestinationSet: false
    property real routingStartLat: 0.
    property real routingStartLon: 0.
    property real routingDestinationLat: 0.
    property real routingDestinationLon: 0.
    property bool routingRequestChanged : false
    property bool routingEnabled: false
    property bool routingP2P: true

    function enableRoutingUI(p2p) {
        // enable the routing UI (currently just the 1-3 buttons)
        if (p2p == null) {
            p2p = true
        }
        routingP2P = p2p
        routingEnabled = true
    }

    function disableRoutingUI() {
        // disable the routing UI & hide the route
        routingEnabled = false
        routingP2P = false
    }

    function setRoutingStart(lat, lon) {
        rWin.routingStartPos.latitude = lat
        rWin.routingStartPos.longitude = lon
        rWin.routingStartPos.isValid = true
        routingStartLat = lat
        routingStartLon = lon
        routingStartSet = true
    }

    function setRoutingDestination(lat, lon) {
        rWin.routingDestinationPos.latitude = lat
        rWin.routingDestinationPos.longitude = lon
        rWin.routingDestinationPos.isValid = true
        routingDestinationLat = lat
        routingDestinationLon = lon
        routingDestinationSet = true
    }

    Component.onCompleted : {
        rWin.log.info("map page: loaded, loading layers")
        pinchmap.loadLayers()
        rWin.log.info("map page: setting map center to: " +
                      rWin.lastGoodPos.latitude + "," +
                      rWin.lastGoodPos.longitude)
        pinchmap.setCenterLatLon(rWin.lastGoodPos.latitude, rWin.lastGoodPos.longitude)
        // report that the map page has been loaded,
        // so that startup feedback can be disabled
        rWin.firstPageLoaded = true
    }

    // if the page becomes active, activate the media keys so they can be used
    // for zooming; if the page is deactivated, deactivate them

    onIsActiveChanged: {
        rWin.actions.mediaKeysEnabled = tabMap.isActive
    }

    function getMap() {
        return pinchmap
    }

    PinchMap {
        id: pinchmap
        anchors.fill : parent
        property bool initialized : false
        zoomLevel: rWin.get("z", 11, setInitialZ)

        function setInitialZ (initialZ) {
            zoomLevel = initialZ
            initialized = true
        }

        tileScale : tabMap.mapTileScale
        name : "mainMap"

        layers : ListModel {
            ListElement {
                layerName : "OSM Mapnik"
                layerId: "mapnik"
                layerOpacity: 1.0
            }
        }

        canvas.visible : tabMap.routingEnabled
        canvas.onPaint : routing.paintRoute(canvas.getContext("2d"))

//        property var redrawStart : 0
//        canvas.onPaint : {
//            redrawStart = new Date().valueOf()
//            routing.paintRoute(canvas.getContext("2d"))
//        }
//        canvas.onPainted : {
//            var currentTime = new Date().valueOf()
//            rWin.log.debug("Canvas redraw time: " + (currentTime - redrawStart) + " ms")
//        }

        onZoomLevelChanged : {
            // save zoom level
            if (pinchmap.initialized) {
                // only save the changed zoom level
                // once the map page is properly initialized
                // (we don't want to save the initial placeholder value)
                rWin.set("z", parseInt(zoomLevel))
            }
        }

        Connections {
            target: rWin
            onPosChanged: {
                //rWin.log.debug("map page: fix changed")
                // this callback is used to keep the map centered when the current position changes
                if (tabMap.center && ! updateTimer.running) {
                    //rWin.log.debug("map page: Update from GPS position")
                    pinchmap.setCenterLatLon(rWin.lastGoodPos.latitude, rWin.lastGoodPos.longitude);
                    updateTimer.start();
                } else if (tabMap.center) {
                    rWin.log.debug("map page: Update timer preventing another update.");
                }
            }
        }

        Connections {
            target: rWin.actions
            onZoomUp : {
                console.log("UP")
                pinchmap.zoomOut()
            }
            onZoomDown : {
                console.log("DOWN")
                pinchmap.zoomIn()
            }
        }

        onDrag : {
            // disable map centering once drag is detected
            tabMap.center = false
        }

        Timer {
            id: updateTimer
            interval: 500
            repeat: false
        }

        // Rotating the map for fun and profit.
        // angle: -compass.azimuth

        showCurrentPosition: true
        currentPositionValid: rWin.llValid
        currentPositionLat: rWin.lastGoodPos.latitude
        currentPositionLon: rWin.lastGoodPos.longitude
        //currentPositionAzimuth: compass.azimuth
        //TODO: switching between GPS bearing & compass azimuth
        currentPositionAzimuth: rWin.bearing
        //currentPositionError: gps.lastGoodFix.error
        currentPositionError: 0
    }

    Item {
        id : routing
        property var touchpos: [0,0]
        property var routePoints : ListModel {
            id: routeModel
        }
        property var routeMessages : ListModel {
            id: routeMessageList
        }

        function paintRoute(ctx) {
            var offsetX = pinchmap.canvas.canvasWindow.x
            var offsetY = pinchmap.canvas.canvasWindow.y
            var thispos = (0,0,0)
            var messagePointDiameter = 10
            // clear the canvas
            ctx.clearRect(0,0,pinchmap.canvas.width,pinchmap.canvas.height)
            ctx.save()
            // The canvas has its x,y coordinates shifted to the upper left, so that
            // when it is moved during map panning, the offscreen parts of the route will
            // be visible and not cut off. Because of this we need to apply a translation
            // before we start drawing the route and related objects to take the shifted
            // origin into account.
            ctx.translate(pinchmap.width, pinchmap.height)
            if (tabMap.routingEnabled) {
                ctx.lineWidth = 10
                ctx.strokeStyle = Qt.rgba(0, 0, 0.5, 0.45)
                if(rWin.routingStartPos.isValid) {
                    // draw a semi-transparent line from start marker to start of the route
                    var startpos = pinchmap.getScreenpointFromCoord(rWin.routingStartPos.latitude,rWin.routingStartPos.longitude)
                    var startX = startpos[0]+offsetX
                    var startY = startpos[1]+offsetY
                    // only draw the lines when there is a route
                    if (routeMessages.count) {
                        var routeStart = routePoints.get(0)
                        var routeStartXY = pinchmap.getScreenpointFromCoord(routeStart.lat, routeStart.lon)
                        ctx.beginPath()
                        ctx.moveTo(startX, startY)
                        ctx.lineTo(routeStartXY[0], routeStartXY[1])
                        ctx.stroke()
                    }
                }

                if(rWin.routingDestinationPos.isValid) {
                    // draw a semi-transparent line from destination marker to end of the route
                    var destipos = pinchmap.getScreenpointFromCoord(rWin.routingDestinationPos.latitude,rWin.routingDestinationPos.longitude)
                    var destX = destipos[0]+offsetX
                    var destY = destipos[1]+offsetY
                    // only draw the lines when there is a route
                    if (routeMessages.count) {
                        var routeEnd = routePoints.get(routePoints.count-1)
                        var routeEndXY = pinchmap.getScreenpointFromCoord(routeEnd.lat, routeEnd.lon)
                        ctx.beginPath()
                        ctx.moveTo(destX, destY)
                        ctx.lineTo(routeEndXY[0], routeEndXY[1])
                        ctx.stroke()
                    }
                }

                // draw the step point background
                ctx.strokeStyle = Qt.rgba(0, 0, 0.5, 1.0)
                for (var i=0; i<routeMessages.count; i++) {
                    ctx.beginPath()
                    thispos = routeMessages.get(i)
                    destipos = pinchmap.getScreenpointFromCoord(thispos.lat,thispos.lon)
                    //ctx.ellipse(destipos[0]-messagePointDiameter,destipos[1]-messagePointDiameter, messagePointDiameter*2, messagePointDiameter*2)
                    ctx.arc(destipos[0],destipos[1], 3, 0, 2.0 * Math.PI)
                    ctx.stroke()
                }

                // draw the route
                ctx.beginPath()
                for (var i=0; i<routePoints.count; i++) {
                    thispos = routePoints.get(i)
                    destipos = pinchmap.getScreenpointFromCoord(thispos.lat,thispos.lon)
                    ctx.lineTo(destipos[0],destipos[1])
                }
                ctx.stroke()

                // draw the step points
                ctx.lineWidth = 7
                ctx.strokeStyle = Qt.rgba(1, 1, 0, 1)
                ctx.fillStyle = Qt.rgba(1, 1, 0, 1)
                for (var i=0; i<routeMessages.count; i++) {
                    ctx.beginPath()
                    thispos = routeMessages.get(i)
                    destipos = pinchmap.getScreenpointFromCoord(thispos.lat,thispos.lon)
                    ctx.beginPath()
                    ctx.arc(destipos[0],destipos[1], 2, 0, 2.0 * Math.PI)
                    ctx.stroke()
                    ctx.fill()
                }

                // now draw the start and end indicators so that they
                // are "above" the route and not obscured by it

                // place a red marker on the start point (if the point is set)
                if(rWin.routingStartPos.isValid) {
                    ctx.beginPath()
                    ctx.strokeStyle = Qt.rgba(1, 0, 0, 1)
                    ctx.fillStyle = Qt.rgba(1, 0, 0, 1)
                    ctx.moveTo(startX,startY)
                    // inner point
                    ctx.arc(startX, startY, 3, 0, 2.0 * Math.PI)
                    ctx.stroke()
                    ctx.fill()
                    // outer circle
                    ctx.beginPath()
                    ctx.strokeStyle = Qt.rgba(1, 0, 0, 0.95)
                    ctx.arc(startX, startY, 15, 0, 2.0 * Math.PI)
                    ctx.stroke()
                }

                // place a green marker at the destination point (if the point is set)
                if(rWin.routingDestinationPos.isValid) {
                    ctx.beginPath()
                    // place a red marker on the start point
                    ctx.strokeStyle = Qt.rgba(0, 1, 0, 1)
                    ctx.fillStyle = Qt.rgba(0, 1, 0, 1)
                    ctx.moveTo(destX, destY)
                    // inner point
                    ctx.arc(destX, destY, 3, 0, 2.0 * Math.PI)
                    ctx.stroke()
                    ctx.fill()
                    // outer circle
                    ctx.beginPath()
                    ctx.strokeStyle = Qt.rgba(0, 1, 0, 0.95)
                    ctx.arc(destX, destY, 15, 0, 2.0 * Math.PI)
                    ctx.stroke()
                }
            }
            ctx.restore()
        }

        Connections {
            // only connect to the PinchMap onClicked signal
            // when expecting start or destination input
            target : selectRoutingStart || selectRoutingDestination ? pinchmap : null
            onMapClicked: {
                routingRequestChanged = false
                // store the position we touched in Lat,Lon
                routing.touchpos = pinchmap.getCoordFromScreenpoint(screenX, screenY)
                if (selectRoutingStart) {
                    setRoutingStart(routing.touchpos[0],  routing.touchpos[1])
                    selectRoutingStart = false
                    routingRequestChanged = true
                }
                if (selectRoutingDestination) {
                    setRoutingDestination(routing.touchpos[0],  routing.touchpos[1])
                    selectRoutingDestination = false
                    routingRequestChanged = true
                }
                if (routingRequestChanged && routingStartSet && routingDestinationSet) {
                    // a (possibly new) route is needed
                    routing.requestRoute()
                }
                if (routingRequestChanged) {
                    // request a refresh of the canvas to
                    // display newly set start/destination point
                    pinchmap.canvas.requestPaint()
                }
            }
        }

        function requestRoute() {
            // request route for the current start and destination
            if (!routingStartSet) {
                rWin.log.error("can't get route: start not set")
                return false
            }
            if (!routingDestinationSet) {
                rWin.log.error("can't get route: destination not set")
                return false
            }
            if (!routingStartSet && !routingDestinationSet) {
                rWin.log.error("can't get route: start and destination not set")
                return false
            }
            rWin.python.call("modrana.gui.modules.route.llRoute", [[routingStartLat,routingStartLon], [routingDestinationLat, routingDestinationLon]])
            rWin.log.info("route requested")
            return true
        }

        Component.onCompleted: {
            rWin.python.setHandler("routeReceived", function(route, routeMessagePoints){
                // clear old route first
                routePoints.clear()
                routeMessages.clear()
                for (var i=0; i<route.length; i++) {
                    routePoints.append({"lat": route[i][0], "lon": route[i][1]});
                }
                for (var i=0; i<routeMessagePoints.length; i++) {
                    routeMessages.append({"lat": routeMessagePoints[i][0], "lon": routeMessagePoints[i][1], "message": routeMessagePoints[i][3]})
                }
                pinchmap.canvas.requestPaint()
            })
        }
    }

    Sensors.Compass {
        id : compass
        dataRate : 50
        active : tabMap.isActive && tabMap.showCompass
        property int old_value: 0
        onReadingChanged : {
            // fix for the "northern wiggle" originally
            // from Sailcompass by THP - Thanks! :)
            var new_value = -1.0 * compass.reading.azimuth
            if (Math.abs(old_value-new_value)>270){
                if (old_value > new_value){
                    new_value += 360.0
                }else{
                    new_value -= 360.0
                }
            }
            old_value = new_value
            compassImage.rotation = new_value
        }
    }

    Image {
        id: compassImage
        visible : tabMap.showCompass
        opacity : tabMap.compassOpacity
        // TODO: investigate how to replace this by an image loader
        // what about rendered size ?
        // also why are the edges of the image so jarred ?

        property string rosePath : if (rWin.qrc) {
            "qrc:/themes/" + rWin.theme.id +"/windrose-simple.svg"
        } else {
            "file://" + rWin.platform.themesFolderPath + "/" + rWin.theme.id +"/windrose-simple.svg"
        }

        //source: "qrc:/themes/" + rWin.theme.id +"/windrose-simple.svg"
        //source: "file://" + rWin.platform.themesFolderPath + "/" + rWin.theme.id +"/windrose-simple.svg"
        source : compassImage.rosePath
        transformOrigin: Item.Center

        Behavior on rotation {
            SmoothedAnimation{ velocity: -1; duration:100;maximumEasingTime: 100 }
        }


        anchors.left: tabMap.left
        anchors.leftMargin: rWin.c.style.main.spacingBig
        anchors.top: tabMap.top
        anchors.topMargin: rWin.c.style.main.spacingBig
        smooth: true
        width: Math.min(tabMap.width/4, tabMap.height/4)
        fillMode: Image.PreserveAspectFit
        z: 2

//        Image {
//            //property int angle: gps.targetBearing || 0
//            property int angle: 0
//            property int outerMargin: 0
//            id: arrowImage
//            //visible: (gps.targetValid && gps.lastGoodFix.valid)
//
//            // TODO: investigate how to replace this by an image loader
//            // what about rendered size ?
//            source: "../../../../themes/"+ rWin.theme.id +"/arrow_target.svg"
//            width: (compassImage.paintedWidth / compassImage.sourceSize.width)*sourceSize.width
//            fillMode: Image.PreserveAspectFit
//            x: compassImage.width/2 - width/2
//            y: arrowImage.outerMargin
//            z: 3
//            transform: Rotation {
//                origin.y: compassImage.height/2 - arrowImage.outerMargin
//                origin.x: arrowImage.width/2
//                angle: arrowImage.angle
//            }
//        }
    }
    Column {
        anchors.bottom: buttonsRight.top
        anchors.bottomMargin: rWin.c.style.map.button.margin * 2
        anchors.right: pinchmap.right
        anchors.rightMargin: rWin.c.style.map.button.margin
        spacing: rWin.c.style.map.button.spacing
        visible: tabMap.routingEnabled
        MapButton {
            id: routingStart
            text: qsTr("<b>start</b>")
            width: rWin.c.style.map.button.size * 1.25
            height: rWin.c.style.map.button.size
            checked : selectRoutingStart
            toggledColor : Qt.rgba(1, 0, 0, 0.7)
            visible: tabMap.routingEnabled && tabMap.routingP2P
            onClicked: {
                selectRoutingStart = !selectRoutingStart
                selectRoutingDestination = false
            }
        }
        MapButton {
            id: routingEnd
            text: qsTr("<b>end</b>")
            width: rWin.c.style.map.button.size * 1.25
            height: rWin.c.style.map.button.size
            checked : selectRoutingDestination
            toggledColor : Qt.rgba(0, 1, 0, 0.7)
            visible: tabMap.routingEnabled && tabMap.routingP2P
            onClicked: {
                selectRoutingStart = false
                selectRoutingDestination = !selectRoutingDestination
            }
        }
        MapButton {
            id: endRouting
            visible: tabMap.routingEnabled
            text: qsTr("<b>clear</b>")
            width: rWin.c.style.map.button.size * 1.25
            height: rWin.c.style.map.button.size
            onClicked: {
                selectRoutingStart = false
                selectRoutingDestination = false
                tabMap.routingEnabled = false
            }
        }
    }
    Row {
        id: buttonsRight
        anchors.bottom: pinchmap.bottom
        anchors.bottomMargin: rWin.c.style.map.button.margin
        anchors.right: pinchmap.right
        anchors.rightMargin: rWin.c.style.map.button.margin
        spacing: rWin.c.style.map.button.spacing
        MapButton {
            iconName: "plus_small.png"
            onClicked: {pinchmap.zoomIn() }
            width: rWin.c.style.map.button.size
            height: rWin.c.style.map.button.size
            enabled : pinchmap.zoomLevel != pinchmap.maxZoomLevel
        }
        MapButton {
            iconName: "minus_small.png"
            onClicked: {pinchmap.zoomOut() }
            width: rWin.c.style.map.button.size
            height: rWin.c.style.map.button.size
            enabled : pinchmap.zoomLevel != pinchmap.minZoomLevel
        }
    }
    Column {
        id: buttonsLeft
        anchors.bottom: pinchmap.bottom
        anchors.bottomMargin: rWin.c.style.map.button.margin
        anchors.left: pinchmap.left
        anchors.leftMargin: rWin.c.style.map.button.margin
        spacing: rWin.c.style.map.button.spacing
        MapButton {
            iconName : "minimize_small.png"
            checkable : true
            visible: !rWin.platform.fullscreenOnly
            onClicked: {
                rWin.toggleFullscreen()
            }
            width: rWin.c.style.map.button.size
            height: rWin.c.style.map.button.size
        }
        MapButton {
            id: followPositionButton
            iconName : "center_small.png"
            width: rWin.c.style.map.button.size
            height: rWin.c.style.map.button.size
            checked : tabMap.center
            /*
            checked is bound to tabMap.center, no need to toggle
            it's value when the button is pressed
            */
            checkable: false
            onClicked: {
                // toggle map centering
                if (tabMap.center) {
                    tabMap.center = false // disable
                } else {
                    tabMap.center = true // enable
                    if (rWin.llValid) { // recenter at once (TODO: validation ?)
                        pinchmap.setCenterLatLon(rWin.pos.latitude, rWin.pos.longitude);
                    }
                }
            }
        }
        MapButton {
            id: mainMenuButton
            iconName: showModeOnMenuButton ? rWin.mode  + "_small.png" : "menu_small.png"
            width: rWin.c.style.map.button.size
            height: rWin.c.style.map.button.size
            onClicked: {
                rWin.log.debug("map page: Menu pushed!")
                rWin.push("Menu", undefined, !rWin.animate)
            }
        }
    }
    /*
    ProgressBar {
        id: zoomBar
        anchors.top: pinchmap.top;
        anchors.topMargin: 1
        anchors.left: pinchmap.left;
        anchors.right: pinchmap.right;
        maximumValue: pinchmap.maxZoomLevel;
        minimumValue: pinchmap.minZoomLevel;
        value: pinchmap.zoomLevel;
        visible: false
        Behavior on value {
            SequentialAnimation {
                PropertyAction { target: zoomBar; property: "visible"; value: true }
                NumberAnimation { duration: 100; }
                PauseAnimation { duration: 750; }
                PropertyAction { target: zoomBar; property: "visible"; value: false }
            }
        }
    }*/

}
