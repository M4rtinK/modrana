//BackgroundRectangle.qml

import QtQuick 1.1

Rectangle {
    // border width == 1 causes rendering artifacts
    border.width : 2
    border.color : "white"
    property bool active : false
    color : active ? "darkblue" : "black"
}