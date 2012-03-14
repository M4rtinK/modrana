import QtQuick 1.1
import com.nokia.meego 1.0

// map, ui, POI, navigation, network, debug


IconGridPage {
    model : ListModel {
        id : testModel
        ListElement {
            caption : "Layer"
            icon : "map.png"
            menu : ""
        }
        ListElement {
            caption : "Download"
            icon : "download.png"
            menu : ""
        }
    }
}