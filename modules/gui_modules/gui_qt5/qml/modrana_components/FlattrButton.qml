//FlattrButton.qml

import QtQuick 2.0
import UC 1.0

Rectangle {
    id : flattrButton
    color : flattrMA.pressed ? "limegreen" : "green"
    radius : 5
    width : 150 * rWin.c.style.m
    // height should be slightly smaller than for the flattr button
    height : rWin.c.style.button.generic.height * 0.75
    property string url : ""

    Label {
        anchors.horizontalCenter : parent.horizontalCenter
        anchors.verticalCenter : parent.verticalCenter
        text : "<b>Flattr this !</b>"
        color : "white"
        font.pixelSize : 20 * rWin.c.style.m
    }
    MouseArea {
        id : flattrMA
        anchors.fill : parent
        onClicked : {
            rWin.log.info('Flattr button clicked')
            Qt.openUrlExternally(url)
        }
    }
}


