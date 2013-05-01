import QtQuick 1.1
import "./qtc"

// map, ui, POI, navigation, network, debug



IconGridPage {
    id : mapMenuPage
    function getPage(menu){
        if (menu == "mapDialog") {
            console.log("OPEN MAP LAYER DIALOG")
            layerSelectD.open()
        } else if (menu == "LayersPage") {
            var component = Qt.createComponent("Map" + menu + ".qml");
            if (component.status == Component.Ready) {
                var component = Qt.createComponent("Map" + menu + ".qml")
                var layersPage = component.createObject(rWin)
                return layersPage
             } else if (component.status == Component.Error) {
                 // Error Handling
                 console.log("Error loading component:", component.errorString());
             }
        } else {
            return Qt.createComponent("Map" + menu + ".qml")
        }
    }

    model : ListModel {
        id : testModel
        ListElement {
            caption : "Main map"
            icon : "map.png"
            menu : "mapDialog"
        }
        ListElement {
            caption : "Overlays"
            icon : "map_layers.png"
            menu : "LayersPage"
        }
        ListElement {
            caption : "Download"
            icon : "download.png"
            menu : ""
        }
    }

    Component.onCompleted : {
        layerSelectD.close()
    }

    MapLayerSelectionDialog {
        id : layerSelectD
        onLayerSelected  : {
            rWin.mapPage.getMap().setLayerById(0, layerId)
            rWin.pageStack.pop(null)
            accept()
        }
    }
}