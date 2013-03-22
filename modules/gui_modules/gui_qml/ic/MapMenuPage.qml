import QtQuick 1.1
//import com.nokia.meego 1.0
import "./qtc"


// map, ui, POI, navigation, network, debug



IconGridPage {
    id : mapMenuPage
    function getPage(menu){
        if (menu == "mapDialog") {
            console.log("OPEN MAP LAYER DIALOG")
            layerSelectD.open()
        }
    }

    model : ListModel {
        id : testModel
        ListElement {
            caption : "Layer"
            icon : "map_layers.png"
            menu : "mapDialog"
        }
        ListElement {
            caption : "Layers"
            icon : "map_layers.png"
            menu : "mapLayers"
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
            rWin.mapPage.getMap().setLayer(0, selectedLayer)
            rWin.pageStack.pop(null)
            accept()
        }
    }
}