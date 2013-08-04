//OptionsUIPage.qml

import QtQuick 1.1
import "qtc/PageStatus.js" as PageStatus
import "./qtc"
import com.nokia.meego 1.0

BasePage {
    id: optionsUIPage
    headerText : "UI"

    content {
        Column {
            anchors.top : parent.top
            anchors.left : parent.left
            anchors.right : parent.right
            anchors.topMargin : C.style.main.spacing
            anchors.leftMargin : C.style.main.spacing
            anchors.rightMargin : C.style.main.spacing
            spacing : C.style.main.spacingBig * 2
            width : parent.width
            Column {
                spacing : C.style.main.spacing
                Label {
                    text : qsTr("Theme")
                }
                // once more themes are available,
                // use a picker button ?
                ButtonRow {
                    checkedButton : modrana.theme_id == "default" ? defaultButton : nightButton
                    Button {
                        id : defaultButton
                        text : "default"
                        onClicked : modrana.theme_id = "default"

                    }
                    Button {
                        id : nightButton
                        text : "night"
                        onClicked : modrana.theme_id = "night"
                    }
                }
            }
            SwitchWithText {
                text : qsTr("Show mode on menu button")
                checked : rWin.mapPage.showModeOnMenuButton
                onCheckedChanged : {
                     rWin.mapPage.showModeOnMenuButton = checked
                     options.set("showModeOnMenuButton", checked)
                }
            }
            SwitchWithText {
                text : qsTr("Animations")
                checked : rWin.animate
                onCheckedChanged : {
                     rWin.animate = checked
                     options.set("QMLAnimate", checked)
                }
            }
        }
    }
}
