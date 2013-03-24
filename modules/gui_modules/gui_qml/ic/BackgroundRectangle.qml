//BackgroundRectangle.qml

import QtQuick 1.1

Rectangle {
    border.width : 1
    border.color : "white"
    property bool active : false
    color : active ? "darkblue" : "black"
}