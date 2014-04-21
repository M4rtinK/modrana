import QtQuick 2.0
import Sailfish.Silica 1.0
MouseArea {
    id : bMouse
    property color highlightedColor: Theme.rgba(Theme.highlightBackgroundColor, Theme.highlightBackgroundOpacity)
    implicitHeight: Theme.itemSizeSmall
    Rectangle {
        anchors.fill : parent
        property bool clickable : false
        color: bMouse.pressed ? highlightedColor : "transparent"
    }
}