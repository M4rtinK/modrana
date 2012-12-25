//InfoSpeedPage.qml

import QtQuick 1.1
import "qtc/PageStatus.js" as PageStatus
import "./qtc"

BasePage {
    id: locationPage
    headerText : "Location"
    bottomPadding : 0
    isFlickable : false
    //anchors.fill : parent

    content {
        Item {
            id : fixWrapper
            anchors.fill : parent

            visible : gps.hasFix
            Label {
                id : fixStatus
                anchors.top : parent.top
                anchors.topMargin : 24
                anchors.horizontalCenter : parent.horizontalCenter
                text: gps.lastGoodFix.mode == 3 ? "3D fix" : "2D fix"
                color: gps.lastGoodFix == 3 ? "limegreen" : "yellow"
                font.pixelSize : 32
            }
            Button {
                id : copyCoordinatesButton
                anchors.topMargin : 24
                anchors.top : fixStatus.bottom
                anchors.horizontalCenter : parent.horizontalCenter
                text: "copy coordinates"
                width : 300
            }
            Grid {
                id : lGrid
                anchors.top : copyCoordinatesButton.bottom
                anchors.left : parent.left
                anchors.right : parent.right
                anchors.topMargin : 24
                anchors.leftMargin : 16
                anchors.rightMargin : 16
                property real cellWidth : width/columns
                // 2 columns in landscape, 1 in portrait
                columns : rWin.inPortrait ? 1 : 2
                spacing : 16
                Label {
                    anchors.topMargin : 24
                    property string valueString : gps.lastGoodFix.valid ? gps.lastGoodFix.lat : '<font color="red">unknown</font>'
                    text: "<b>latitude:</b> " + valueString
                    width : lGrid.cellWidth
                    font.pixelSize : 24

                }
                Label {
                    anchors.topMargin : 24
                    property string valueString : gps.lastGoodFix.valid ? gps.lastGoodFix.lon : '<font color="red">unknown</font>'
                    text: "<b>longitude:</b> " + valueString
                    width : lGrid.cellWidth
                    font.pixelSize : 24
                }
                Label {
                    anchors.topMargin : 24
                    //anchors.horizontalCenter : parent.horizontalCenter
                    property string valueString : gps.lastGoodFix.altitudeValid ? gps.lastGoodFix.altitude + " meters": '<font color="red">unknown</font>'
                    text: "<b>altitude:</b> " + valueString
                    width : lGrid.cellWidth
                    font.pixelSize : 24
                }
                Label {
                    anchors.topMargin : 24
                    property string valueString : gps.lastGoodFix.speedValid ? gps.lastGoodFix.speed.toPrecision(3) + " meters/sec": '<font color="red">unknown</font>'
                    text: "<b>speed:</b> " + valueString
                    width : lGrid.cellWidth
                    font.pixelSize : 24
                }
                Label {
                    anchors.topMargin : 24
                    property string valueString : gps.lastGoodFix.climbValid ? gps.lastGoodFix.climb + " meters/sec": '<font color="red">unknown</font>'
                    text: "<b>climb:</b> " + valueString
                    width : lGrid.cellWidth
                    font.pixelSize : 24
                }
                Label {
                    anchors.topMargin : 24
                    property string valueString : gps.lastGoodFix.bearingValid ? gps.lastGoodFix.bearing.toPrecision(3) + "° to true north": '<font color="red">unknown</font>'
                    text: "<b>bearing:</b> " + valueString
                    width : lGrid.cellWidth
                    font.pixelSize : 24
                }
                Label {
                    anchors.topMargin : 24
                    text: "<b>visible satellites:</b> " + checkPositiveNumber(gps.lastGoodFix.sats)
                    width : lGrid.cellWidth
                    font.pixelSize : 24
                }
                Label {
                    anchors.topMargin : 24
                    //anchors.horizontalCenter : parent.horizontalCenter
                    text: "<b>satellites in use:</b> " + checkPositiveNumber(gps.lastGoodFix.satsInUse)
                    width : lGrid.cellWidth
                    font.pixelSize : 24
                }
                Label {
                    anchors.topMargin : 24
                    property string valueString : gps.lastGoodFix.magneticVariation != -1  ? gps.lastGoodFix.magneticVariation.toPrecision(3) + " ° ttn": '<font color="red">unknown</font>'
                    text: "<b>magnetic variation:</b> " + valueString
                    width : lGrid.cellWidth
                    font.pixelSize : 24
                }
                Label {
                    anchors.topMargin : 24
                    //anchors.horizontalCenter : parent.horizontalCenter
                    text: "<b>GPS time:</b> " + gps.lastGoodFix.gpsTime
                    width : lGrid.cellWidth
                    font.pixelSize : 24
                }
            }
        }

        function checkPositiveNumber(number) {
            if (number < 0) {
                return '<font color="red">unknown</font>'
            } else {
                return number
            }
        }

        Label {
            id : noFixLabel
            visible : !gps.hasFix
            anchors.horizontalCenter : parent.horizontalCenter
            //anchors.verticalCenter : parent.verticalCenter
            anchors.top : parent.top
            anchors.topMargin : 24
            color : "red"
            font.pixelSize : 64
            text : "NO FIX"
        }
    }

    Connections {
        target: status == PageStatus.Inactive ? null : gps
        onLastGoodFixChanged: {
            console.log('LOCATION UPDATE')
            console.log(modules.getS("stats", "getCurrentSpeedString"))
            console.log(gps.lastGoodFix.mode)
            //otherSpeedsString = getOtherSpeeds()
        }
    }



}