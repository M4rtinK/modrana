import QtQuick 2.0
import QtQuick.Controls 1.0

MouseArea {
    id : bMouse
    property string highlightedColor: "darkblue"
    implicitHeight: rWin.c.style.dialog.item.height
    Rectangle {
        anchors.fill : parent
        property bool clickable : false
        color: bMouse.pressed ? highlightedColor : rWin.theme.color.main_fill
        radius : rWin.c.style.listView.cornerRadius
    }
}