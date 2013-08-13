//TextButton.qml

import QtQuick 1.1
import "./qtc"

BackgroundRectangle {
    id : textButton
    property alias text : tbLabel.text
    signal clicked
    Label {
        id : tbLabel
        anchors.verticalCenter : parent.verticalCenter
        anchors.left : parent.left
        anchors.leftMargin : C.style.main.spacing
        anchors.right : parent.right
        anchors.rightMargin : C.style.main.spacing
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