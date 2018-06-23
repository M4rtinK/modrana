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
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Map")
            icon : "map.svg"
            menu : "MapPage"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "UI")
            icon : "n900.svg"
            menu : "UIPage"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "POI")
            icon : "poi.svg"
            menu : "POIPage"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Navigation")
            icon : "navigation.svg"
            menu : "NavigationPage"
        }
         ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Tracks")
            icon : "tracklogs.svg"
            menu : "TracksPage"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Network")
            icon : "network.svg"
            menu : "NetworkPage"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Debug")
            icon : "debug.svg"
            menu : "DebugPage"
        }
    }
}