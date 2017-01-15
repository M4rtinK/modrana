//PayPalButton.qml

import QtQuick 2.0
import UC 1.0

Rectangle {
    id : ppButton
    color : ppMA.pressed ? "yellow" : "gold"
    radius : 30
    width : 150 * rWin.c.style.m
    height : rWin.c.style.button.generic.height
    property string url : ""

    Label {
        anchors.horizontalCenter : parent.horizontalCenter
        anchors.verticalCenter : parent.verticalCenter
        text : "<b>PayPal</b>"
        font.pixelSize : 32 * rWin.c.style.m
    }
    MouseArea {
        id : ppMA
        anchors.fill : parent
        onClicked : {
            rWin.log.info('PayPal button clicked')
            Qt.openUrlExternally(url)
        }
    }
}


