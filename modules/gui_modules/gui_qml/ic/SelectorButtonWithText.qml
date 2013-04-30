//SelectorButtonWithText.qml
import QtQuick 1.1
import com.nokia.meego 1.0

Item {
    id: container

    height: label.height
    width : parent.width

    property alias text : label.text
    property alias buttonText : pfsButton.text
    property alias iconSource : pfsButton.iconSource
    property alias enabled : pfsButton.enabled
    property Item selector

    Label {
        id: label

        anchors {
            top: parent.top
            left: parent.left
            right: pfsButton.left
            rightMargin: 16
        }
    }

    Button {
        id : pfsButton
        iconSource : "image://theme/icon-m-common-combobox-arrow"
        width : 200
        anchors {
            right: parent.right
            verticalCenter: parent.verticalCenter
        }
        onClicked : {
            selector.open()
        }
    }
}
