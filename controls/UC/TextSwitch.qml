import QtQuick 2.0
import QtQuick.Controls 2.0
import "style.js" as S

Item {
    id: container

    height: label.height
    width : parent.width

    property alias text: label.text
    property alias checked: switcher.checked

    Label {
        id: label
        anchors {
            top: parent.top
            left: parent.left
            right: switcher.left
            rightMargin: S.style.main.spacingBig
        }
    }

    Switch {
        id: switcher
        anchors {
            right: parent.right
            verticalCenter: parent.verticalCenter
        }
    }
}
