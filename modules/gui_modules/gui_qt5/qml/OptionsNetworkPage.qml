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
            KeyComboBox {
                id : automaticDownloadThreadCount
                label : qsTr("Number of automatic tile download threads")
                key : "maxAutoDownloadThreads2"
                property string previousValue : null
                defaultValue : rWin.c.default.autoDownloadThreadCount
                model : ListModel {
                    id : maxAutoDownloadThreads2
                    ListElement {
                        text : "1 (serial)"
                        value : "1"
                    }
                    ListElement {
                        text : "5"
                        value : "5"
                    }
                    ListElement {
                        text : "10 (default)"
                        value : "10"
                    }
                    ListElement {
                        text : "20"
                        value : "20"
                    }
                    ListElement {
                        text : "50"
                        value : "50"
                    }
                }
                onValueChanged : {
                    rWin.log.info("setting automatic download thread count: " + item.value)
                    // don't trigger the notification when the key combo box is initialized
                    // for the first time with values from the Python backend (if any)
                    if (previousValue && value != previousValue) {
                        rWin.notify("You need to restart modRana for the thread number change to take effect.", 5000)
                    }
                    previousValue = value
                }
            }
        }
    }
}
