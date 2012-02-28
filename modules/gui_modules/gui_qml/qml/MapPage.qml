import QtQuick 1.1
import com.nokia.meego 1.0
import "uiconstants.js" as UI
import "functions.js" as F

Page {
    id: tabMap
    property int buttonSize: 72
    /*property alias geocacheModel: pinchmap.model // for access by the list page
    */

    //orientationLock: PageOrientation.LockPortrait

    function showOnMap(lat, lon) {
        pinchmap.setCenterLatLon(lat, lon);
        tabGroup.currentTab = tabMap
    }

    PinchMap {
        id: pinchmap
        width: parent.width
        height: parent.height
        zoomLevel: 11

        Connections {
            target: gps
            onLastGoodFixChanged: {
                //console.log("fix changed")
                if (tabMap.status == PageStatus.Active) {
                    if (followPositionButton.checked && ! updateTimer.running) {
                        //console.debug("Update from GPS position")
                        pinchmap.setCenterLatLon(gps.lastGoodFix.lat, gps.lastGoodFix.lon);
                        updateTimer.start();
                    } else if (followPositionButton.checked) {
                        console.debug("Update timer preventing another update.");
                    }
                }
            }
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

        showTargetIndicator: gps.targetValid;
        showTargetAtLat: gps.target.lat || 0
        showTargetAtLon: gps.target.lon || 0
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
        source: "../../../../themes/"+ rWin.theme +"/windrose-simple.svg"
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
            visible: (gps.targetValid && gps.lastGoodFix.valid)
            /* TODO: investigate how to replace this by an image loader
             what about rendered size ?
             */
            source: "../../../../themes/"+ rWin.theme +"/arrow_target.svg"
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

    /*
    Text {
        text: F.formatDistance(gps.targetDistance || 0, settings)
        anchors.horizontalCenter: compassImage.horizontalCenter
        anchors.top: compassImage.bottom
        anchors.topMargin: 8
        style: Text.Outline
        styleColor: "white"
        font.pixelSize: 32
        visible: (gps.targetValid && gps.data.valid && gps.targetDistanceValid)
    }
    */

    Row {
        id: buttonsRight
        anchors.bottom: pinchmap.bottom
        anchors.bottomMargin: 16
        anchors.right: pinchmap.right
        anchors.rightMargin: 16
        spacing: 16
        Button {
            iconSource: theme.inverted ? "image://theme/icon-m-input-add" : "image://theme/icon-m-common-add"
            onClicked: {pinchmap.zoomIn() }
            width: parent.parent.buttonSize
            height: parent.parent.buttonSize
        }
        Button {
            iconSource: theme.inverted ? "image://theme/icon-m-input-remove" : "image://theme/icon-m-common-remove"
            onClicked: {pinchmap.zoomOut() }
            width: parent.parent.buttonSize
            height: parent.parent.buttonSize
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
            id: followPositionButton
            iconSource: "image://theme/icon-m-common-location" + (theme.inverted ? "-inverse" : "")
            width: parent.parent.buttonSize
            height: parent.parent.buttonSize
            checkable: true
            onClicked: {
                if (checked && gps.lastGoodFix) {
                    pinchmap.setCenterLatLon(gps.lastGoodFix.lat, gps.lastGoodFix.lon);
                }
            }
        }
        Button {
            id: refreshGeocachesButton
            iconSource: "image://theme/icon-s-transfer-download" + (theme.inverted ? "-inverse" : "")
            width: parent.parent.buttonSize
            height: parent.parent.buttonSize
            onClicked: {
                pinchmap.requestUpdate()
            }
        }
    }
    ProgressBar {
        id: zoomBar
        anchors.bottom: buttonsLeft.top;
        anchors.bottomMargin: 16;
        anchors.left: buttonsLeft.left;
        anchors.right: buttonsRight.right;
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
    }
}
