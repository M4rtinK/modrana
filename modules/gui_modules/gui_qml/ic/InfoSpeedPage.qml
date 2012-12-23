//InfoSpeedPage.qml

import QtQuick 1.1
import "qtc/PageStatus.js" as PageStatus

BasePage {
    id: speedPage
    headerText : "Speed"
    bottomPadding : 0
    isFlickable : false
    //anchors.fill : parent
    content {
        Item {
            id : spacer1
            anchors.fill : parent
            height : speedPage.height
            //anchors.top : parent.top
            //anchors.bottom : parent.bottom
            //height : 96
        }
        Text {
            id : currentSpeed
            anchors.verticalCenter : parent.verticalCenter
            //anchors.top : spacer1.bottom
            //anchors.topMargin : 96
            anchors.horizontalCenter : parent.horizontalCenter
            text: modules.getS("stats", "getCurrentSpeedString")
            font.pixelSize : 96
        }
    }

    Connections {
        target: status == PageStatus.Inactive ? null : gps
        onLastGoodFixChanged: {
            //console.log('SPEED UPDATE')
            currentSpeed.text = modules.getS("stats", "getCurrentSpeedString")
        }
    }
}