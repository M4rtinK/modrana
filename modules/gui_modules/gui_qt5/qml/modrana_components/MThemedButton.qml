//IconButton.qml
// A simple button with an icon in the middle.

import QtQuick 2.0
import UC 1.0

Rectangle {
    id : icb
    property real margin : rWin.c.style.main.spacing
    property color normalColor : rWin.theme.color.icon_button_normal
    property color toggledColor : rWin.theme.color.icon_button_toggled
    property color notEnabledColor : "lightgray"
    property bool checkable : false
    property bool checked : false
    color : normalColor

    border.width : 1 * rWin.c.style.m
    border.color : "black"

    radius : 4 * rWin.c.style.m
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
