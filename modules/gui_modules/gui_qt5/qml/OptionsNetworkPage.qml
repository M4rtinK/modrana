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
                description: if (networkUsage.value == "minimal") {
                        qsTr("In <b>minimal</b> network usage mode no map tiles are downloaded over the network, only previously cached tiles are used.")
                    } else {
                        qsTr("In <b>full</b> network usage mode no network usage restrictions are in place.")
                    }
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
                onItemChanged : {
                    rWin.log.info("setting network mode: " + item.value)
                }
            }
        }
    }
}
