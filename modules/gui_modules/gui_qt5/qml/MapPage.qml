import QtQuick 2.0
import "functions.js" as F
import UC 1.0

Item {
    id: tabMap
    property int buttonSize: 72
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

    Component.onCompleted : {
        pinchmap.setCenterLatLon(rWin.lastGoodPos.latitude, rWin.lastGoodPos.longitude)
    }

    function getMap() {
        return pinchmap
    }

    PinchMap {
        id: pinchmap
        width: parent.width
        height: parent.height
        zoomLevel: rWin.get("z", 11, function(v){zoomLevel=v})

        layers : ListModel {
            ListElement {
                layerName : "OSM Mapnik"
                layerId: "mapnik"
                layerOpacity: 1.0
            }
        }

        onZoomLevelChanged : {
            // save zoom level
            rWin.set("z", parseInt(zoomLevel))
        }

        Connections {
            target: rWin
            onPosChanged: {
                //console.log("fix changed")
                if (tabMap.center && ! updateTimer.running) {
                    //console.debug("Update from GPS position")
                    pinchmap.setCenterLatLon(rWin.pos.latitude, rWin.pos.longitude);
                    updateTimer.start();
                } else if (tabMap.center) {
                    console.debug("Update timer preventing another update.");
                }
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

        /*
        onLatitudeChanged: {
            settings.mapPositionLat = latitude;
        }
        onLongitudeChanged: {
            settings.mapPositionLon = longitude;
        }
        onZoomLevelChanged: {
            settings.mapZoom = pinchmap.zoomLevel;
        }
        */

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

    /* TODO: use with compass
    Image {
        id: compassImage
        // TODO: investigate how to replace this by an image loader
        // what about rendered size ?

        source: "../../../../themes/"+ rWin.theme.id +"/windrose-simple.svg"
        transform: [Rotation {
                id: azCompass
                origin.x: compassImage.width/2
                origin.y: compassImage.height/2
                //angle: -compass.azimuth
            }]
        anchors.left: tabMap.left
        anchors.leftMargin: rWin.c.style.main.spacingBig
        anchors.top: tabMap.top
        anchors.topMargin: rWin.c.style.main.spacingBig
        smooth: true
        width: Math.min(tabMap.width/4, tabMap.height/4)
        fillMode: Image.PreserveAspectFit
        z: 2

        Image {
            //property int angle: gps.targetBearing || 0
            property int angle: 0
            property int outerMargin: 0
            id: arrowImage
            //visible: (gps.targetValid && gps.lastGoodFix.valid)

            // TODO: investigate how to replace this by an image loader
            // what about rendered size ?
            source: "../../../../themes/"+ rWin.theme.id +"/arrow_target.svg"
            width: (compassImage.paintedWidth / compassImage.sourceSize.width)*sourceSize.width
            fillMode: Image.PreserveAspectFit
            x: compassImage.width/2 - width/2
            y: arrowImage.outerMargin
            z: 3
            transform: Rotation {
                origin.y: compassImage.height/2 - arrowImage.outerMargin
                origin.x: arrowImage.width/2
                angle: arrowImage.angle
            }
        }
    }
    */

    Row {
        id: buttonsRight
        anchors.bottom: pinchmap.bottom
        anchors.bottomMargin: rWin.c.style.map.button.margin
        anchors.right: pinchmap.right
        anchors.rightMargin: rWin.c.style.map.button.margin
        spacing: rWin.c.style.map.button.spacing
        Button {
            iconSource: "image://python/icon/" + rWin.theme.id + "/" + "plus_small.png"
            onClicked: {pinchmap.zoomIn() }
            width: rWin.c.style.map.button.size
            height: rWin.c.style.map.button.size
            enabled : pinchmap.zoomLevel != pinchmap.maxZoomLevel
            //text : "<h1>+</h1>"
        }
        Button {
            iconSource: "image://python/icon/" + rWin.theme.id + "/" + "minus_small.png"
            onClicked: {pinchmap.zoomOut() }
            width: rWin.c.style.map.button.size
            height: rWin.c.style.map.button.size
            enabled : pinchmap.zoomLevel != pinchmap.minZoomLevel

            //text : "<h1>-</h1>"
        }
    }
    Column {
        id: buttonsLeft
        anchors.bottom: pinchmap.bottom
        anchors.bottomMargin: rWin.c.style.map.button.margin
        anchors.left: pinchmap.left
        anchors.leftMargin: rWin.c.style.map.button.margin
        spacing: rWin.c.style.map.button.spacing
        Button {
            iconSource: "image://python/icon/" + rWin.theme.id + "/" + "minimize_small.png"
            //iconSource: "themes/" + rWin.theme.id + "/" + "minimize_small.png"
            checkable : true
            visible: !rWin.platform.fullscreenOnly
            onClicked: {
                rWin.toggleFullscreen()
            }
            width: rWin.c.style.map.button.size
            height: rWin.c.style.map.button.size
            Component.onCompleted: {
                iconSource = "image://python/icon/" + rWin.theme.id + "/" + "minimize_small.png"
            }
        }
        Button {
            id: followPositionButton
            iconSource: "image://python/icon/" + rWin.theme.id + "/" + "center_small.png"
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
        Button {
            id: mainMenuButton
            iconSource: showModeOnMenuButton ?
                "image://python/icon/" + rWin.theme.id + "/" + rWin.mode  + "_small.png"
                :"image://python/icon/" + rWin.theme.id + "/" + "menu_small.png"
            width: rWin.c.style.map.button.size
            height: rWin.c.style.map.button.size
            onClicked: {
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
