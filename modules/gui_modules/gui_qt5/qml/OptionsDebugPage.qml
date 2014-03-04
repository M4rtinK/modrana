//OptionsDebugPage.qml

import QtQuick 2.0
import UC 1.0

BasePage {
    id: debugPage
    headerText : "Debug"

    content {
        Column {
            anchors.top : parent.top
            anchors.left : parent.left
            anchors.right : parent.right
            anchors.topMargin : rWin.c.style.main.spacing
            anchors.leftMargin : rWin.c.style.main.spacing
            anchors.rightMargin : rWin.c.style.main.spacing
            spacing : rWin.c.style.main.spacingBig * 2
            width : parent.width
            TextSwitch {
                text : qsTr("Show debug button")
                checked : rWin.showDebugButton
                onCheckedChanged : {
                     rWin.showDebugButton = checked
                     rWin.set("showQt5GUIDebugButton", checked)
                }
            }
            width : parent.width
            TextSwitch {
                text : qsTr("Show unfinished pages")
                checked : rWin.showDebugButton
                onCheckedChanged : {
                     rWin.showDebugButton = checked
                     rWin.set("showQt5GUIUnfinishedPages", checked)
                }
            }
        }
    }
}
