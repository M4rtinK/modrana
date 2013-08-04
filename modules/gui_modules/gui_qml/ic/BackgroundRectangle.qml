//BackgroundRectangle.qml

import QtQuick 1.1

Rectangle {
    property bool active : false
    color : active ? "darkblue" : modrana.theme.color.main_fill
    radius : C.style.listView.cornerRadius
}