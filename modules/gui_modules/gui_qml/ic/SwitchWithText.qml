//SwitchWithText.qml
import QtQuick 1.1
import com.nokia.meego 1.0

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
            rightMargin: 16
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
