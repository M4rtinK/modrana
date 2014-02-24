import QtQuick 2.0
import UC 1.0

IconGridPage {
    id : mapMenuPage

    function setLayer(layerId) {
        rWin.mapPage.getMap().setLayerById(0, layerId)
        rWin.push(null, !rWin.animate)
    }

    function getPage(menu){
        if (menu == "LayerPage") {
            console.log("OPEN MAP LAYER PAGE")
            return Qt.createComponent("Map" + menu + ".qml")
        } else {
            return Qt.createComponent("Map" + menu + ".qml")
        }
        /*
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
        */
    }

    model : ListModel {
        id : testModel
        ListElement {
            caption : "Main map"
            icon : "map.png"
            //menu : "mapDialog"
            menu : "LayerPage"
        }

        // not yet implemented
        /*
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
        */
    }
}