// Tile.qml

import QtQuick 2.0
import UC 1.0


Item {
    id : tile
    property int tileSize : 256
    property real tileOpacity : 1.0
    property alias source : img.source
    Image {
        property int retryCount : 1
        id: img
        width: tile.tileSize
        height: tile.tileSize
        opacity: tile.tileOpacity
        asynchronous : true
    }
    Label {
        opacity: 0.7
        anchors.leftMargin: 16
        font.pixelSize : 16
        elide : Text.ElideRight
        y: 8 + index*16
        //text : tile.ind + "= " +tile.tileX + " " + tile.tileY
        /*
        text: layerName + " "+(img.status == Image.Ready ? "Ready" :
               img.status == Image.Null ? "Not Set" :
               img.status == Image.Error ? "Error" :
               "Loading...")
        */
    }
}

