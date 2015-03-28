//TextButton.qml

import QtQuick 2.0
import UC 1.0

ThemedBackgroundRectangle {
    id : textButton
    property alias text : tbLabel.text
    Label {
        id : tbLabel
        anchors.verticalCenter : parent.verticalCenter
        anchors.left : parent.left
        anchors.leftMargin : rWin.c.style.main.spacing
        anchors.right : parent.right
        anchors.rightMargin : rWin.c.style.main.spacing
        elide : Text.ElideRight
        horizontalAlignment : Text.AlignHCenter
    }
    onClicked : {
        textButton.clicked()
    }
}