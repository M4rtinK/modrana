import QtQuick 1.1
import com.nokia.meego 1.0

// map, ui, POI, navigation, network, debug


IconGridPage {
    model : ListModel {
        id : testModel
        ListElement {
            caption : "map"
            icon : "map.png"
            menu : ""
        }
        ListElement {
            caption : "UI"
            icon : "n900.png"
            menu : ""
        }
        ListElement {
            caption : "POI"
            icon : "poi.png"
            menu : ""
        }
        ListElement {
            caption : "navigation"
            icon : "gps_satellite.png"
            menu : ""
        }
        ListElement {
            caption : "network"
            icon : "network.png"
            menu : ""
        }
        ListElement {
            caption : "debug"
            icon : "debug.png"
            menu : ""
        }
    }
}