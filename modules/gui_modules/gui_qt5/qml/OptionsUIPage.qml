//OptionsUIPage.qml

import QtQuick 2.0
import UC 1.0

BasePage {
    id: optionsUIPage
    headerText : "UI"

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
            Column {
                spacing : rWin.c.style.main.spacing
                Label {
                    text : qsTr("Theme")
                }
                KeyComboBox {
                    id : themeCb
                    //checkedButton : modrana.theme_id == "default" ? defaultButton : nightButton
                    key : "theme"
                    model : ListModel {
                        id : cbMenu
                        ListElement {
                            text : "default"
                            value : "default"

                        }
                        ListElement {
                            text : "night"
                            value : "night"
                        }
                    }

                    onItemChanged : {
                        console.log("setting theme: " + themeCb.item.value)
                    }
                }
            }
            SwitchWithText {
                text : qsTr("Show mode on menu button")
                checked : rWin.mapPage.showModeOnMenuButton
                onCheckedChanged : {
                     rWin.mapPage.showModeOnMenuButton = checked
                     rWin.set("showModeOnMenuButton", checked)
                }
            }
            SwitchWithText {
                text : qsTr("Animations")
                checked : rWin.animate
                onCheckedChanged : {
                     rWin.animate = checked
                     rWin.set("QMLAnimate", checked)
                }
            }
        }
    }
}
