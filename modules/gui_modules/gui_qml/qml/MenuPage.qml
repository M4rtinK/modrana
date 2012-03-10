import QtQuick 1.1
import com.nokia.meego 1.0

IconGridPage {
    model : ListModel {
        id : testModel
        ListElement {
            caption : "search"
            icon : "search.png"
            menu : ""
        }
        ListElement {
            caption : "routes"
            icon : "route.png"
            menu : ""
        }
        ListElement {
            caption : "POI"
            icon : "poi.png"
            menu : ""
        }
        ListElement {
            caption : "info"
            icon : "info.png"
            menu : ""
        }
        ListElement {
            caption : "mode"
            icon : "mode.png"
            menu : ""
        }
        ListElement {
            caption : "options"
            icon : "options.png"
            menu : "optionsMenu"
        }
    }
}