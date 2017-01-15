//BitcoinButton.qml

import QtQuick 2.0
import UC 1.0

Rectangle {
    id : bitcoinButton
    color : bitcoinMA.pressed ? "silver" : "black"
    radius : 25
    border.width : 2
    border.color : "white"
    width : 150 * rWin.c.style.m
    height : rWin.c.style.button.generic.height * 0.85
    property string url : ""

    Label {
        anchors.horizontalCenter : parent.horizontalCenter
        anchors.verticalCenter : parent.verticalCenter
        font.family: "Arial"
        font.pixelSize : 24 * rWin.c.style.m
        text : "<b>Bitcoin</b>"
        color : bitcoinMA.pressed ? "black" : "white"
        width : parent.width
        horizontalAlignment : Text.AlignHCenter
        verticalAlignment : Text.AlignVCenter
    }
    MouseArea {
        id : bitcoinMA
        anchors.fill : parent
        onClicked : {
            rWin.log.info('Bitcoin button clicked')
            var bitcoinPage = Qt.createComponent("BitcoinPage.qml")
            rWin.pushPage(bitcoinPage, {url : bitcoinButton.url}, rWin.animate)
        }
    }
}


