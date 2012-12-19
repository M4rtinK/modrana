import QtQuick 1.1


// map, ui, POI, navigation, network, debug


IconGridPage {
    isMockup : true
    model : ListModel {
        id : testModel
        ListElement {
            caption : "Map"
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
            caption : "Navigation"
            icon : "navigation.png"
            menu : ""
        }
        ListElement {
            caption : "Network"
            icon : "network.png"
            menu : ""
        }
        ListElement {
            caption : "Debug"
            icon : "debug.png"
            menu : ""
        }
    }
}