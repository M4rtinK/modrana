// Tile.qml

import QtQuick 2.0
import UC 1.0


Item {
    id : tile
    property int tileSize : 256
    property real tileOpacity : 1.0
    property alias source : img.source
    property bool waiting : false
    property string tileId : ""
    property bool cache : img.cache
    Image {
        property int retryCount : 1
        id: img
        cache : false
        width: tile.tileSize
        height: tile.tileSize
        opacity: tile.tileOpacity
        //synchronous :
        onStatusChanged : {
            //console.log("status changed:" + img.status + " " + img.source + " " + img.sourceSize.width)
            if (img.status == Image.Ready) {
                // check if we got a real image or an info info
                // pixel telling us the tile was not found locally
                // and will be downloaded
                if (img.sourceSize.width == 1) {
                    // info tile, disable caching, clear source and
                    // connect to the tile downloaded signal and wait
                    // for the tile to be downloaded
                    img.cache = false
                    img.source = ""
                }
            }
        }
    }
    Label {
        opacity: 0.7
        anchors.leftMargin: 16
        font.pixelSize : 8
        //font.pixelSize : 16
        elide : Text.ElideRight
        y: 8 + index*16
        //text : tile.ind + "= " +tile.tileX + " " + tile.tileY
        text: tile.tileId + "<br>" + tile.source
        /*
        text: layerName + " "+(img.status == Image.Ready ? "Ready" :
               img.status == Image.Null ? "Not Set" :
               img.status == Image.Error ? "Error" :
               "Loading...")
        */
    }
}

