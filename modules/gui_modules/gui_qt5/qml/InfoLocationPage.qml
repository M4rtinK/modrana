//InfoSpeedPage.qml
// Shows live raw location data

import QtQuick 2.0
import UC 1.0

BasePage {
    id: locationPage

    headerText : if (rWin.position.coordinate.isValid) {
        if (rWin.position.altitudeValid) {
            '3D fix'
        } else {
            '2D fix'
        }
    } else {
        'Location'
    }

    bottomPadding : rWin.c.style.main.spacingBig*2

    content : Item {
        id : fixWrapper
        anchors.top : parent.top
        anchors.left : parent.left
        anchors.right : parent.right
        height : lGrid.y - y + lGrid.height
        visible : rWin.hasFix
        /*
        Button {
            id : copyCoordinatesButton
            anchors.topMargin : rWin.c.style.main.spacing*3
            anchors.top : parent.top
            anchors.left : parent.left
            text: "copy coordinates"
            width : 300 * rWin.c.style.main.multiplier
        }
        */
        Grid {
            id : lGrid
            anchors.top : parent.top
            anchors.left : parent.left
            anchors.right : parent.right
            anchors.topMargin : rWin.c.style.main.spacing*3
            anchors.leftMargin : rWin.c.style.main.spacingBig
            anchors.rightMargin : rWin.c.style.main.spacingBig
            property real cellWidth : width/columns
            // 2 columns in landscape, 1 in portrait
            columns : rWin.inPortrait ? 1 : 2
            spacing : 16

            property real lat : rWin.position.coordinate.latitude
            property real lon : rWin.position.coordinate.longitude
            property bool latValid : rWin.position.latitudeValid
            property bool lonValid : rWin.position.longitudeValid

            property real altitude : rWin.position.coordinate.altitude
            property bool altitudeValid : rWin.position.altitudeValid

            property real speed : rWin.position.speed
            property bool speedValid : rWin.position.speedValid

            property real horizontalAccuracy : rWin.position.horizontalAccuracy
            property real verticalAccuracy : rWin.position.verticalAccuracy
            property real horizontalAccuracyValid : rWin.position.horizontalAccuracyValid
            property real verticalAccuracyValid : rWin.position.verticalAccuracyValid

            property date fixTimestamp : rWin.position.timestamp

            property string notValidString : '<font color="red">(not valid)</font>'
            property string unknownString : '<font color="red">unknown</font>'

            // TODO: translations! :)

            Label {
                anchors.topMargin : rWin.c.style.main.spacing*3
                property string validString : lGrid.latValid ? "" : lGrid.notValidString
                property string valueString : lGrid.lat ? lGrid.lat + " " + validString : lGrid.unknownString
                text: "<b>latitude:</b> " + valueString
                width : lGrid.cellWidth
                font.pixelSize : rWin.c.style.main.spacing*3
            }
            Label {
                anchors.topMargin : rWin.c.style.main.spacing*3
                property string validString : lGrid.lonValid ? "" : lGrid.notValidString
                property string valueString : lGrid.lon ? lGrid.lon + " " + validString : lGrid.unknownString
                text: "<b>longitude:</b> " + valueString
                width : lGrid.cellWidth
                font.pixelSize : rWin.c.style.main.spacing*3
            }
            Label {
                anchors.topMargin : rWin.c.style.main.spacing*3
                property string validString : lGrid.altitudeValid ? "" : lGrid.notValidString
                property string valueString : lGrid.altitude ? lGrid.altitude : lGrid.unknownString
                text: "<b>altitude:</b> " + valueString + " m " + validString
                width : lGrid.cellWidth
                font.pixelSize : rWin.c.style.main.spacing*3
            }
            Label {
                anchors.topMargin : rWin.c.style.main.spacing*3
                property string validString : lGrid.speedValid ? "" : lGrid.notValidString
                property string valueString : lGrid.speed ? lGrid.speed + " m/s " + validString :
                                                            (lGrid.speed == 0) ? "not moving" :
                                                                                 lGrid.unknownString
                text: "<b>speed:</b> " + valueString
                width : lGrid.cellWidth
                font.pixelSize : rWin.c.style.main.spacing*3
            }
            Label {
                anchors.topMargin : rWin.c.style.main.spacing*3
                property string valueString : rWin.bearing ? rWin.bearing.toPrecision(3) + "° to true north": lGrid.unknownString
                text: "<b>bearing:</b> " + valueString
                width : lGrid.cellWidth
                font.pixelSize : rWin.c.style.main.spacing*3
            }
            Label {
                anchors.topMargin : rWin.c.style.main.spacing*3
                property string validString : lGrid.horizontalAccuracyValid ? "" : lGrid.notValidString
                property string valueString : lGrid.horizontalAccuracy ? lGrid.horizontalAccuracy : lGrid.unknownString
                text: "<b>horizontal accuracy:</b> " + valueString + " m " + validString
                width : lGrid.cellWidth
                font.pixelSize : rWin.c.style.main.spacing*3
            }
            Label {
                anchors.topMargin : rWin.c.style.main.spacing*3
                property string validString : lGrid.verticalAccuracyValid ? "" : lGrid.notValidString
                property string valueString : lGrid.verticalAccuracy ? lGrid.verticalAccuracy : lGrid.unknownString
                text: "<b>vertical accuracy:</b> " + valueString + " m " + validString
                width : lGrid.cellWidth
                font.pixelSize : rWin.c.style.main.spacing*3
            }
            Label {
                anchors.topMargin : rWin.c.style.main.spacing*3
                property string valueString : lGrid.fixTimestamp ? lGrid.fixTimestamp : lGrid.unknownString
                text: "<b>fix timestamp:</b> " + valueString
                width : lGrid.cellWidth
                font.pixelSize : rWin.c.style.main.spacing*3
            }

            /*
            // not all data types are available through the QtPositioning API modRana
            // currently uses for the Qt5 GUI
            // * it might be possible to get additional data when running from GPSD data
            //   directly on some platforms

            Label {
                anchors.topMargin : rWin.c.style.main.spacing*3
                text: "<b>visible satellites:</b> " + checkPositiveNumber(gps.lastGoodFix.sats)
                width : lGrid.cellWidth
                font.pixelSize : rWin.c.style.main.spacing*3
            }
            Label {
                anchors.topMargin : rWin.c.style.main.spacing*3
                //anchors.horizontalCenter : parent.horizontalCenter
                text: "<b>satellites in use:</b> " + checkPositiveNumber(gps.lastGoodFix.satsInUse)
                width : lGrid.cellWidth
                font.pixelSize : rWin.c.style.main.spacing*3
            }
            Label {
                anchors.topMargin : rWin.c.style.main.spacing*3
                property string valueString : gps.lastGoodFix.magneticVariation != -1  ? gps.lastGoodFix.magneticVariation.toPrecision(3) + "° ttn": '<font color="red">unknown</font>'
                text: "<b>magnetic variation:</b> " + valueString
                width : lGrid.cellWidth
                font.pixelSize : rWin.c.style.main.spacing*3
            }

            Label {
                anchors.topMargin : rWin.c.style.main.spacing*3
                property string valueString : gps.lastGoodFix.speedAccuracy != -1  ? gps.lastGoodFix.speedAccuracy.toPrecision(3) + " m/s": '<font color="red">unknown</font>'
                text: "<b>speed accuracy:</b> " + valueString
                width : lGrid.cellWidth
                font.pixelSize : rWin.c.style.main.spacing*3
            }
            Label {
                anchors.topMargin : rWin.c.style.main.spacing*3
                property string valueString : gps.lastGoodFix.climbAccuracy != -1  ? gps.lastGoodFix.climbAccuracy.toPrecision(3) + " m/s": '<font color="red">unknown</font>'
                text: "<b>climb accuracy:</b> " + valueString
                width : lGrid.cellWidth
                font.pixelSize : rWin.c.style.main.spacing*3
            }
            Label {
                anchors.topMargin : rWin.c.style.main.spacing*3
                property string valueString : gps.lastGoodFix.climbValid ? gps.lastGoodFix.climb + " m/s": '<font color="red">unknown</font>'
                text: "<b>climb:</b> " + valueString
                width : lGrid.cellWidth
                font.pixelSize : rWin.c.style.main.spacing*3
            }
            Label {
                anchors.topMargin : rWin.c.style.main.spacing*3
                property string valueString : gps.lastGoodFix.timeAccuracy != -1  ? gps.lastGoodFix.timeAccuracy.toString() + " s": '<font color="red">unknown</font>'
                text: "<b>GPS time accuracy:</b> " + valueString
                width : lGrid.cellWidth
                font.pixelSize : rWin.c.style.main.spacing*3
            }
            Label {
                anchors.topMargin : rWin.c.style.main.spacing*3
                //anchors.horizontalCenter : parent.horizontalCenter
                text: "<b>GPS time:</b> " + gps.lastGoodFix.gpsTime
                width : lGrid.cellWidth
                font.pixelSize : rWin.c.style.main.spacing*3
            }
            */
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
        visible : !rWin.hasFix
        anchors.horizontalCenter : parent.horizontalCenter
        //anchors.verticalCenter : parent.verticalCenter
        anchors.top : parent.top
        anchors.topMargin : rWin.c.style.main.spacing*3
        color : "red"
        font.pixelSize : 64 * rWin.c.style.main.multiplier
        //TODO: handle location usage being disabled by the user
        //text : gps.hasFix ? "NO FIX" : "fix in progress"
        text : rWin.location.enabled ? "fix in progress" : "location usage disabled<br>(you can enable it from <i>Options->Location</i>"
    }
}