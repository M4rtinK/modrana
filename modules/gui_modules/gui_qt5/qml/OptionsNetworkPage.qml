//OptionsNetworkPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: optionsNetworkPage
    headerText : qsTr("Network")
    content : ContentColumn {
        spacing : rWin.c.style.main.spacing
        Item {
            id : spacer
            width : 1
            height : rWin.c.style.main.spacing
        }
        KeyComboBox {
            id : networkUsage
            label : qsTr("Network usage")
            key : "network"
            description: if (networkUsage.value == "minimal") {
                    qsTr("In <b>minimal</b> network usage mode no map tiles are downloaded over the network, only previously cached tiles are used.")
                } else {
                    qsTr("In <b>full</b> network usage mode no network usage restrictions are in place.")
                }
            model : ListModel {
                id : network
                ListElement {
                    text : QT_TRANSLATE_NOOP("ComboBox", "Full")
                    value : "full"
                }
                ListElement {
                    text : QT_TRANSLATE_NOOP("ComboBox", "Minimal")
                    value : "minimal"
                }
            }
            onItemChanged : {
                rWin.log.info("setting network mode: " + item.value)
            }
        }
        SectionHeader {
            text : qsTr("Tile download")
        }
        KeyComboBox {
            id : automaticDownloadThreadCount
            label : qsTr("Number of automatic tile download threads")
            key : "maxAutoDownloadThreads2"
            property string previousValue : ""
            defaultValue : rWin.c.default.autoDownloadThreadCount
            model : ListModel {
                id : maxAutoDownloadThreads2
                ListElement {
                    text : QT_TRANSLATE_NOOP("ComboBox", "1 (serial)")
                    value : "1"
                }
                ListElement {
                    text : QT_TRANSLATE_NOOP("ComboBox", "2")
                    value : "2"
                }
                 ListElement {
                    text : QT_TRANSLATE_NOOP("ComboBox", "4")
                    value : "4"
                }
                ListElement {
                    text : QT_TRANSLATE_NOOP("ComboBox", "10 (default)")
                    value : "10"
                }
                ListElement {
                    text : QT_TRANSLATE_NOOP("ComboBox", "20")
                    value : "20"
                }
                ListElement {
                    text : QT_TRANSLATE_NOOP("ComboBox", "50")
                    value : "50"
                }
            }
            onValueChanged : {
                rWin.log.info("setting automatic download thread count: " + item.value)
                // don't trigger the notification when the key combo box is initialized
                // for the first time with values from the Python backend (if any)
                if (previousValue && value != previousValue) {
                    rWin.notify(qsTr("You need to restart modRana for the thread number change to take effect."), 5000)
                }
                previousValue = value
            }
        }
    }
}
