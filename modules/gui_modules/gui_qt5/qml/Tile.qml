// Tile.qml

import QtQuick 2.0
import UC 1.0

Item {
    id : tile
    property int tileSize : 256
    property real tileOpacity : 1.0
    property alias source : img.source
    property var tileXY : ""
    property string tileId : mapInstance.name+"/"+tile.mapLayerId+"/"+pinchmap.zoomLevel+"/"+tileXY
    property string oldTileId : ""
    property int retryCount : 0
    property bool error : false
    property string mapLayerId : ""
    property string mapLayerName : ""
    property bool downloading : false
    property bool available : false
    property int zoomLevel : 15
    property var mapInstance

    onAvailableChanged : {
        // - if available is true the tile is locally available,
        //   which means we can can set the source property for the
        //   tile Image element to that it can be loaded and displayed
        // - if available is false it means that the tile is not
        //   available locally and a tile download request has been
        //   queued (provided automatic tile downloading is enabled)
        // - TODO: sensibly show to the user if automatic tile
        //   download is disabled

        if (tile.available) {
            // tile is available from local storage - load it at once! :)
            tile.retryCount = 0
            tile.error = false
            tile.downloading = false
            tile.source = tile.mapInstance.tileUrl(tileId)
        }
    }

    function _clearTile() {
        // clear the tile to a "no tile loaded" state
        // - set image source to ""
        // - set available & downloading to false
        // - clear download errors
        tile.retryCount = 0
        tile.error = false
        tile.downloading = false
        tile.available = false
        tile.source = ""
    }

    function tileDownloaded(result) {
        // result[0] = success true/false
        // result[1] = fatal error true/false
        if (!result[0]) {
            // something went wrong
            if (result[1]) {
                // fatal error
                tile.downloading = false
                tile.error = true
            } else {
                // non fatal error, increment retry count
                tile.retryCount++
                // TODO: use a constant ?
                if (tile.retryCount <= 5) {
                    // we are still within the retry count limit,
                    // so trigger another download request
                    mapInstance.isTileAvailable(tile.tileId)
                } else {
                    // retry count limit reached, switch to error state
                    tile.downloading = false
                    tile.error = true
                }
            }
        } else {
            // the file has been apparently successfully downloaded
            // and is available to be loaded and displayed
            tile.available = true
        }
    }

    Component.onDestruction : {
        // remove tile from tracking
        delete mapInstance.currentTiles[tile.tileId]
    }

    onZoomLevelChanged : {
        // zoom level changed, we need to reload the tile
        tile._clearTile()
    }

    onTileIdChanged : {
        // update tile id in the tracking dict to account for the tile id
        if (mapInstance.currentTiles[tile.oldTileId]) {
            delete mapInstance.currentTiles[tile.oldTileId]
        }
        tile.oldTileId = tile.tileId
        // register the file with new tile ID
        mapInstance.currentTiles[tile.tileId] = tile
        tile._clearTile()
        // check if the new tile id is available from local storage
        // (and thus could be loaded at once) or needs to be downloaded
        mapInstance.isTileAvailable(tile.tileId)
    }

    Image {
        id: img
        width: tile.tileSize
        height: tile.tileSize
        opacity: tile.downloading ? 0.0 : tile.tileOpacity
        asynchronous : true
    }

    // normal status text
    Label {
        opacity: 0.7
        visible : tile.downloading
        anchors.leftMargin: 16
        font.pixelSize : 16
        elide : Text.ElideMiddle
        y: 8 + index*16
        width : tile.tileSize - 16
        // TODO: use a constant ?
        property string retryString : tile.retryCount ? "Downloading... (" + tile.retryCount + "/5)" : "Downloading..."
        property string statusString : tile.error == true ? "dl failed" : retryString
        text : tile.mapLayerName + " : " + statusString
    }
    // debug status text
    /*
    Label {
        opacity: 1.0
        color : "black"
        anchors.leftMargin: 16
        font.pixelSize : 16
        elide : Text.ElideRight
        width : tile.tileSize - 16
        y: 8 + index*16
        text: tile.tileId + "<br>source set: " + (tile.source != '') +
              "<br>cache:" + tile.cache + "<br>error:" + tile.error +
              "<br>retryCount: " + tile.retryCount +
              "<br>download: " + tile.downloading
    }*/
}

