//BackgroundRectangle.qml

import QtQuick 2.0

Rectangle {
    property bool active : false
    color : active ? "darkblue" : rWin.theme.color.main_fill
    radius : rWin.c.style.listView.cornerRadius
}