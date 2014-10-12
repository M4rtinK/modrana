import QtQuick 2.0
import UC 1.0
import "modrana_components"

IconGridPage {
    id : mapMenuPage

    function setLayer(layerId) {
        rWin.mapPage.getMap().setLayerById(0, layerId)
        rWin.push(null, !rWin.animate)
    }

    function getPage(menu){
        return Qt.createComponent("Map" + menu + ".qml")
    }

    model : ListModel {
        id : testModel
        ListElement {
            caption : "Main map"
            icon : "map.png"
            //menu : "mapDialog"
            menu : "LayerPage"
        }
        ListElement {
            caption : "Overlays"
            icon : "map_layers.png"
            menu : "LayersPage"
        }
        Component.onCompleted : {
            if (rWin.showUnfinishedPages.value) {
                testModel.append(
                    {"caption": "Download", "icon":"download.png", "menu":"DownloadPage"}
                )
            }
        }
    }
}