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
    property var mapInstance : null

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
    // connection to the map instance for for tile-downloaded notifications
    Connections {
        target: tile.downloading ? tile.mapInstance : null
        onTileDownloaded: {
            // is this us ?
            if (tile.downloading && loadedTileId == tile.tileId) {
                //console.log("THIS TILE " + tile.tileId + " error: " + tileError + " " + tile.source)
                if (tileError > 0) {
                    // something went wrong
                    if (tileError == 1) {
                        // fatal error
                        tile.error = true
                    } else {
                        if (tileError > 1) {
                            // non fatal error, increment retry count
                            tile.retryCount = tile.retryCount + 1
                        }
                        // TODO: use a constant ?
                        if (tile.retryCount <= 5) {
                            // we are still within the retry count limit,
                            // so trigger another download request by trying
                            // to load the tile
                            tile.cache = false
                            tile.source = tileUrl(tileId)
                        } else {
                            // retry count limit reached, switch to error state
                            tile.error = true
                        }
                    }
                } else {
                    // everything appears fine, load the tile
                    tile.retryCount = 0
                    tile.error = false
                    tile.cache = true
                    tile.source = tileUrl(tileId)
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

