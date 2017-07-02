//IconButton.qml
// A simple button with text & with map button color style

import QtQuick 2.0
import UC 1.0

Rectangle {
    id : mtb
    height : mtbLabel.height + 2 * margin
    width : mtbLabel.width + 2 * margin
    property real margin : rWin.c.style.main.spacing
    property color normalColor : "gray"
    property color toggledColor : rWin.theme.color.icon_button_toggled
    property color notEnabledColor : "lightgray"
    property bool checkable : false
    property bool checked : false
    property alias text : mtbLabel.text
    property alias textColor : mtbLabel.color

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
        if (mtb.enabled) {
            checked ? mtb.color = toggledColor : mtb.color = normalColor
        } else {
            mtb.color = notEnabledColor
        }
    }

    onCheckedChanged : {
        if (mtb.enabled) {
            checked ? mtb.color = toggledColor : mtb.color = normalColor
        }
    }

    Label {
        id : mtbLabel
        anchors.left : parent.left
        anchors.leftMargin : mtb.margin
        anchors.verticalCenter : parent.verticalCenter
        //anchors.right : parent.right
        //anchors.rightMargin : rWin.c.style.main.spacing
        //elide : Text.ElideRight
        //fontSizeMode : Text.HorizontalFit
        //horizontalAlignment : Text.AlignHCenter
    }

    MouseArea {
        anchors.fill : parent
        enabled : mtb.enabled
        onClicked: {
            mtb.clicked()
            if (mtb.checkable) {
                mtb.checked = !mtb.checked
            }
        }

        onPressedChanged : {
            pressed ? mtb.color = toggledColor : mtb.color = normalColor
        }

        onPressAndHold : {
            mtb.pressAndHold()
        }

    }

}