import QtQuick 2.0
import "modrana_components"

IconGridPage {

    function getPage(menu) {
        if (menu == "RouteMenu") {
            // until we have a proper routing page just enable
            // a simplified routing mode right away :)
            rWin.mapPage.enableRoutingUI(true)
            rWin.getPage(null)
            rWin.notify(qsTr("Routing mode enabled"), 3000)
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
            icon : "search.svg"
            menu : "SearchMenu"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Route")
            icon : "route.svg"
            menu : "RouteMenu"
        }

        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Map")
            icon : "map.svg"
            menu : "MapMenu"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "POI")
            icon : "poi.svg"
            menu : "POIMenu"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Tracks")
            icon : "tracklogs.svg"
            menu : "TracksMenu"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Info")
            icon : "info.svg"
            menu : "InfoMenu"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Options")
            icon : "options.svg"
            menu : "OptionsMenu"
        }
    }
}