//InfoSpeedPage.qml
// Shows live raw location data

import QtQuick 1.1
import "qtc/PageStatus.js" as PageStatus
import "./qtc"

BasePage {
    id: locationPage
    headerText : getFixStatus(gps.lastGoodFix.mode)
    bottomPadding : C.style.main.spacingBig*2

    function getFixStatus(mode) {
        if(mode == 3) {
            return '3D fix'
        } else if (mode == 2) {
            return '2D fix'
        } else {
            return 'Location'
        }
    }

    content {
        Item {
            id : fixWrapper
            anchors.top : parent.top
            anchors.left : parent.left
            anchors.right : parent.right
            height : lGrid.y - y + lGrid.height
            visible : gps.hasFix
            /*
            Button {
                id : copyCoordinatesButton
                anchors.topMargin : C.style.main.spacing*3
                anchors.top : parent.top
                anchors.left : parent.left
                text: "copy coordinates"
                width : 300 * C.style.main.multiplier
            }
            */
            Grid {
                id : lGrid
                //anchors.top : copyCoordinatesButton.bottom
                anchors.top : parent.top
                anchors.left : parent.left
                anchors.right : parent.right
                anchors.topMargin : C.style.main.spacing*3
                anchors.leftMargin : C.style.main.spacingBig
                anchors.rightMargin : C.style.main.spacingBig
                property real cellWidth : width/columns
                // 2 columns in landscape, 1 in portrait
                columns : rWin.inPortrait ? 1 : 2
                spacing : 16
                Label {
                    anchors.topMargin : C.style.main.spacing*3
                    property string valueString : gps.lastGoodFix.valid ? gps.lastGoodFix.lat : '<font color="red">unknown</font>'
                    text: "<b>latitude:</b> " + valueString
                    width : lGrid.cellWidth
                    font.pixelSize : C.style.main.spacing*3
                }
                Label {
                    anchors.topMargin : C.style.main.spacing*3
                    property string valueString : gps.lastGoodFix.valid ? gps.lastGoodFix.lon : '<font color="red">unknown</font>'
                    text: "<b>longitude:</b> " + valueString
                    width : lGrid.cellWidth
                    font.pixelSize : C.style.main.spacing*3
                }
                Label {
                    anchors.topMargin : C.style.main.spacing*3
                    property string valueString : gps.lastGoodFix.altitudeValid ? gps.lastGoodFix.altitude + " m": '<font color="red">unknown</font>'
                    text: "<b>altitude:</b> " + valueString
                    width : lGrid.cellWidth
                    font.pixelSize : C.style.main.spacing*3
                }
                Label {
                    anchors.topMargin : C.style.main.spacing*3
                    property string valueString : gps.lastGoodFix.speedValid ? gps.lastGoodFix.speed.toPrecision(3) + " m/s": '<font color="red">unknown</font>'
                    text: "<b>speed:</b> " + valueString
                    width : lGrid.cellWidth
                    font.pixelSize : C.style.main.spacing*3
                }
                Label {
                    anchors.topMargin : C.style.main.spacing*3
                    property string valueString : gps.lastGoodFix.climbValid ? gps.lastGoodFix.climb + " m/s": '<font color="red">unknown</font>'
                    text: "<b>climb:</b> " + valueString
                    width : lGrid.cellWidth
                    font.pixelSize : C.style.main.spacing*3
                }
                Label {
                    anchors.topMargin : C.style.main.spacing*3
                    property string valueString : gps.lastGoodFix.bearingValid ? gps.lastGoodFix.bearing.toPrecision(3) + "° to true north": '<font color="red">unknown</font>'
                    text: "<b>bearing:</b> " + valueString
                    width : lGrid.cellWidth
                    font.pixelSize : C.style.main.spacing*3
                }
                Label {
                    anchors.topMargin : C.style.main.spacing*3
                    property string valueString : gps.lastGoodFix.horizontalAccuracy != -1  ? gps.lastGoodFix.horizontalAccuracy.toPrecision(5) + " m": '<font color="red">unknown</font>'
                    text: "<b>horizontal accuracy:</b> " + valueString
                    width : lGrid.cellWidth
                    font.pixelSize : C.style.main.spacing*3
                }
                Label {
                    anchors.topMargin : C.style.main.spacing*3
                    property string valueString : gps.lastGoodFix.verticalAccuracy != -1  ? gps.lastGoodFix.verticalAccuracy.toPrecision(3) + " m": '<font color="red">unknown</font>'
                    text: "<b>vertical accuracy:</b> " + valueString
                    width : lGrid.cellWidth
                    font.pixelSize : C.style.main.spacing*3
                }
                Label {
                    anchors.topMargin : C.style.main.spacing*3
                    property string valueString : gps.lastGoodFix.speedAccuracy != -1  ? gps.lastGoodFix.speedAccuracy.toPrecision(3) + " m/s": '<font color="red">unknown</font>'
                    text: "<b>speed accuracy:</b> " + valueString
                    width : lGrid.cellWidth
                    font.pixelSize : C.style.main.spacing*3
                }
                Label {
                    anchors.topMargin : C.style.main.spacing*3
                    property string valueString : gps.lastGoodFix.climbAccuracy != -1  ? gps.lastGoodFix.climbAccuracy.toPrecision(3) + " m/s": '<font color="red">unknown</font>'
                    text: "<b>climb accuracy:</b> " + valueString
                    width : lGrid.cellWidth
                    font.pixelSize : C.style.main.spacing*3
                }
                Label {
                    anchors.topMargin : C.style.main.spacing*3
                    text: "<b>visible satellites:</b> " + checkPositiveNumber(gps.lastGoodFix.sats)
                    width : lGrid.cellWidth
                    font.pixelSize : C.style.main.spacing*3
                }
                Label {
                    anchors.topMargin : C.style.main.spacing*3
                    //anchors.horizontalCenter : parent.horizontalCenter
                    text: "<b>satellites in use:</b> " + checkPositiveNumber(gps.lastGoodFix.satsInUse)
                    width : lGrid.cellWidth
                    font.pixelSize : C.style.main.spacing*3
                }
                Label {
                    anchors.topMargin : C.style.main.spacing*3
                    property string valueString : gps.lastGoodFix.magneticVariation != -1  ? gps.lastGoodFix.magneticVariation.toPrecision(3) + "° ttn": '<font color="red">unknown</font>'
                    text: "<b>magnetic variation:</b> " + valueString
                    width : lGrid.cellWidth
                    font.pixelSize : C.style.main.spacing*3
                }
                Label {
                    anchors.topMargin : C.style.main.spacing*3
                    property string valueString : gps.lastGoodFix.timeAccuracy != -1  ? gps.lastGoodFix.timeAccuracy.toString() + " s": '<font color="red">unknown</font>'
                    text: "<b>GPS time accuracy:</b> " + valueString
                    width : lGrid.cellWidth
                    font.pixelSize : C.style.main.spacing*3
                }
                Label {
                    anchors.topMargin : C.style.main.spacing*3
                    //anchors.horizontalCenter : parent.horizontalCenter
                    text: "<b>GPS time:</b> " + gps.lastGoodFix.gpsTime
                    width : lGrid.cellWidth
                    font.pixelSize : C.style.main.spacing*3
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
            anchors.topMargin : C.style.main.spacing*3
            color : "red"
            font.pixelSize : 64 * C.style.main.multiplier
            text : (gps.lastGoodFix == 0 ) ? "NO FIX" : "fix in progress"
        }
    }
    /*
    Connections {
        target: status == PageStatus.Inactive ? null : gps
        onLastGoodFixChanged: {
            console.log('LOCATION UPDATE')
            console.log(modules.getS("stats", "getCurrentSpeedString"))
            console.log(gps.lastGoodFix.mode)
            //otherSpeedsString = getOtherSpeeds()
        }
    }
    */
}