//OptionsNavigationPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: navigationPage
    headerText : "Navigation"

    content : ContentColumn {
        Label {
            text : qsTr("Routing")
        }
        KeyComboBox {
            id : routingProviderCb
            label : qsTr("Routing provider")
            key : "routingProvider"
            defaultValue : rWin.c.default.routingProvider
            visible : rWin.showUnfinishedFeatures
            model : ListModel {
                id : cbMenu
                ListElement {
                    text : "Google - online"
                    value : "GoogleDirections"
                }
                ListElement {
                    text : "Routino - on device"
                    value : "Routino"
                }
            }
            onItemChanged : {
                rWin.log.info("setting routing provider: " + routingProviderCb.item.value)
            }
        }
        KeyComboBox {
            id : routingModeCb
            label : qsTr("Routing mode")
            key : "routingModeQt5"
            defaultValue : 3
            // TODO: use values from modRana constants
            model : ListModel {
                ListElement {
                    text : "Car"
                    value : 3
                }
                ListElement {
                    text : "Walking"
                    value : 1
                }
                ListElement {
                    text : "Cycling"
                    value : 2
                }
            }
            onItemChanged : {
                rWin.log.info("setting routing mode: " + routingModeCb.item.value)
            }
        }
        KeyTextSwitch {
            text : qsTr("Avoid major highways")
            key : "routingAvoidHighways"
            defaultValue : false
        }
        KeyTextSwitch {
            text : qsTr("Avoid toll roads")
            key : "routingAvoidToll"
            defaultValue : false
        }
    }
}
