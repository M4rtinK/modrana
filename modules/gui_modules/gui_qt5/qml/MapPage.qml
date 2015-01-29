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

    property variant pinchmap

    property alias layers : pinchmap.layers

    // routing related stuff
    property bool selectRoutingStart : false
    property bool selectRoutingDestination : false
    property real routingStartLat: 0.
    property real routingStartLon: 0.
    property real routingDestinationLat: 0.
    property real routingDestinationLon: 0.
    
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
                pinchmap.zoomOut()
            }
            onZoomDown : {
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
        TextButton {
            id: routingStart
            text: "routing start"
            width: rWin.c.style.map.button.size
            height: rWin.c.style.map.button.size
            Rectangle {
                id: routingStartRect
                color: "red"
                anchors.fill: parent
            }
            Text {
                text: parent.text
            }
            onClicked: {
                console.log("set startpoint for routing")
                selectRoutingStart = true
                selectRoutingDestination = false
                routingStartRect.color = "blue"
                routingEndRect.color = "red"
            }
        }
        TextButton {
            id: routingEnd
            text: "routing end"
            width: rWin.c.style.map.button.size
            height: rWin.c.style.map.button.size
            Rectangle {
                id: routingEndRect
                color: "red"
                anchors.fill: parent
            }
            Text {
                text: parent.text
            }
            onClicked: {
                console.log("set endpoint for routing")
                selectRoutingStart = false
                selectRoutingDestination = true
                routingEndRect.color = "blue"
                routingStartRect.color = "red"
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
    Canvas {
        id: routingData
        anchors.fill: parent
        opacity: 0.8
        visible: true
        property var touchpos: [0,0]
        property var route : ListModel {
            id: routeModel
        }

        onPaint: { 
            console.log("FJF: canvas paint requested start")
            var startpos = pinchmap.getScreenpointFromCoord(rWin.routingStartPos.latitude,rWin.routingStartPos.longitude)
            var destipos = pinchmap.getScreenpointFromCoord(rWin.routingDestinationPos.latitude,rWin.routingDestinationPos.longitude)
            var startX = startpos[0]
            var startY = startpos[1]
            var destX = destipos[0]
            var destY = destipos[1]
            var thispos = (0,0,0)
            console.log("routing points to plot: ",startpos, destipos)
            var ctx = getContext("2d")
            // clear the canvas
            ctx.clearRect(0,0,tabMap.width,tabMap.height)

            // setup the stroke
            ctx.lineWidth = 4
            ctx.strokeStyle = "red"

            // create a path
            ctx.beginPath()
            console.log("moveto: ", startX, startY)
            ctx.moveTo(startX,startY)
            console.log("list count: " + routingData.route.count)
            console.log("list: " + routingData.route)
            for (var i=0; i<routingData.route.count; i++) {
                console.log("route " + i + routingData.route.get(i))
                thispos = routingData.route.get(i)
                console.log("thispos: ", thispos.lat, thispos.lon)
                destipos = pinchmap.getScreenpointFromCoord(thispos.lat,thispos.lon)
                console.log("lineTo: ", destipos[0], destipos[1])
                ctx.lineTo(destipos[0],destipos[1])
            }
            //ctx.closePath()

            // stroke path
            ctx.stroke()

            console.log("FJF: canvas paint requested done")
        }
        onPainted: {
            console.log("FJF: canvas painted")
        }
        Component.onCompleted: {
            console.log("FJF: Canvas: onCompleted")
            rWin.python.setHandler("routeReceived", function(route){
                rWin.log.debug("routing received:" + route)
                // clear old route first
                routingData.route.clear()
                 for (var i=0; i<route.length; i++) {
                     rWin.log.debug("route: step " + i +": "+route[i][0] + "XXX" + route[i][1])
                     routingData.route.append({"lat": route[i][0], "lon": route[i][1]});
                 }
                 routingData.requestPaint()
            })
        }

        Connections {
            target: pinchmap
            onCenterSet: {
                console.log("FJF: Canvas: pinchmap centerSet")
                routingData.requestPaint()
            }
            onDrag: {
                console.log("FJF: Canvas: pinchmap drag")
                //routingData.requestPaint()
            }
            onZoomLevelChanged: {
                console.log("FJF: Canvas: pinchmap zoomLevel changed")
                routingData.requestPaint()
            }
            onMapClicked: {
                console.log("FJF: Canvas: map clicked")
            }
            onMapDoubleClicked: {
                console.log("FJF: Canvas: map doubleClicked")
                console.log("FJF: screen coordinates", screenX, screenY)
                console.log("FJF: geographic coordinates", pinchmap.getCoordFromScreenpoint(screenX, screenY))
                // store the position we touched in Lat,Lon
                routingData.touchpos = pinchmap.getCoordFromScreenpoint(screenX, screenY)
                if (selectRoutingStart) {
                    routingStartLat = routingData.touchpos[0]
                    routingStartLon = routingData.touchpos[1]
                    rWin.routingStartPos.latitude=routingStartLat
                    rWin.routingStartPos.longitude=routingStartLon
                    console.log("FJF new start point")
                }
                if (selectRoutingDestination) {
                    routingDestinationLat = routingData.touchpos[0]
                    routingDestinationLon = routingData.touchpos[1]
                    rWin.routingDestinationPos.latitude=routingDestinationLat
                    rWin.routingDestinationPos.longitude=routingDestinationLon
                    console.log("FJF new destination point")
                    rWin.python.call("modrana.gui.modules.route.llRoute", [[rWin.routingStartPos.latitude,rWin.routingStartPos.longitude], [rWin.routingDestinationPos.latitude,rWin.routingDestinationPos.longitude]])
                    rWin.log.debug("routing called")
                }

                console.log("FJF: routing:")
                console.log("FJF: startpoint: ", routingStartLat, routingStartLon)
                console.log("FJF: endpoint: ", routingDestinationLat, routingDestinationLon)

                routingData.requestPaint()
            }
            onMapPanEnd: {
                console.log("FJF: mapPanEnd")
                routingData.requestPaint()
            }
        }
    }
}
