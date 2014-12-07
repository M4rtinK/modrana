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
                description: qsTr("In minimal network usage mode no map tiles are downloaded over the network, only previously cached tiles are used.")
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
