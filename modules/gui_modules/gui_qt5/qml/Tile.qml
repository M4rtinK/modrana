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
    // normal status text
    Label {
        opacity: 0.7
        visible : !rWin.tileDebug && (img.status != Image.Ready)
        anchors.leftMargin: 16
        font.pixelSize : 16
        //font.pixelSize : 16
        elide : Text.ElideRight
        y: 8 + index*16

        text : layerName + " " + "Downloading..."

        /*
        text: layerName + " "+(img.source == "" ? "Downloading" :
               img.status == Image.Null ? "Not Set" :
               img.status == Image.Error ? "Error" :
               "Loading...")
        */
    }
    // debug status text
    Label {
        opacity: 1.0
        color : "black"
        visible: rWin.tileDebug
        anchors.leftMargin: 16
        font.pixelSize : 16
        //font.pixelSize : 16
        elide : Text.ElideRight
        y: 8 + index*16
        text: tile.tileId + "<br>source set: " + (tile.source != '') + "<br>cache:" + tile.cache
    }
}

