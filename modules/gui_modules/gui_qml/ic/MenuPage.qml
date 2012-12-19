import QtQuick 1.1

IconGridPage {
    model : ListModel {
        id : testModel
        ListElement {
            caption : "Search"
            icon : "search.png"
            menu : "SearchMenu"
        }
        ListElement {
            caption : "Routes"
            icon : "route.png"
            menu : "RoutesMenu"
        }
        ListElement {
            caption : "POI"
            icon : "poi.png"
            menu : "PoiMenu"
        }
        ListElement {
            caption : "Map"
            icon : "map.png"
            menu : "MapMenu"
        }
        ListElement {
            caption : "Mode"
            icon : "mode.png"
            menu : "ModeMenu"
        }
        ListElement {
            caption : "Info"
            icon : "info.png"
            menu : "InfoMenu"
        }
        ListElement {
            caption : "Options"
            icon : "3gears.png"
            menu : "OptionsMenu"
        }
    }
}