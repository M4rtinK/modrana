//InfoSpeedPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"
import "functions.js" as F

BasePage {
    id: speedPage
    headerText : qsTr("Speed")
    isFlickable : false
    property bool currentSpeedKnown : false
    property int currentSpeedFontBaseSize : speedPage.currentSpeedKnown ? 96 : 48
    property string currentSpeedString : qsTr("unknown")
    property string speedStatsString : ""

    Label {
        id : currentSpeed
        anchors.verticalCenter : parent.verticalCenter
        anchors.horizontalCenter : parent.horizontalCenter
        text: currentSpeedString
        font.pixelSize : currentSpeedFontBaseSize * rWin.c.style.main.multiplier
    }
    Label {
        id : otherSpeed
        anchors.top : currentSpeed.bottom
        anchors.topMargin : speedPage.currentSpeedFontBaseSize * rWin.c.style.main.multiplier
        anchors.horizontalCenter : parent.horizontalCenter
        text: speedStatsString
        font.pixelSize : 32 * rWin.c.style.main.multiplier
    }

    function setSpeeds(speeds) {
        speedPage.currentSpeedKnown = true
        speedPage.currentSpeedString = F.formatSpeedKmh(speeds.current)
        var maxSpeed = F.formatSpeedKmh(speeds.max)
        var avgSpeed = F.formatSpeedKmh(speeds.avg)
        speedPage.speedStatsString = qsTr("maximum") + ": " + maxSpeed + "   " + qsTr("average") + ": " + avgSpeed
    }

    Connections {
        // deactivate the connection when this page is not active
        target: speedPage.isActive ? rWin : null
        onPosChanged: {
            rWin.python.call("modrana.gui.modules.stats.getSpeedStatsDict", [], setSpeeds)
        }
    }
}