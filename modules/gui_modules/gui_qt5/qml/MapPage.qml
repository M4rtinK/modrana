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
    property real routeOpacity : rWin.get("qt5GUIRouteOpacity", 1.0,
                                         function(v){tabMap.routeOpacity=v})
    // opacity of the tracklog logging trace
    property real tracklogTraceOpacity : rWin.get("qt5GUITracklogTraceOpacity", 1.0,
                                         function(v){tabMap.tracklogTraceOpacity=v})
    // opacity of stored tracklogs when shown on the map
    property real tracklogOpacity : rWin.get("qt5GUITracklogOpacity", 1.0,
                                         function(v){tabMap.tracklogOpacity=v})

    // redraw the canvas on opacity value change
    onRouteOpacityChanged : {
                pinchmap.canvas.requestFullPaint()
    }
    onTracklogTraceOpacityChanged : {
                pinchmap.canvas.requestFullPaint()
    }
    onTracklogOpacityChanged : {
                pinchmap.canvas.requestFullPaint()
    }

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
    property bool routeAvailable : routing.routePoints.count >= 2

    // navigation
    property bool navigationEnabled : false

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

    // tracklog trace related stuff
    property bool drawTracklogTrace : false
    onDrawTracklogTraceChanged : {
        // clear trace points once drawing is turned off
        if (drawTracklogTrace) {
            // make sure lastTrace point is always set
            // when trace drawing is going on
            lastTracePoint = {"latitude" : rWin.lastGoodPos.latitude, "longitude": rWin.lastGoodPos.longitude}
        } else {
            clearTracePoints()
            trackRecordingPaused = false
        }
    }
    property bool trackRecordingPaused : false
    property var tracePoints : []
    property var lastTracePoint : null
    property int maxTracePoints : 1000
    // Don't add to trace threshold in meters.
    // - if a point is less distant from the last point than the threshold
    //   it will not be added to the list for drawing
    property real addToTraceThreshold : 1.5

    function addTracePoint(point) {
        // Ignore points under the threshold, as they generally correspond to
        // standing still/bus waiting on a bus stop, etc.
        // Drawing them would only result in weird artifacts &
        // needlessly degrades trace drawing performance.
        if (F.p2pDistance(lastTracePoint, point) > addToTraceThreshold) {
            var map_coords = pinchmap.getMappointFromCoordAtZ(point.latitude, point.longitude, 15)
            var pointDict = {"latitude" : point.latitude, "longitude": point.longitude,
                             "x" : map_coords[0], "y" : map_coords[1]}
            lastTracePoint = pointDict
            tracePoints.push(pointDict)
            if (tracePoints.length > maxTracePoints) {
                // maximum length of the tracklog trace point array
                // has been reached - remove the first (oldest) point
                tracePoints.shift()
            }
            // trigger canvas redraw
            pinchmap.canvas.requestFullPaint()
        }
    }

    function clearTracePoints() {
       tracePoints = []
       lastTracePoint = null
    }

    // tracklog drawing related stuff
    property var tracklogPoints : []

    function showTracklog(tracklog) {
        if (tracklog) {
            // clear any previous points
            tracklogPoints = []

            var firstPoint = tracklog[0]
            // often used variables declared once outside loop
            var ll_coords = (0, 0)
            var map_coords = (0, 0)
            for (var i=0; i<tracklog.length; i++) {
                ll_coords = tracklog[i]
                // also compute map coordinates for the points for faster drawing
                map_coords = pinchmap.getMappointFromCoordAtZ(ll_coords.latitude, ll_coords.longitude, 15)
                tracklogPoints.push({"x": map_coords[0], "y": map_coords[1]})

                // center the map on the first point of the tracklog
                showOnMap(firstPoint.latitude, firstPoint.longitude)

                // make sure the tracklog is drawn on the canvas
                pinchmap.canvas.requestFullPaint()
            }
        }
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
        canvas.visible : tabMap.routingEnabled || tabMap.drawTracklogTrace || tabMap.tracePoints
        canvas.onFullPaint : {
            tracklogs.paintTracklog(ctx)
            tracklogs.paintTrace(ctx)
            routing.paintRoute(ctx)
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
                if (drawTracklogTrace && !trackRecordingPaused) {
                    addTracePoint(rWin.lastGoodPos)
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
            // The correction array should be valid for this
            // painting call, so we can pre compute it and use it
            // for all the conversions instead computing it again
            // for each map @ z15 -> screen coordinate conversion
            var correction = pinchmap.getMappointCorrection(15)
            var m = rWin.c.style.m // DPI multiplier
            var messagePointDiameter = 10
            if (tabMap.routingEnabled) {
                ctx.lineWidth = 10 * m
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
                    destipos = pinchmap.getScreenpointFromMappointCorrected(thispos.x,
                                                                            thispos.y,
                                                                            correction)
                    ctx.arc(destipos[0],destipos[1], 3 * m, 0, 2.0 * Math.PI)
                    ctx.stroke()
                }

                // draw the route
                ctx.globalAlpha = tabMap.routeOpacity
                ctx.lineWidth = 10 * m
                ctx.beginPath()
                for (var i=0; i<routePoints.count; i++) {
                    thispos = routePoints.get(i)
                    destipos = pinchmap.getScreenpointFromMappointCorrected(thispos.x,
                                                                            thispos.y,
                                                                            correction)
                    ctx.lineTo(destipos[0],destipos[1])
                }
                ctx.stroke()
                // restore global opacity back to default
                ctx.globalAlpha = 1.0

                // draw the step points
                ctx.lineWidth = 7 * m
                ctx.strokeStyle = Qt.rgba(1, 1, 0, 1)
                ctx.fillStyle = Qt.rgba(1, 1, 0, 1)
                for (var i=0; i<routeMessages.count; i++) {
                    ctx.beginPath()
                    thispos = routeMessages.get(i)
                    destipos = pinchmap.getScreenpointFromMappointCorrected(thispos.x,
                                                                            thispos.y,
                                                                            correction)
                    ctx.beginPath()
                    ctx.arc(destipos[0],destipos[1], 2 * m, 0, 2.0 * Math.PI)
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
                    ctx.arc(startX, startY, 3 * m, 0, 2.0 * Math.PI)
                    ctx.stroke()
                    ctx.fill()
                    // outer circle
                    ctx.beginPath()
                    ctx.strokeStyle = Qt.rgba(1, 0, 0, 0.95)
                    ctx.arc(startX, startY, 15 * m, 0, 2.0 * Math.PI)
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
                    ctx.arc(destX, destY, 3 * m, 0, 2.0 * Math.PI)
                    ctx.stroke()
                    ctx.fill()
                    // outer circle
                    ctx.beginPath()
                    ctx.strokeStyle = Qt.rgba(0, 1, 0, 0.95)
                    ctx.arc(destX, destY, 15 * m, 0, 2.0 * Math.PI)
                    ctx.stroke()
                }
            }
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
                    pinchmap.canvas.requestFullPaint()
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
            // maybe move to a worker script in the future ?
            rWin.python.setHandler("routeReceived", function(route, routeMessagePoints){
                // lets declare the coord variables variable only once
                // outside of the for loops and then reuse them
                // - maybe that's faster ? ;-)
                var ll_coords = (0, 0)
                var map_coords = (0, 0)

                // clear old route first
                routePoints.clear()
                routeMessages.clear()
                // We also cache map coordinates of the points (at the rather arbitrarily
                // selected zoom level 15) as map -> screen coordinate conversion *should*
                // be in general faster than geo -> screen coordinate conversion.

                for (var i=0; i<route.length; i++) {
                    ll_coords = route[i]
                    // also compute map coordinates for the points for faster drawing
                    map_coords = pinchmap.getMappointFromCoordAtZ(ll_coords[0], ll_coords[1], 15)
                    routePoints.append({"lat": ll_coords[0], "lon": ll_coords[1],
                                        "x": map_coords[0], "y": map_coords[1]})

                }
                for (var i=0; i<routeMessagePoints.length; i++) {
                    ll_coords = ([routeMessagePoints[i][0], routeMessagePoints[i][1]])
                    // also compute map coordinates for the points for faster drawing
                    map_coords = pinchmap.getMappointFromCoordAtZ(ll_coords[0], ll_coords[1], 15)
                    routeMessages.append({"lat": ll_coords[0], "lon": ll_coords[1],
                                          "x": map_coords[0], "y": map_coords[1],
                                          "message": routeMessagePoints[i][3]})
                }
                pinchmap.canvas.requestFullPaint()
            })
        }
    }

    Item {
        id : tracklogs

        function paintTracklog(ctx) {
            if (tracklogPoints) {
                // The correction array should be valid for this
                // painting call, so we can pre compute it and use it
                // for all the conversions instead computing it again
                // for each map @ z15 -> screen coordinate conversion
                var correction = pinchmap.getMappointCorrection(15)
                // declare the xy variable outside of the loop
                var xyPoint = (0, 0)
                // draw the tracklog
                // TODO: separate style for tracklog drawing
                ctx.lineWidth = rWin.c.style.map.tracklogTrace.width
                //ctx.strokeStyle = rWin.c.style.map.tracklogTrace.color
                ctx.strokeStyle = "red"
                ctx.globalAlpha = tabMap.tracklogOpacity
                ctx.beginPath()
                tracklogPoints.forEach(function (trackPoint, pointIndex) {
                    xyPoint = pinchmap.getScreenpointFromMappointCorrected(trackPoint.x,
                                                                           trackPoint.y,
                                                                           correction)
                    ctx.lineTo(xyPoint[0],xyPoint[1])
                })
                ctx.stroke()
                // restore global opacity back to default
                ctx.globalAlpha = 1.0

            }
        }

        function paintTrace(ctx) {
            if (drawTracklogTrace) {
                // The correction array should be valid for this
                // painting call, so we can pre compute it and use it
                // for all the conversions instead computing it again
                // for each map @ z15 -> screen coordinate conversion
                var correction = pinchmap.getMappointCorrection(15)
                // declare the xy variable otuside of the loop
                var xyPoint = (0, 0)
                // draw the track logging trace
                ctx.lineWidth = rWin.c.style.map.tracklogTrace.width
                ctx.globalAlpha = tabMap.tracklogTraceOpacity
                ctx.strokeStyle = rWin.c.style.map.tracklogTrace.color
                ctx.beginPath()
                //for (var i=0; i<tracePoints.length; i++) {
                tracePoints.forEach(function (tracePoint, pointIndex) {
                    xyPoint = pinchmap.getScreenpointFromMappointCorrected(tracePoint.x,
                                                                           tracePoint.y,
                                                                           correction)
                    //var xyPoint = pinchmap.getScreenpointFromCoord(llPoint.latitude,llPoint.longitude)
                    ctx.lineTo(xyPoint[0],xyPoint[1])
                })
                ctx.stroke()
                // restore global opacity back to default
                ctx.globalAlpha = 1.0

            }
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
        visible : tabMap.showCompass && !tabMap.navigationEnabled
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
            visible: tabMap.routingEnabled && tabMap.routingP2P && !tabMap.navigationEnabled
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
            visible: tabMap.routingEnabled && tabMap.routingP2P && !tabMap.navigationEnabled
            onClicked: {
                selectRoutingStart = false
                selectRoutingDestination = !selectRoutingDestination
            }
        }
        MapButton {
            id: navigateButton
            checkable : true
            visible: tabMap.routingEnabled && tabMap.routeAvailable
            text: qsTr("<b>navigate</b>")
            width: rWin.c.style.map.button.size * 1.25
            height: rWin.c.style.map.button.size
            onClicked: {
                if (tabMap.navigationEnabled) {
                    rWin.log.info("stopping navigation")
                } else {
                    rWin.log.info("starting navigation")
                }
                tabMap.navigationEnabled = !tabMap.navigationEnabled
            }
        }
        MapButton {
            id: endRouting
            visible: tabMap.routingEnabled && !tabMap.navigationEnabled
            text: qsTr("<b>clear</b>")
            width: rWin.c.style.map.button.size * 1.25
            height: rWin.c.style.map.button.size
            onClicked: {
                selectRoutingStart = false
                selectRoutingDestination = false
                tabMap.routingEnabled = false

                pinchmap.canvas.requestFullPaint()
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
            visible: !rWin.platform.fullscreen_only
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
