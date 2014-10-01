//InfoSpeedPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: speedPage
    headerText : "Speed"
    bottomPadding : 0
    isFlickable : false
    property string currentSpeedString : "unknown"
    property string speedStatsString : ""

    Label {
        id : currentSpeed
        parent : contentParent
        anchors.verticalCenter : parent.verticalCenter
        anchors.horizontalCenter : parent.horizontalCenter
        text: currentSpeedString
        font.pixelSize : 96 * rWin.c.style.main.multiplier
    }
    Label {
        id : otherSpeed
        parent : contentParent
        anchors.top : currentSpeed.bottom
        anchors.topMargin : 96 * rWin.c.style.main.multiplier
        anchors.horizontalCenter : content.horizontalCenter
        text: speedStatsString
        font.pixelSize : 32 * rWin.c.style.main.multiplier
    }

    function setSpeeds(speeds) {
        speedPage.currentSpeedString = speeds.current;
        speedPage.speedStatsString = "maximum: " + speeds.max + "   average: " + speeds.avg
    }

    Connections {
        // deactivate the connection when this page is not active
        target: speedPage.isActive ? rWin : null
        onPosChanged: {
            rWin.python.call("modrana.gui.modules.stats.getSpeedStatsDict", [], setSpeeds)
        }
    }
}