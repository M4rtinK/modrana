import QtQuick 1.1
import com.nokia.meego 1.0
import "uiconstants.js" as UI
import "functions.js" as F

Page {
    orientationLock: PageOrientation.LockPortrait


    Column {
        spacing: 10
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        anchors.fill: parent
        anchors.topMargin: 16
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        id: compassColumn

        Row {
            InfoLabel {
                name: "Distance"
                value: gps.targetDistanceValid ? F.formatDistance(gps.targetDistance, settings) : "-"
                width: compassColumn.width/2.0
            }
            Column {
                width: compassColumn.width/2.0
                Label {
                    id: t0
                    font.pixelSize: 20
                    color: UI.COLOR_INFOLABEL
                    font.weight: Font.Bold
                    text: "Accuracy"
                    anchors.right: parent.right
                }

                Label {
                    id: t1
                    text: gps.lastGoodFix.valid ? ("± " + F.formatDistance(gps.lastGoodFix.error, settings)) : "-"
                    font.pixelSize: UI.FONT_DEFAULT
                    font.weight: Font.Light
                    anchors.right: parent.right
                }
            }
            anchors.left: parent.left
            anchors.right: parent.right
        }

        Item {
            width: parent.width
            height: compassImage.height
            anchors.topMargin: -32
            Image {
                id: compassImage
                source: theme.inverted ? "../data/windrose-night.svg" : "../data/windrose.svg"
                transform: [Rotation {
                        id: azCompass
                        origin.x: compassImage.width/2
                        origin.y: compassImage.height/2
                        angle: -compass.azimuth
                    }]
                smooth: true
                width: compassColumn.width * 0.9
                anchors.horizontalCenter: parent.horizontalCenter
                fillMode: Image.PreserveAspectFit
                z: 2
                Image {
                    property int angle: gps.targetBearing || 0
                    property int outerMargin: 50
                    visible: (gps.targetValid && gps.lastGoodFix.valid)
                    id: arrowImage
                    source: "../data/arrow_target.svg"
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
              // Disabled due to some weird loading behavior
            Image {
                source: "image://theme/icon-m-viewfinder-camera" + (theme.inverted ? "" : "-selected")
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        showCamera();
                    }
                }
            }*/
        }


        Row {
            InfoLabel {
                name: "Altitude"
                value: gps.lastGoodFix.altitudeValid ? F.formatDistance(gps.lastGoodFix.altitude, settings) : "-"
                width: compassColumn.width/3.0
            }
            InfoLabel {
                name: "Bearing"
                value: F.formatBearing(compass.azimuth)
                width: compassColumn.width/3
            }
            InfoLabel {
                name: "Comp. Accuracy"
                value: Math.floor(compass.calibration * 100) + "%"
                width: compassColumn.width/3
            }
        }

        InfoLabel {
            name: gps.data.valid ? "Current Position" : "Last Known Position"
            value: gps.data.valid
                   ? F.formatCoordinate(gps.data.lat, gps.data.lon, settings)
                   : (gps.lastGoodFix.valid ? F.formatCoordinate(gps.lastGoodFix.lat, gps.lastGoodFix.lon, settings) : "...there is none.")
            width: compassColumn.width
        }

        Row {
            InfoLabel {
                id: currentTarget
                name: "Current Target"
                value: gps.targetValid ? F.formatCoordinate(gps.target.lat, gps.target.lon, settings) : "not set"
                width: compassColumn.width - changeTargetButton.width
            }
            Button {
                id: changeTargetButton
                width: compassColumn.width/6
                anchors.bottom: currentTarget.bottom
                iconSource: "image://theme/icon-m-toolbar-edit" + (theme.inverted ? "-white" : "")
                onClicked: {
                    coordinateSelectorDialog.source = "CoordinateSelectorDialog.qml";
                    coordinateSelectorDialog.item.accepted.connect(function() {
                                                                       var res = coordinateSelectorDialog.item.getValue();
                                                                       controller.setTarget(res[0], res[1])
                                                                   });

                    if (gps.targetValid) {
                        coordinateSelectorDialog.item.setValue(gps.target.lat, gps.target.lon);
                    } else if (gps.lastGoodFix.valid) {
                        coordinateSelectorDialog.item.setValue(gps.lastGoodFix.lat, gps.lastGoodFix.lon);
                    }
                    coordinateSelectorDialog.item.open()
                }
            }
        }


    }
    
    function openMenu() {
        menu.open();
    }

    Loader {
        id: coordinateSelectorDialog
    }
    
    Menu {
        id: menu
        visualParent: parent

        MenuLayout {
            MenuItem { text: "Unset Target"; onClicked: { controller.setAsTarget(null); } }
            MenuItem { text: "Settings"; onClicked: { showSettings(); } }
        }
    }
}
