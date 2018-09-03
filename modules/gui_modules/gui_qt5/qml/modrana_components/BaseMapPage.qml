import QtQuick 2.0
import QtQuick.Layouts 1.1
import QtSensors 5.0 as Sensors
import UC 1.0
import "../map_components"
import "../functions.js" as F
import "../backend"

Page {
    id : baseMapPage

    // general properties
    property bool showCompass : rWin.get("showQt5GUIMapCompass", true,
                                         function(v){baseMapPage.showCompass=v})
    property real compassOpacity : rWin.get("qt5GUIMapCompassOpacity", 0.7,
                                         function(v){baseMapPage.compassOpacity=v})
    property real routeOpacity : rWin.get("qt5GUIRouteOpacity", 1.0,
                                         function(v){baseMapPage.routeOpacity=v})
    // opacity of the tracklog logging trace
    property real tracklogTraceOpacity : rWin.get("qt5GUITracklogTraceOpacity", 1.0,
                                         function(v){baseMapPage.tracklogTraceOpacity=v})
    // opacity of stored tracklogs when shown on the map
    property real tracklogOpacity : rWin.get("qt5GUITracklogOpacity", 1.0,
                                         function(v){baseMapPage.tracklogOpacity=v})

    property bool center : true

    // zoom level
    property int zoomLevel : 15
    property int minZoomLevel : 0
    property int maxZoomLevel : 17

    // routing
    signal newRouteAvailable(var route)
    signal navigationStepChanged(var step)
    signal clearRoute
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

    property int mapButtonSize : Math.min(width/8.0, height/8.0)
    property int mapButtonSpacing : mapButtonSize / 4

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

    function routeToPoint(point) {
        // route from current position to a point
        rWin.mapPage.setRoutingStart(rWin.lastGoodPos.latitude, rWin.lastGoodPos.longitude)
        rWin.mapPage.setRoutingDestination(point.latitude, point.longitude)
        rWin.mapPage.routing.requestRoute(true)
        rWin.mapPage.enableRoutingUI(false)
    }

    // navigation
    property bool navigationEnabled : false
    property real navigationOverlayHeight : rWin.inPortrait ? height * 0.2 : height * 0.3
    property string currentStepMessage : ""
    property string currentStepIconId : ""
    property var currentStepCoord : Coordinate {
        latitude : 0.0
        longitude : 0.0
    }

    // map layers
    function appendMapLayer(layerId, layerName, opacityValue) {
        // add another map layer on top of existing map layers
        // by name with the given opacity
        rWin.log.error("appendMapLayer() is not implemented!")
    }

    function setMapLayerByIndex(index) {
        // set map layer by index
        rWin.log.error("setMapLayerByIndex() is not implemented!")
    }

    function removeMapLayerByIndex(index) {
        // remove map layer by index
        rWin.log.error("removeMapLayerByIndex() is not implemented!")
    }

    function setMapLayerOpacity(index, opacity) {
        // set map layer opacity by index
        rWin.log.error("setMapLayerOpacity() is not implemented!")
    }

    // search markers
    function addSearchMarker(point) {
        // add a search marker to the map
        rWin.log.error("addSearchMarker() is not implemented!")
    }

    function clearSearchMarkers() {
        // clear all search markers currently visible on the map
        rWin.log.error("clearSearchMarkers() is not implemented!")
    }

    // POI markers
    function addPOIMarker(point) {
        // add a POI marker to the map
        rWin.log.debug("addPOIMarker() is not implemented!")
    }

    function removePOIMarkerById(point) {
        // remove a visible POI marked by its id
        // (nothing happens if no such POI is visible)
        rWin.log.debug("removePOIMarkerById() is not implemented!")
    }

    function clearPOIMarkers() {
        // clear all POI markers currently visible on the map
        rWin.log.debug("clearPOIMarkers() is not implemented!")
    }

    function poiClicked(point) {
        // this function needs to be connected to the implementation
        // specific mechanism which decides that a POI has been clicked
        rWin.log.info("POI clicked: " + point.name)
        var poiPage = rWin.loadPage("POIPage", {"point" : point,
                                                "previousPage" : baseMapPage})
        rWin.pushPageInstance(poiPage)
    }

    // arbitrary tracklog display
    function showTracklog(tracklog) {
        // show a tracklog on the map
        rWin.log.error("showTracklog() is not implemented!")
    }

    function clearTracklogs() {
        // clear all tracklog displayed on the map
        rWin.log.error("clearTracklogs() is not implemented!")
    }

    // track logging & logging trace drawing
    property bool drawTracklogTrace : false
    property bool trackRecordingPaused : false

    function addTracePoint(point) {
        // add a trace point to be displayed together
        // with the other trace points (if any)
        rWin.log.error("addTracePoint() is not implemented!")
    }

    function clearTracePoints() {
        // clear all trace point currently visible on the map
        rWin.log.error("clearTracePoints() is not implemented!")
    }

    // point menu
    // - a point related menu generally shown after a long press on the map
    signal clearPointMenus

    // general functions
    function showOnMap(lat, lon) {
        // center the map view to the given coordinates
        rWin.log.error("showOnMap() is not implemented!")
    }

    function centerMapOnCurrentPosition() {
        // center the map view on current position
        rWin.log.error("centerMapOnCurrentPosition() is not implemented!")
    }

    function zoomIn() {
        // zoom the map out by one zoom level
        rWin.log.error("zoomIn() is not implemented!")
    }

    function zoomOut() {
        // zoom the map in by one zoom level
        rWin.log.error("zoomOut() is not implemented!")
    }

    // signal handlers

    // if the page becomes active, activate the media keys so they can be used
    // for zooming; if the page is deactivated, deactivate them
    onIsActiveChanged: {
        rWin.actions.mediaKeysEnabled = baseMapPage.isActive
    }

    // compass
    Sensors.Compass {
        id : compass
        dataRate : 50
        active : baseMapPage.isActive && baseMapPage.showCompass
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
        visible : baseMapPage.showCompass && !baseMapPage.navigationEnabled
        opacity : baseMapPage.compassOpacity
        // TODO: investigate how to replace this by an image loader
        // what about rendered size ?
        // also why are the edges of the image so jarred ?

        property string rosePath : if (rWin.qrc) {
            "qrc:/themes/" + rWin.theme.id +"/windrose-simple.svg"
        } else {
            "file://" + rWin.platform.themesFolderPath + "/" + rWin.theme.id +"/windrose-simple.svg"
        }

        source : compassImage.rosePath
        transformOrigin: Item.Center

        Behavior on rotation {
            SmoothedAnimation{ velocity: -1; duration:100;maximumEasingTime: 100 }
        }

        anchors.left: parent.left
        anchors.leftMargin: rWin.c.style.main.spacingBig
        anchors.top: parent.top
        anchors.topMargin: rWin.c.style.main.spacingBig
        smooth: true
        width: Math.min(baseMapPage.width/4, baseMapPage.height/4)
        fillMode: Image.PreserveAspectFit
        z: 2
    }

    // routing and navigation buttons
    Column {
        anchors.bottom: buttonsRight.top
        anchors.bottomMargin: rWin.c.style.map.button.margin * 2
        anchors.right: parent.right
        anchors.rightMargin: rWin.c.style.map.button.margin
        spacing: mapButtonSpacing
        visible: baseMapPage.routingEnabled

        MapTextButton {
            id: routingStart
            anchors.right: parent.right
            text: qsTr("<b>start</b>")
            margin: mapButtonSize * 0.2
            height: baseMapPage.mapButtonSize
            checked : selectRoutingStart
            toggledColor : Qt.rgba(1, 0, 0, 0.7)
            visible: baseMapPage.routingEnabled && baseMapPage.routingP2P && !baseMapPage.navigationEnabled
            onClicked: {
                selectRoutingStart = !selectRoutingStart
                selectRoutingDestination = false
            }
        }
        MapTextButton {
            id: routingEnd
            anchors.right: parent.right
            text: qsTr("<b>end</b>")
            margin: mapButtonSize * 0.2
            height: mapButtonSize
            checked : selectRoutingDestination
            toggledColor : Qt.rgba(0, 1, 0, 0.7)
            visible: baseMapPage.routingEnabled && baseMapPage.routingP2P && !baseMapPage.navigationEnabled
            onClicked: {
                selectRoutingStart = false
                selectRoutingDestination = !selectRoutingDestination
            }
        }
        MapTextButton {
            id: navigateButton
            anchors.right: parent.right
            checkable : true
            visible: baseMapPage.routingEnabled && baseMapPage.routeAvailable
            text: qsTr("<b>navigate</b>")
            height: mapButtonSize
            margin: mapButtonSize * 0.2
            onClicked: {
                if (baseMapPage.navigationEnabled) {
                    rWin.log.info("stopping navigation")
                    rWin.python.call("modrana.gui.navigation.stop", [], function(){})
                } else {
                    rWin.log.info("starting navigation")
                    rWin.python.call("modrana.gui.navigation.start", [], function(){})
                }
                baseMapPage.navigationEnabled = !baseMapPage.navigationEnabled
            }
        }
        MapTextButton {
            id: clearRouting
            anchors.right: parent.right
            visible: baseMapPage.routingEnabled && !baseMapPage.navigationEnabled
            text: qsTr("<b>clear</b>")
            height: mapButtonSize
            margin: mapButtonSize * 0.2
            onClicked: {
                selectRoutingStart = false
                selectRoutingDestination = false
                baseMapPage.routingEnabled = false
                // trigger the clear route signal
                baseMapPage.clearRoute()
            }
        }
    }
    // zoom up  & down buttons
    Row {
        id: buttonsRight
        anchors.bottom: parent.bottom
        anchors.bottomMargin: rWin.c.style.map.button.margin
        anchors.right: parent.right
        anchors.rightMargin: rWin.c.style.map.button.margin
        spacing: mapButtonSpacing
        MapIconButton {
            iconName: "plus_small.svg"
            onClicked: {
                baseMapPage.zoomIn()
            }
            width: mapButtonSize
            height: mapButtonSize
            margin : mapButtonSize / 6.0
            enabled : baseMapPage.zoomLevel != baseMapPage.maxZoomLevel
        }
        MapIconButton {
            iconName: "minus_small.svg"
            onClicked: {
                baseMapPage.zoomOut()
            }
            width: mapButtonSize
            height: mapButtonSize
            margin : mapButtonSize / 3.0

            enabled : baseMapPage.zoomLevel != baseMapPage.minZoomLevel
        }
    }
    // menu, centering & full screen buttons
    Column {
        id: buttonsLeft
        anchors.bottom: parent.bottom
        anchors.bottomMargin: rWin.c.style.map.button.margin
        anchors.left: parent.left
        anchors.leftMargin: rWin.c.style.map.button.margin
        spacing: mapButtonSpacing
        MapIconButton {
            iconName : "minimize_small.svg"
            checkable : true
            visible: !rWin.platform.fullscreen_only
            onClicked: {
                rWin.toggleFullscreen()
            }
            width: mapButtonSize
            height: mapButtonSize
            margin : mapButtonSize / 5.0
        }
        MapIconButton {
            id: followPositionButton
            iconName : "center_small.svg"
            width: mapButtonSize
            height: mapButtonSize
            margin : mapButtonSize / 7.0
            checked : baseMapPage.center
            toggledColor : "#3c60fa"
            /*
            checked is bound to baseMapPage.center, no need to toggle
            it's value when the button is pressed
            */
            checkable: false
            onClicked: {
                // toggle map centering
                if (baseMapPage.center) {
                    baseMapPage.center = false // disable
                } else {
                    baseMapPage.center = true // enable
                    if (rWin.llValid) { // recenter at once (TODO: validation ?)
                        baseMapPage.centerMapOnCurrentPosition()
                    }
                }
            }
        }
        MapIconButton {
            id: mainMenuButton
            iconName: "menu_small.svg"
            width: mapButtonSize
            height: mapButtonSize
            onClicked: {
                rWin.log.debug("map page: Menu pushed!")
                rWin.push("Menu", undefined, !rWin.animate)
            }
        }
    }

    // update distance from current step if in navigation mode
    Connections {
        target : baseMapPage.navigationEnabled ? rWin : null
        onPosChanged : {
            navigationOverlay.distanceFromStep = F.p2pDistance(
                baseMapPage.currentStepCoord,
                rWin.pos
            )
        }
    }

    // show markers for newly added POI on the map
    Connections {
        target : rWin
        onNewPoiAddedToDatabase : {
            rWin.log.debug("adding marker for newly added POI: " + point.name)
            addPOIMarker(point)
        }
    }

    // navigation overlay
    NavigationOverlay {
        id : navigationOverlay
        visible : baseMapPage.navigationEnabled
        message : baseMapPage.currentStepMessage
        iconId : baseMapPage.currentStepIconId
        anchors.top : parent.top
        anchors.left : parent.left
        anchors.right : parent.right
        height : navigationOverlayHeight
    }


    Component.onCompleted : {
        // connect to navigation signals

        // route available

        rWin.python.setHandler("routeReceived", function(route){
            baseMapPage.newRouteAvailable(route)
            if (baseMapPage.navigationEnabled) {
                rWin.python.call("modrana.gui.navigation.start", [], function(){})
            }
        })
        // started
        rWin.python.setHandler("navigationStarted", function(){
            if (!baseMapPage.navigationEnabled) {
                rWin.notify(qsTr("Navigation started."), 1500)
            }
        })

        // stopped
        rWin.python.setHandler("navigationStopped", function(){
            rWin.notify(qsTr("Navigation stopped."), 3000)
        })

        // destination reached
        rWin.python.setHandler("navigationDestionationReached", function(){
            rWin.notify(qsTr("Destination reached."), 3000)
        })

        // rerouting
        rWin.python.setHandler("navigationReroutingTriggered", function(){
            // set start indicator to current position when rerouting
            baseMapPage.setRoutingStart(rWin.lastGoodPos.latitude,
                                        rWin.lastGoodPos.longitude)
            rWin.notify(qsTr("Rerouting."), 3000)
        })


        // step changed
        rWin.python.setHandler("navigationCurrentStepChanged", function(step){
            rWin.log.debug("navigation step changed")
            rWin.log.debug(step.message)
            rWin.log.debug(step.latitude)
            rWin.log.debug(step.longitude)
            baseMapPage.currentStepIconId = step.icon
            baseMapPage.currentStepMessage = step.message
            baseMapPage.currentStepCoord.latitude = step.latitude
            baseMapPage.currentStepCoord.longitude = step.longitude
            baseMapPage.navigationStepChanged(step)
        })
    }
}