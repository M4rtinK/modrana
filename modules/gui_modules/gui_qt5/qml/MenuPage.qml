import QtQuick 2.0
import "modrana_components"

IconGridPage {

    function getPage(menu) {
        if (menu == "RouteMenu") {
            // until we have a proper routing page just enable
            // a simplified routing mode right away :)
            rWin.mapPage.enableRoutingUI(true)
            rWin.getPage(null)
            rWin.notify("Routing mode enabled", 3000)
        } else if (menu == "POIMenu") {
            // make sure poi listing is always reloaded on entry
            return rWin.loadPage("POICategoryListPage")

        } else {
            // just do the normal thing
            return rWin.getPage(menu)
        }
    }

    model : ListModel {
        id : testModel
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Search")
            icon : "search.png"
            menu : "SearchMenu"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Route")
            icon : "route.png"
            menu : "RouteMenu"
        }

        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Map")
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
            caption : QT_TRANSLATE_NOOP("IconGridPage", "POI")
            icon : "poi.png"
            menu : "POIMenu"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Tracks")
            icon : "tracklogs.png"
            menu : "TracksMenu"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Info")
            icon : "info.png"
            menu : "InfoMenu"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Options")
            icon : "3gears.png"
            menu : "OptionsMenu"
        }

        Component.onCompleted : {
            if (rWin.showUnfinishedFeatures) {
                testModel.append(
                    {"caption": "POI", "icon":"poi.png", "menu":""}
                )
                testModel.append(
                    {"caption": "Data", "icon":"download.png", "menu":""}
                )
            }
        }
    }
}