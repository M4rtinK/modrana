import QtQuick 2.0


// map, ui, POI, navigation, network, debug


IconGridPage {

    function getPage(menu){
        return Qt.createComponent("Options" + menu + ".qml")
    }

    isMockup : false
    model : ListModel {
        id : testModel
        ListElement {
            caption : "Map"
            icon : "map.png"
            menu : "MapPage"
        }
        ListElement {
            caption : "UI"
            icon : "n900.png"
            menu : "UIPage"
        }
        ListElement {
            caption : "POI"
            icon : "poi.png"
            menu : "POIPage"
        }
        ListElement {
            caption : "Navigation"
            icon : "navigation.png"
            menu : "NavigationPage"
        }
        ListElement {
            caption : "Network"
            icon : "network.png"
            menu : "NetworkPage"
        }
        ListElement {
            caption : "Debug"
            icon : "debug.png"
            menu : "DebugPage"
        }
    }
}