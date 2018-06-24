//BitcoinPage.qml

import QtQuick 2.0
import UC 1.0

BasePage {
    id : bitcoinPage
    headerText: qsTr("Bitcoin address")
    property string url : ""
    content : ContentColumn {
        id: dialogContent
        Image {
            id : bitcoinQrCode
            property real sizeRatio : rWin.inPortrait ? 0.5 : 0.25
            width : parent.width * sizeRatio
            height : parent.width * sizeRatio
            anchors.horizontalCenter : parent.horizontalCenter
            asynchronous : true
            smooth: true
            source : "image://python/icon/" + rWin.theme.id + "/qrcode_bitcoin.svg"
        }
        TextInput {
            id : urlField
            anchors.horizontalCenter : parent.horizontalCenter
            font.pointSize : 20 * rWin.c.style.m
            height : 48 * rWin.c.style.m
            width : bitcoinPage.width - 24 * rWin.c.style.m
            text : bitcoinPage.url
            wrapMode : TextInput.WrapAnywhere
            horizontalAlignment : TextInput.AlignHCenter
            onTextChanged : {
                selectAll()
            }
        }
        Button {
            anchors.horizontalCenter : parent.horizontalCenter
            text: qsTr("Copy to clipboard")
            onClicked: {
                urlField.selectAll()
                urlField.copy()
                rWin.notify(qsTr("Bitcoin address copied to clipboard"), 3000)
            }
        }
    }
}