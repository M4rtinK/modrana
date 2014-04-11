import QtQuick 2.0

IconGridPage {
    model : ListModel {
        id : testModel
        ListElement {
            caption : "Search"
            icon : "search.png"
            menu : "SearchMenu"
        }

        // TODO: un-comment once implemented
        /*
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
        */

        ListElement {
            caption : "Map"
            icon : "map.png"
            menu : "MapMenu"
        }

        // TODO: un-comment once
        // mode does something
        /*
        ListElement {
            caption : "Mode"
            icon : "mode.png"
            menu : "ModeMenu"
        }
        */
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
        Component.onCompleted : {
            if (rWin.showUnfinishedPages) {
                testModel.append(
                    {"caption": "Route", "icon":"route.png", "menu":""}
                )
            }
        }
    }
}