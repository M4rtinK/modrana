//HeaderDialog.qml

import QtQuick 1.1
import com.nokia.meego 1.0

Dialog {
    id : bitcoinDialog
    width : parent.width - 30
    property Style platformStyle: SelectionDialogStyle {}
    property string titleText: "Bitcoin address"
    title: Item {
        id: header
        height: bitcoinDialog.platformStyle.titleBarHeight
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        Item {
            id: labelField
            anchors.fill:  parent
            Item {
                id: labelWrapper
                anchors.left: parent.left
                anchors.right: closeButton.left
                anchors.bottom:  parent.bottom
                anchors.bottomMargin: bitcoinDialog.platformStyle.titleBarLineMargin
                height: titleLabel.height
                Label {
                    id: titleLabel
                    x: bitcoinDialog.platformStyle.titleBarIndent
                    width: parent.width - closeButton.width
                    font: bitcoinDialog.platformStyle.titleBarFont
                    color: bitcoinDialog.platformStyle.commonLabelColor
                    elide: bitcoinDialog.platformStyle.titleElideMode
                    text: bitcoinDialog.titleText
                }
            }
            Image {
                id: closeButton
                anchors.verticalCenter : labelWrapper.verticalCenter
                anchors.right: labelField.right
                opacity: closeButtonArea.pressed ? 0.5 : 1.0
                source: "image://theme/icon-m-common-dialog-close"
                MouseArea {
                    id: closeButtonArea
                    anchors.fill: parent
                    onClicked:  {bitcoinDialog.reject();}
                }
            }
        }
        Rectangle {
            id: headerLine
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom:  header.bottom
            height: 1
            color: "#4D4D4D"
        }
    }
    content:Item {
        id: dialogContent
        width : parent.width
        height : bitcoinQrCode.height + urlField.height + 32
    }
}