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
    property string oldTileId : ""
    property int retryCount : 0
    property bool error : false
    property string layerId : ""
    property string layerName : ""
    property bool downloading : false
    property int zoomLevel : 15
    property int tileX : null
    property int tileY : null
    property var mapInstance

    function _getTileId() {
        return mapInstance.name+"/"+tile.layerId+"/"+pinchmap.zoomLevel+"/"+tile.tileX+"/"+tile.tileY
    }

    function _tileStatusCB(tileAvailable) {
        // this function is a callback for an asynchronous tile availability checking call
        // - if tileAvailable is true the tile is locally available,
        //   which means we can can set the source property for the
        //   tile Image element to that it can be loaded
        // - if tileAvailable is false it means that the tile is not
        //   available locally and a tile download request has been
        //   queued (provided automatic tile downloading is enabled)

        if (tileAvailable) {
            // tile is available from local storage - load it at once! :)
            tile.retryCount = 0
            tile.error = false
            tile.downloading = false
            tile.source = tile.mapInstance.tileUrl(tileId)
        } else {
            // tile is queued to be downloaded
            tile.downloading = true
            tile.waiting = false
        }
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
                    mapInstance.isTileAvailable(tile.tileId, tile._tileStatusCB)
                } else {
                    // retry count limit reached, switch to error state
                    tile.downloading = false
                    tile.error = true
                }
            }
        } else {
            // the file has been apparently successfully downloaded,
            // load it
            tile._loadTile()
        }
    }


    function _registerDownloadNotification() {
        // register into a dictionary of tiles waiting for notification
        // about a tile being downloaded
        mapInstance.tilesBeingDownloaded[tile.tileId] = tile
    }

    function _unregisterDownloadNotification() {
        // unregister form the download notification directory
        delete mapInstance.tilesBeingDownloaded[tile.TileId]
    }

    function _loadTile() {
        tile.retryCount = 0
        tile.error = false
        tile.downloading = false
        tile.source = tile.mapInstance.tileUrl(tileId)
    }

    Component.onCompleted : {
        tile.tileId = tile._getTileId()
    }

    Component.onDestruction : {
        // remove tile from tracking
        tile._unregisterDownloadNotification()
    }

    onZoomLevelChanged : {
        // zoom level changed, we need to reload the tile
        tile.downloading = false
        tile.waiting = true
        tile.tileId = tile._getTileId()
    }

    onTileIdChanged : {
        // update tile id in the tracking dict to account for the tile id
        delete mapInstance.tilesBeingDownloaded[tile.oldTileId]
        tile.oldTileId = tile.tileId
        tile._registerDownloadNotification()

        // check if the new tile id is available from local storage
        // (and thus could be loaded at once) or needs to be downloaded
        mapInstance.isTileAvailable(tile.tileId, tile._tileStatusCB)
    }

    onDownloadingChanged : {
        if (tile.downloading) {
            _registerDownloadNotification()
        } else {
            _unregisterDownloadNotification()
        }
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
        text : tile.layerName + " : " + statusString
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

