//BitcoinPage.qml

import QtQuick 2.0
import UC 1.0

BasePage {
    id : bitcoinPage
    headerText: "Bitcoin address"
    property string url : ""
    content : ContentColumn {
        id: dialogContent
        Image {
            id : bitcoinQrCode
            anchors.horizontalCenter : parent.horizontalCenter
            source : "image://python/icon/" + rWin.theme.id + "/qrcode_bitcoin.png"
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
                rWin.notify("Bitcoin address copied to clipboard", 3000)
            }
        }
    }
}