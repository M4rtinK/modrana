//IconButton.qml
/*
A simple button with an icon in the middle.
*/
import QtQuick 1.1

Rectangle {
    id : icb
    height : iconSize
    width : iconSize
    property real iconSize : 80
    property real margin : 8
    property alias iconName : themedIcon.iconName
    property color normalColor : modrana.theme.color.icon_button_normal
    property color toggledColor : modrana.theme.color.icon_button_toggled

    // "#c6d1f3" QML toggled
    // modRana theme:
    // #3c60fa outline
    // "#92aaf3" fill
    // "#00004d" main text
    radius : 10
    smooth : true
    signal clicked
    signal pressAndHold
    TIcon {
        id: themedIcon
        anchors.horizontalCenter : parent.horizontalCenter
        anchors.top : parent.top
        anchors.bottom : parent.bottom
        iconName : icon
        anchors.topMargin : icb.margin
        anchors.bottomMargin : icb.margin
        width : parent.width-icb.margin
        height : parent.height-icb.margin
    }
    MouseArea {
        anchors.fill : parent
        onClicked: icb.clicked()
        onPressedChanged: {
            pressed ? icb.color = toggledColor : icb.color = normalColor
        }
        onPressAndHold : {
            icb.pressAndHold()
        }

    }

}