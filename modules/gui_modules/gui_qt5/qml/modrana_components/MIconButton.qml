//IconButton.qml
// A simple button with an icon in the middle.

import QtQuick 2.0
import UC 1.0

MThemedButton {
    id : icb
    height : iconSize
    width : iconSize
    property real iconSize : rWin.c.style.button.icon.size
    property alias iconName : themedIcon.iconName

    TIcon {
        id: themedIcon
        anchors.horizontalCenter : parent.horizontalCenter
        anchors.top : parent.top
        anchors.bottom : parent.bottom
        anchors.topMargin : icb.margin
        anchors.bottomMargin : icb.margin
        width : parent.width-icb.margin
        height : parent.height-icb.margin
    }
}
