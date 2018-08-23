import QtQuick 2.0
import UC 1.0
import "modrana_components"

MapLayerSelector {
    property int layerIndex : 0
    property bool returnToMap : true
    onLayerSelected : {
        rWin.set("layer", layerId)
        rWin.mapPage.setMapLayerByIndex(layerIndex, layerId)
        if(returnToMap) {
            // flush the page stack & return to the map screen
            rWin.push(null, !rWin.animate)
        } else {
            // just pop itself from the page stack and return to the
            // previous screen (like this the map layer page can be
            // used as a handy map layer selection dialog when switching
            // back to the map is not needed)
            rWin.pageStack.pop(undefined, !rWin.animate)
        }
    }
}