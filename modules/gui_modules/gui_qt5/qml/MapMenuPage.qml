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
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Main map")
            icon : "map.png"
            //menu : "mapDialog"
            menu : "LayerPage"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Overlays")
            icon : "map_layers.png"
            menu : "LayersPage"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Clear")
            icon : "debug.png"
            menu : "ClearPage"
        }
        Component.onCompleted : {
            if (rWin.showUnfinishedFeatures) {
                testModel.append(
                    {"caption": "Download", "icon":"download.png", "menu":"DownloadPage"}
                )
            }
        }
    }
}