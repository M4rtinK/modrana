import QtQuick 2.0
import UC 1.0
import "modrana_components"

MapLayerSelector {
    onLayerSelected : {
        rWin.set("layer", layerId)
        rWin.mapPage.getMap().setLayerById(0, layerId)
        rWin.push(null, !rWin.animate)
    }
}