//InfoSpeedPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: speedPage
    headerText : qsTr("Speed")
    isFlickable : false
    property string currentSpeedString : qsTr("unknown")
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
        anchors.horizontalCenter : parent.horizontalCenter
        text: speedStatsString
        font.pixelSize : 32 * rWin.c.style.main.multiplier
    }

    function setSpeeds(speeds) {
        speedPage.currentSpeedString = speeds.current;
        speedPage.speedStatsString = qsTr("maximum") + ": " + speeds.max + "   " + qsTr("average") + ": " + speeds.avg
    }

    Connections {
        // deactivate the connection when this page is not active
        target: speedPage.isActive ? rWin : null
        onPosChanged: {
            rWin.python.call("modrana.gui.modules.stats.getSpeedStatsDict", [], setSpeeds)
        }
    }
}