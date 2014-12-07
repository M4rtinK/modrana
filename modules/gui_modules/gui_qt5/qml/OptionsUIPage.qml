//OptionsUIPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: optionsUIPage
    headerText : "UI"
    content : ContentColumn {
        Column {
            spacing : rWin.c.style.main.spacing
            anchors.left : parent.left
            anchors.right : parent.right
            KeyComboBox {
                id : themeCb
                label : qsTr("Theme")
                key : "theme"
                defaultValue : rWin.c.default.theme
                model : ListModel {
                    id : cbMenu
                    ListElement {
                        text : "Silica"
                        value : "silica"
                    }
                    ListElement {
                        text : "classic"
                        value : "default"
                    }
                    ListElement {
                        text : "night"
                        value : "night"
                    }
                }
                onItemChanged : {
                    rWin.log.info("setting theme: " + themeCb.item.value)
                }
            }
        }
        /*
        // Mode stuff is not yet used
        TextSwitch {
            text : qsTr("Show mode on menu button")
            checked : rWin.mapPage.showModeOnMenuButton
            onCheckedChanged : {
                 rWin.mapPage.showModeOnMenuButton = checked
                 rWin.set("showModeOnMenuButton", checked)
            }
        }
        */
        TextSwitch {
            text : qsTr("Animations")
            checked : rWin.animate
            onCheckedChanged : {
                 rWin.animate = checked
                 //rWin.set("QMLAnimate", checked)
            }
        }
        Label {
            text : qsTr("Screen")
        }
        TextSwitch {
            text : qsTr("Keep screen on")
            checked : rWin.keepScreenOn
            onCheckedChanged : {
                 rWin.keepScreenOn = checked
            }
        }
        Label {
            text : qsTr("Map screen")
        }
        TextSwitch {
            text : qsTr("Show compass")
            checked : rWin.mapPage.showCompass
            onCheckedChanged : {
                 rWin.mapPage.showCompass = checked
                 rWin.set("showQt5GUIMapCompass", checked)
            }
        }
        Label {
            text : qsTr("Compass opacity")
        }
        Slider {
            id : compassOpacitySlider
            width : parent.width
            stepSize : 0.1
            maximumValue : 1.0
            minimumValue : 0.0
            value : rWin.mapPage.compassOpacity
            valueText : ""
            onPressedChanged : {
                // set the value once users
                // stops interacting with the slider
                if (pressed == false) {
                    rWin.mapPage.compassOpacity = value
                    rWin.set("qt5GUIMapCompassOpacity", value)
                }
            }
        }
    }
}
