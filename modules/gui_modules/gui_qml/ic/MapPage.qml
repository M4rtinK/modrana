import QtQuick 1.1
import "functions.js" as F
import "./qtc"

Item {

    id: tabMap
    property int buttonSize: 72
    anchors.fill : parent
    function showOnMap(lat, lon) {
        pinchmap.setCenterLatLon(lat, lon);
        tabGroup.currentTab = tabMap
    }

    property bool center : true
    property bool showModeOnMenuButton : options.get("showModeOnMenuButton", false)

    property variant pinchmap

    property alias layers : pinchmap.layers

    Component.onCompleted : {
        pinchmap.setCenterLatLon(gps.lastGoodFix.lat, gps.lastGoodFix.lon);
    }

    function getMap() {
        return pinchmap
    }

    PinchMap {
        id: pinchmap
        width: parent.width
        height: parent.height
        zoomLevel: options.get("z", 11)

        layers : ListModel {
            ListElement {
                layerName : "OSM Mapnik"
                layerId: "mapnik"
                layerOpacity: 1.0
            }
        }

        onZoomLevelChanged : {
            // save zoom level
            options.setI("z", parseInt(zoomLevel))
        }

        Connections {
            target: gps
            onLastGoodFixChanged: {
                //console.log("fix changed")
                if (tabMap.center && ! updateTimer.running) {
                    //console.debug("Update from GPS position")
                    pinchmap.setCenterLatLon(gps.lastGoodFix.lat, gps.lastGoodFix.lon);
                    updateTimer.start();
                } else if (tabMap.center) {
                    console.debug("Update timer preventing another update.");
                }
            }
        }

        onDrag : {
            // disable map centering once drag is detected
            tabMap.center = false
            console.log("DRAG DRAG")
            console.log(theme)
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
        currentPositionValid: gps.hasFix
        currentPositionLat: gps.lastGoodFix.lat
        currentPositionLon: gps.lastGoodFix.lon
        //currentPositionAzimuth: compass.azimuth
        //TODO: switching between GPS bearing & compass azimuth
        currentPositionAzimuth: gps.lastGoodFix.bearing
        currentPositionError: gps.lastGoodFix.error
    }

    Image {
        id: compassImage
        /* TODO: investigate how to replace this by an image loader
         what about rendered size ?
         */
        source: "../../../../themes/"+ modrana.theme_id +"/windrose-simple.svg"
        transform: [Rotation {
                id: azCompass
                origin.x: compassImage.width/2
                origin.y: compassImage.height/2
                //angle: -compass.azimuth
            }]
        anchors.left: tabMap.left
        anchors.leftMargin: 16
        anchors.top: tabMap.top
        anchors.topMargin: 16
        smooth: true
        width: Math.min(tabMap.width/4, tabMap.height/4)
        fillMode: Image.PreserveAspectFit
        z: 2

        Image {
            property int angle: gps.targetBearing || 0
            property int outerMargin: 0
            id: arrowImage
            //visible: (gps.targetValid && gps.lastGoodFix.valid)
            /* TODO: investigate how to replace this by an image loader
             what about rendered size ?
             */
            source: "../../../../themes/"+ modrana.theme_id +"/arrow_target.svg"
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

    Row {
        id: buttonsRight
        anchors.bottom: pinchmap.bottom
        anchors.bottomMargin: 16
        anchors.right: pinchmap.right
        anchors.rightMargin: 16
        spacing: 16
        Button {
            iconSource: "image://icons/" + modrana.theme_id + "/" + "plus_small.png"
            onClicked: {pinchmap.zoomIn() }
            width: parent.parent.buttonSize
            height: parent.parent.buttonSize
            enabled : pinchmap.zoomLevel != pinchmap.maxZoomLevel
            //text : "<h1>+</h1>"
        }
        Button {
            iconSource: "image://icons/" + modrana.theme_id + "/" + "minus_small.png"
            onClicked: {pinchmap.zoomOut() }
            width: parent.parent.buttonSize
            height: parent.parent.buttonSize
            enabled : pinchmap.zoomLevel != pinchmap.minZoomLevel

            //text : "<h1>-</h1>"
        }
    }
    Column {
        id: buttonsLeft
        anchors.bottom: pinchmap.bottom
        anchors.bottomMargin: 16
        anchors.left: pinchmap.left
        anchors.leftMargin: 16
        spacing: 16
        Button {
            iconSource: "image://icons/" + modrana.theme_id + "/" + "minimize_small.png"
            checkable : true
            visible: !platform.fullscreenOnly()
            onClicked: {
                platform.toggleFullscreen()
            }
            width: parent.parent.buttonSize
            height: parent.parent.buttonSize
        }
        Button {
            id: followPositionButton
            iconSource: "image://icons/" + modrana.theme_id + "/" + "center_small.png"
            width: parent.parent.buttonSize
            height: parent.parent.buttonSize
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
                    if (gps.lastGoodFix) { // recenter at once
                        pinchmap.setCenterLatLon(gps.lastGoodFix.lat, gps.lastGoodFix.lon);
                    }
                }
            }
        }
        Button {
            id: mainMenuButton
            iconSource: showModeOnMenuButton ?
                "image://icons/" + modrana.theme_id + "/" + modrana.mode  + "_small.png"
                :"image://icons/" + modrana.theme_id + "/" + "menu_small.png"
            width: parent.parent.buttonSize
            height: parent.parent.buttonSize
            onClicked: {
                rWin.push("Menu")
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
