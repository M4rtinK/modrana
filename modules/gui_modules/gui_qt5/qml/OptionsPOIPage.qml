//OptionsPOIPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: poiPage
    headerText : qsTr("POI")

    content : ContentColumn {
        SectionHeader {
            text : qsTr("Place search")
        }
        KeyTextSwitch {
            id : nominatimSwitch
            text : qsTr("Nominatim (online)")
            key : "placeSearchNominatimEnabled"
            defaultValue : false
            onCheckedChanged : {
                if (checkedValid) {
                    osmScoutServerSwitch.checked = !checked
                }
            }
        }
        KeyTextSwitch {
            id: osmScoutServerSwitch
            text : qsTr("OSM Scout Server (on device)")
            key : "placeSearchOSMScoutServerEnabled"
            defaultValue : false
            onCheckedChanged : {
                if (checkedValid) {
                    nominatimSwitch.checked = !checked
                }
            }
        }
        SectionHeader {
            text : qsTr("Local search")
        }
        KeyTextSwitch {
            id : googleLocalSearchSwitch
            text : qsTr("Google (online)")
            key : "localSearchGoogleEnabled"
            defaultValue : false
            onCheckedChanged : {
                if (checkedValid) {
                    osmScoutServerLocalSearchSwitch.checked = !checked
                }
            }
        }
        KeyTextSwitch {
            id: osmScoutServerLocalSearchSwitch
            text : qsTr("OSM Scout Server (on device)")
            key : "localSearchOSMScoutServerEnabled"
            defaultValue : false
            onCheckedChanged : {
                if (checkedValid) {
                    googleLocalSearchSwitch.checked = !checked
                }
            }
        }
    }
}
