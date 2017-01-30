//OptionsPOIPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: poiPage
    headerText : "POI"

    content : ContentColumn {
        Label {
            text : qsTr("Place search")
        }
        KeyTextSwitch {
            id : nominatimSwitch
            text : qsTr("Nominatim")
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
            text : qsTr("OSM Scout Server")
            key : "placeSearchOSMScoutServerEnabled"
            defaultValue : false
            onCheckedChanged : {
                if (checkedValid) {
                    nominatimSwitch.checked = !checked
                }
            }
        }
    }
}
