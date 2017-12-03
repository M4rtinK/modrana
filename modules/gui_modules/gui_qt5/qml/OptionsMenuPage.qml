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
            icon : "map.png"
            menu : "MapPage"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "UI")
            icon : "n900.png"
            menu : "UIPage"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "POI")
            icon : "poi.png"
            menu : "POIPage"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Navigation")
            icon : "navigation.png"
            menu : "NavigationPage"
        }
         ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Tracks")
            icon : "tracklogs.png"
            menu : "TracksPage"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Network")
            icon : "network.png"
            menu : "NetworkPage"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Debug")
            icon : "debug.png"
            menu : "DebugPage"
        }
    }
}