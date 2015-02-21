import QtQuick 2.0
import QtQuick.Controls 1.0
import "style.js" as S

MouseArea {
    id : bMouse
    property string highlightedColor: "darkblue"
    property string normalColor : "#92aaf3"
    implicitHeight: S.style.dialog.item.height
    Rectangle {
        anchors.fill : parent
        property bool clickable : false
        color: bMouse.pressed ? highlightedColor : normalColor
        radius : S.style.listView.cornerRadius
    }
}