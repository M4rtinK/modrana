// PinchMapPage.qml
//
// A map view implementation based on the PinchMap element.

import QtQuick 2.0
import "functions.js" as F
import UC 1.0
import "modrana_components"
import "map_components"
import "pinchmap"

BaseMapPage {
    id: pinchmapPage
    property int mapTileScale : rWin.get(
    "mapScale", 1, function(v){mapTileScale=v})

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

    property bool showModeOnMenuButton : rWin.get("showModeOnMenuButton", false,
    function(v){showModeOnMenuButton=v})

    // zoom level
    property alias zoomLevel : pinchmap.zoomLevel
    property alias minZoomLevel : pinchmap.minZoomLevel
    property alias maxZoomLevel : pinchmap.maxZoomLevel

    property var pinchmap

    property alias layers : pinchmap.layers

    // routing related stuff
    property alias routing : routing
    property bool routeAvailable : routing.routePoints.count >= 2

    onClearRoute : {
        // clear the route from the map
        // - the needed booleans have already been set,
        //   so just redraw the canvas to clear the route
        pinchmap.canvas.requestFullPaint()
    }

    // map layers
    function appendMapLayer(layerId, layerName, opacityValue) {
        // add another map layer on top of existing map layers
        // by name with the given opacity
        pinchmap.appendLayer(layerId, layerName, opacityValue)
    }

    function setMapLayerByIndex(index, layerId) {
        // set map layer by index
        pinchmap.setLayerById(index, layerId)
    }

    function removeMapLayerByIndex(index) {
        // remove map layer by index
        pinchmap.removeLayer(index)
    }

    function setMapLayerOpacity(index, opacity) {
        // set map layer opacity by index
        pinchmap.setLayerOpacity(index, opacity)
    }

    // tracklogs and trace display
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
        // show a tracklog on the map
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

    function clearTracklogs() {
        // clear all tracklog displayed on the map
        tracklogPoints = []
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

    // search markers
    function addSearchMarker(point) {
        // add a search marker to the map
        pinchmap.addSearchMarker(point)
    }

    function clearSearchMarkers() {
        pinchmap.clearSearchMarkers()
    }

    // POI markers
    function addPOIMarker(point) {
        pinchmap.addPOIMarker(point)
    }

    function removePOIMarkerById(point) {
        pinchmap.removePOIMarkerById(point)
    }

    function clearPOIMarkers() {
        pinchmap.clearPOIMarkers()
    }

    // general functions
    function showOnMap(lat, lon) {
        pinchmap.setCenterLatLon(lat, lon);
        // show on map moves map center and
        // and thus disables centering
        center = false
    }

    // point menu control
    onClearPointMenus : {
        pinchmap.onClearPointMenus()
    }

    function centerMapOnCurrentPosition() {
        pinchmap.setCenterLatLon(rWin.pos.latitude, rWin.pos.longitude);
    }

    function zoomIn() {
        pinchmap.zoomIn()
    }

    function zoomOut() {
        pinchmap.zoomOut()
    }

    PinchMap {
        id: pinchmap
        // make sure the pinch map is under UI elements
        z : -1
        anchors.fill : parent
        property bool initialized : false
        zoomLevel: rWin.get("z", 11, setInitialZ)

        // shift the scale bar down when the navigation overlay is active
        scaleBarTopOffset : navigationEnabled ? navigationOverlayHeight : 0

        function setInitialZ (initialZ) {
            zoomLevel = initialZ
            initialized = true
        }

        tileScale : pinchmapPage.mapTileScale
        name : "mainMap"

        layers : ListModel {
            ListElement {
                layerName : "OSM Mapnik"
                layerId: "mapnik"
                layerOpacity: 1.0
            }
        }
        canvas.visible : pinchmapPage.routingEnabled || pinchmapPage.drawTracklogTrace || pinchmapPage.tracePoints
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
                if (pinchmapPage.center && ! updateTimer.running) {
                    //rWin.log.debug("map page: Update from GPS position")
                    pinchmap.setCenterLatLon(rWin.lastGoodPos.latitude, rWin.lastGoodPos.longitude);
                    updateTimer.start();
                } else if (pinchmapPage.center) {
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
            pinchmapPage.center = false
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
            if (pinchmapPage.routingEnabled) {
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

                // draw the current step indicator when navigation is enabled
                if (pinchmapPage.navigationEnabled) {
                    var currentStep = pinchmap.getScreenpointFromCoord(pinchmapPage.currentStepCoord.latitude,
                                                                       pinchmapPage.currentStepCoord.longitude)
                    var currentStepX = currentStep[0]+offsetX
                    var currentStepY = currentStep[1]+offsetY
                    ctx.lineWidth = 4 * m
                    ctx.beginPath()
                    ctx.strokeStyle = Qt.rgba(1, 0, 0, 0.95)
                    ctx.arc(currentStepX, currentStepY, 15 * m, 0, 2.0 * Math.PI)
                    ctx.stroke()
                }

                // draw the route
                ctx.strokeStyle = Qt.rgba(0, 0, 0.5, 1.0)
                ctx.globalAlpha = pinchmapPage.routeOpacity
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

        // connect to the POI clicked signals from pinchmap
        Connections {
            target : pinchmap
            onPoiClicked : {
                poiClicked(point)
            }
        }

        function requestRoute(startWithHeading) {
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

            var startHeading = null

            // include current heading when requested
            if (startWithHeading) {
                startHeading = rWin.bearing
            }
            var route_request = {
                "waypoints" : [
                    {"latitude" : routingStartLat,
                     "longitude" : routingStartLon,
                     "heading" : startHeading},
                     {"latitude" : routingDestinationLat,
                     "longitude" : routingDestinationLon,
                     "heading" : null}
                ]
            }
            rWin.python.call("modrana.gui.routing.request_route", [route_request])
            rWin.log.info("route requested")
            return true
        }

        Connections {
            // maybe move to a worker script in the future ?
            target : pinchmapPage
            onNewRouteAvailable: {
                // lets declare the coord variables variable only once
                // outside of the for loops and then reuse them
                // - maybe that's faster ? ;-)
                var ll_coords = (0, 0)
                var map_coords = (0, 0)

                // clear old route first
                routing.routePoints.clear()
                routing.routeMessages.clear()
                // We also cache map coordinates of the points (at the rather arbitrarily
                // selected zoom level 15) as map -> screen coordinate conversion *should*
                // be in general faster than geo -> screen coordinate conversion.

                for (var i=0; i<route.points.length; i++) {
                    ll_coords = route.points[i]
                    // also compute map coordinates for the points for faster drawing
                    map_coords = pinchmap.getMappointFromCoordAtZ(ll_coords[0], ll_coords[1], 15)
                    routing.routePoints.append({"lat": ll_coords[0], "lon": ll_coords[1],
                                        "x": map_coords[0], "y": map_coords[1]})

                }
                for (var i=0; i<route.messagePoints.length; i++) {
                    ll_coords = ([route.messagePoints[i][0], route.messagePoints[i][1]])
                    // also compute map coordinates for the points for faster drawing
                    map_coords = pinchmap.getMappointFromCoordAtZ(ll_coords[0], ll_coords[1], 15)
                    routing.routeMessages.append({"lat": ll_coords[0], "lon": ll_coords[1],
                                          "x": map_coords[0], "y": map_coords[1],
                                          "message": route.messagePoints[i][3]})
                }
                pinchmap.canvas.requestFullPaint()
            }
            onNavigationStepChanged: {
                // request repaint if navigation step changes to that
                // current step indicator is in correct place
                pinchmap.canvas.requestFullPaint()
            }
            onNavigationEnabledChanged: {
                // we need to show/hide current step indicator when navigation is turned on/off
                pinchmap.canvas.requestFullPaint()
            }
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
                ctx.globalAlpha = pinchmapPage.tracklogOpacity
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
                ctx.globalAlpha = pinchmapPage.tracklogTraceOpacity
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
}
