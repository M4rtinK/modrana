import QtQuick 1.1
import com.nokia.meego 1.0

IconGridPage {
    model : ListModel {
        id : testModel
        ListElement {
            caption : "Search"
            icon : "search.png"
            menu : ""
        }
        ListElement {
            caption : "Routes"
            icon : "route.png"
            menu : ""
        }
        ListElement {
            caption : "POI"
            icon : "poi.png"
            menu : ""
        }
        ListElement {
            caption : "Info"
            icon : "info.png"
            menu : ""
        }
        ListElement {
            caption : "Mode"
            icon : "mode.png"
            menu : ""
        }
        ListElement {
            caption : "Options"
            icon : "options.png"
            menu : "optionsMenu"
        }
    }
}