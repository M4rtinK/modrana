//OptionsUIPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: optionsUIPage
    headerText : qsTr("UI")
    content : ContentColumn {
        spacing : rWin.c.style.main.spacing
        Item {
            id : spacer
            width : 1
            height : rWin.c.style.main.spacing
        }
        KeyComboBox {
            id : themeCb
            label : qsTr("Theme")
            key : "theme"
            defaultValue : rWin.c.default.theme
            model : ListModel {
                id : cbMenu
                ListElement {
                    text : QT_TRANSLATE_NOOP("ComboBox", "Silica")
                    value : "silica"
                }
                ListElement {
                    text : QT_TRANSLATE_NOOP("ComboBox", "classic")
                    value : "default"
                }
                ListElement {
                    text : QT_TRANSLATE_NOOP("ComboBox", "night")
                    value : "night"
                }
            }
            onItemChanged : {
                if (themeCb.item) {
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
            }
        }
        TextSwitch {
            text : qsTr("Show back button")
            checked : rWin.showBackButton
            onCheckedChanged : {
                rWin.showBackButton = checked
            }
            // only show this switch on platforms that don't
            // require the back button, so that users don't
            // easily "luck themselves out"
            visible : !rWin.platform.needs_back_button
        }
        SectionHeader {
            text : qsTr("Screen")
            visible : keepScreenOnSwitch.visible
        }
        TextSwitch {
            id : keepScreenOnSwitch
            text : qsTr("Keep screen on")
            checked : rWin.keepScreenOn
            visible : rWin.keepAlive.available
            onCheckedChanged : {
                 rWin.keepScreenOn = checked
            }
        }
        SectionHeader {
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
