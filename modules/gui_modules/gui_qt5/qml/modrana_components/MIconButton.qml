//IconButton.qml
// A simple button with an icon in the middle.

import QtQuick 2.0
import UC 1.0

Rectangle {
    id : icb
    height : iconSize
    width : iconSize
    property real iconSize : rWin.c.style.button.icon.size
    property real margin : rWin.c.style.main.spacing
    property alias iconName : themedIcon.iconName
    property color normalColor : rWin.theme.color.icon_button_normal
    property color toggledColor : rWin.theme.color.icon_button_toggled
    property color notEnabledColor : "lightgray"
    property bool checkable : false
    property bool checked : false
    property alias text : ibLabel.text

    color : normalColor

    // "#c6d1f3" QML toggled
    // modRana theme:
    // #3c60fa outline
    // "#92aaf3" fill
    // "#00004d" main text
    radius : 10 * rWin.c.style.m
    smooth : true
    signal clicked
    signal pressAndHold

    onEnabledChanged : {
        if (icb.enabled) {
            checked ? icb.color = toggledColor : icb.color = normalColor
        } else {
            icb.color = notEnabledColor
        }
    }

    onCheckedChanged : {
        if (icb.enabled) {
            checked ? icb.color = toggledColor : icb.color = normalColor
        }
    }

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

    Label {
        id : ibLabel
        anchors.verticalCenter : parent.verticalCenter
        anchors.left : parent.left
        anchors.leftMargin : rWin.c.style.main.spacing
        anchors.right : parent.right
        anchors.rightMargin : rWin.c.style.main.spacing
        elide : Text.ElideRight
        fontSizeMode : Text.HorizontalFit
        horizontalAlignment : Text.AlignHCenter
    }

    MouseArea {
        anchors.fill : parent
        enabled : icb.enabled
        onClicked: {
            icb.clicked()
            if (icb.checkable) {
                icb.checked = !icb.checked
            }
        }

        onPressedChanged : {
            pressed ? icb.color = toggledColor : icb.color = normalColor
        }

        onPressAndHold : {
            icb.pressAndHold()
        }

    }

}