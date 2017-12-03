import QtQuick 2.0
import "modrana_components"

// map, ui, POI, navigation, network, debug


IconGridPage {

    function getPage(menu){
        return Qt.createComponent("Options" + menu + ".qml")
    }

    isMockup : false
    model : ListModel {
        id : testModel
        ListElement {
            caption : QT_TR_NOOP("Map")
            icon : "map.png"
            menu : "MapPage"
        }
        ListElement {
            caption : QT_TR_NOOP("UI")
            icon : "n900.png"
            menu : "UIPage"
        }
        ListElement {
            caption : QT_TR_NOOP("POI")
            icon : "poi.png"
            menu : "POIPage"
        }
        ListElement {
            caption : QT_TR_NOOP("Navigation")
            icon : "navigation.png"
            menu : "NavigationPage"
        }
         ListElement {
            caption : QT_TR_NOOP("Tracks")
            icon : "tracklogs.png"
            menu : "TracksPage"
        }
        ListElement {
            caption : QT_TR_NOOP("Network")
            icon : "network.png"
            menu : "NetworkPage"
        }
        ListElement {
            caption : QT_TR_NOOP("Debug")
            icon : "debug.png"
            menu : "DebugPage"
        }
    }
}