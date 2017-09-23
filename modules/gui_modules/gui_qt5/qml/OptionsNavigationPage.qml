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
            model : ListModel {
                id : cbMenu
                ListElement {
                    text : "Google - online"
                    value : "GoogleDirections"
                }
                ListElement {
                    text : "Monav - on device"
                    value : "MonavLight"
                }
                ListElement {
                    text : "OSM Scout Server - on device"
                    value : "OSMScoutServer"
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
        Label {
            text : qsTr("Route opacity")
        }
        Slider {
            id : routeOpacitySlider
            width : parent.width
            stepSize : 0.1
            value : rWin.mapPage.routeOpacity
            valueText : ""
            onPressedChanged : {
                // set the value once users
                // stops interacting with the slider
                if (pressed == false) {
                    rWin.mapPage.routeOpacity = value
                    rWin.set("qt5GUIRouteOpacity", value)
                }
            }
        }


    }
}
