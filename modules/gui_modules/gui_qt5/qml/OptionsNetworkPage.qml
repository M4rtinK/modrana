//OptionsNetworkPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: optionsNetworkPage
    headerText : "Network"
    content : ContentColumn {
        Column {
            spacing : rWin.c.style.main.spacing
            anchors.left : parent.left
            anchors.right : parent.right
            KeyComboBox {
                id : networkUsage
                label : qsTr("Network Usage")
                key : "network"
                model : ListModel {
                    id : network
                    ListElement {
                        text : "Full"
                        value : "full"
                    }
                    ListElement {
                        text : "Minimal"
                        value : "minimal"
                    }
                }
            }
// the onItemChanged bit below breaks the page, no idea why at the moment
// Frederik
//            onItemChanged : {
//                rWin.log.info("setting network mode: " + network.value)
//            }
        }
    }
}
