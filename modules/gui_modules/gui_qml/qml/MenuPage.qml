import QtQuick 1.1
import com.nokia.meego 1.0

IconGridPage {
    model : ListModel {
        id : testModel
        ListElement {
            caption : "Search"
            icon : "search.png"
            menu : "searchMenu"
        }
        ListElement {
            caption : "Routes"
            icon : "route.png"
            menu : "routesMenu"
        }
        ListElement {
            caption : "POI"
            icon : "poi.png"
            menu : "poiMenu"
        }
        ListElement {
            caption : "Info"
            icon : "info.png"
            menu : "infoMenu"
        }
        ListElement {
            caption : "Mode"
            icon : "mode.png"
            menu : "modeMenu"
        }
        ListElement {
            caption : "Options"
            icon : "options.png"
            menu : "optionsMenu"
        }
    }
}