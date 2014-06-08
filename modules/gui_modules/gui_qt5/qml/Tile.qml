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
    property alias cache : img.cache
    property int retryCount : 0
    property bool error : false
    property string layerName : ""
    property bool downloading : false

    Image {
        id: img
        cache : true
        width: tile.tileSize
        height: tile.tileSize
        opacity: tile.downloading ? 0.0 : tile.tileOpacity
        asynchronous : true
        onStatusChanged : {
            //console.log("status changed: " + tile.tileId + " " +  img.status + " " +
            //            img.source + " " + img.sourceSize.width)
            if (img.status == Image.Ready) {
                // check if we got a real image or an info info
                // pixel telling us the tile was not found locally
                // and will be downloaded
                if (img.sourceSize.width == 1) {
                    // info tile, disable caching, clear source,
                    // connect to the tile downloaded signal,
                    // issue a tile download request and then wait
                    // for the tile to be downloaded
                    img.cache = false
                    if (!tile.downloading) {
                        tile.downloading = true
                        rWin.python.call("modrana.gui.addTileDownloadRequest", [tile.tileId], function(){})
                    }
                } else {
                    tile.downloading = false
                }
            }
        }
    }
    // normal status text
    Label {
        opacity: 0.7
        visible : !rWin.tileDebug && tile.downloading
        anchors.leftMargin: 16
        font.pixelSize : 16
        elide : Text.ElideMiddle
        y: 8 + index*16
        width : tile.tileSize - 16
        // TODO: use a constant ?
        property string retryString : tile.retryCount ? "Downloading... (" + tile.retryCount + "/5)" : "Downloading..."
        property string statusString : tile.error == true ? "dl failed" : retryString
        text : tile.layerName + " : " + statusString
    }
    // debug status text
    Label {
        opacity: 1.0
        color : "black"
        visible: rWin.tileDebug
        anchors.leftMargin: 16
        font.pixelSize : 16
        elide : Text.ElideRight
        width : tile.tileSize - 16
        y: 8 + index*16
        text: tile.tileId + "<br>source set: " + (tile.source != '') +
              "<br>cache:" + tile.cache + "<br>error:" + tile.error +
              "<br>retryCount: " + tile.retryCount +
              "<br>download: " + tile.downloading
    }
}

