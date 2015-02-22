//TextButton.qml

import QtQuick 2.0
import UC 1.0

ThemedBackgroundRectangle {
    id : textButton
    property alias text : tbLabel.text
    signal clicked
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
    MouseArea {
        id : tbMA
        anchors.fill : parent
        onClicked : {
            textButton.clicked()
        }
    }
}