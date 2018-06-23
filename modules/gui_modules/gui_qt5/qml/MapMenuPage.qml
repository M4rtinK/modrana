import QtQuick 2.0
import UC 1.0
import "modrana_components"

IconGridPage {
    id : mapMenuPage

    function getPage(menu){
        return Qt.createComponent("Map" + menu + ".qml")
    }

    model : ListModel {
        id : testModel
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Main map")
            icon : "map.svg"
            menu : "LayerPage"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Overlays")
            icon : "map_layers.svg"
            menu : "LayersPage"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Clear")
            icon : "clear.svg"
            menu : "ClearPage"
        }
    }
}