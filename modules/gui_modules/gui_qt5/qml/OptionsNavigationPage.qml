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
            visible : rWin.showUnfinishedFeatures
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
    }
}