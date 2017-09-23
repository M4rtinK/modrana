import QtQuick 2.0
import QtQuick.Controls 2.0
import "style.js" as S

MouseArea {
    id : bMouse
    property string highlightedColor: "darkblue"
    property string normalColor : "#92aaf3"
    property int cornerRadius : S.style.listView.cornerRadius
    // make it possible to simulate pressed state even if not physically pressed
    property bool pressed_override : false
    implicitHeight: S.style.dialog.item.height
    Rectangle {
        anchors.fill : parent
        property bool clickable : false
        color: bMouse.pressed || pressed_override ? highlightedColor : normalColor
        radius : cornerRadius
    }
}