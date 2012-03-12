import QtQuick 1.1
import com.nokia.meego 1.0

// map, ui, POI, navigation, network, debug


IconGridPage {
    model : ListModel {
        id : testModel
        ListElement {
            caption : "Compass"
            icon : "windrose-simple.svg"
            menu : ""
        }
        ListElement {
            caption : "About"
            icon : "info.png"
            menu : ""
        }
    }
}