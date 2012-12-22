//InfoSpeedPage.qml

import QtQuick 1.1

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
            anchors.verticalCenter : parent.verticalCenter
            //anchors.top : spacer1.bottom
            //anchors.topMargin : 96
            anchors.horizontalCenter : parent.horizontalCenter
            id : currentSpeed
            text: "" + 88 + "km"
            font.pixelSize : 96
        }
    }
}