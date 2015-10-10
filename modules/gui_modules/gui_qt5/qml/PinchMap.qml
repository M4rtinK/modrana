import QtQuick 2.0
import "functions.js" as F
//import "./qtc/PageStatus.js" as PageStatus
import UC 1.0
import "modrana_components"

Rectangle {
    id: pinchmap;
    property string name : ""
    // TODO: give pinchmap element instances unique names
    // if name is not set
    property int zoomLevel: 10;
    property int oldZoomLevel: 99
    property int maxZoomLevel: 18;
    property int minZoomLevel: 2;
    property int minZoomLevelShowGeocaches: 9;
    property int tileScale: 1;
    property int tileSize: 256 * tileScale;
    property int cornerTileX: 32;
    property int cornerTileY: 21;
    property int numTilesX: Math.ceil(width/tileSize) + 2;
    property int numTilesY: Math.ceil(height/tileSize) + 2;
    property int maxTileNo: Math.pow(2, zoomLevel) - 1;
    property bool showTargetIndicator: false
    property double showTargetAtLat: 0;
    property double showTargetAtLon: 0;

    property bool showCurrentPosition: false;
    property bool currentPositionValid: false;
    property double currentPositionLat: 0;
    property double currentPositionLon: 0;
    property double currentPositionAzimuth: 0;
    property double currentPositionError: 0;

    property alias positionIndicator : positionIndicator
    property alias canvas : canvas

    property bool rotationEnabled: false

    property double latitude: 0
    property double longitude: 0
    property var scaleBarLength: getScaleBarLength(latitude);
    
    property alias angle: rot.angle
    property var searchMarkerModel : null

    // use mapnik as the default map layer
    property var layers :  ListModel {
        ListElement {
            layerName : "OSM Mapnik"
            layerId : "mapnik"
            layerOpacity : 1.0
        }
    }

    // indicates that the map layer list has been succesfully initialized
    // and the pinchmap is ready for tile element instantiation
    // - this avoids a strange race condition where sometimes a tile
    //   has been missing some overlays resulting in tiles missing from
    //   the map
    property bool layersReady : false

    // NOTE: for now there is only a single overlay group called "main"
    property string overlayGroupName : "main"
    property int earthRadius: 6371000
    property bool tooManyPoints: true
    property int tileserverPort : 0
    property int status: PageStatus.Active
    signal drag // signals that map-drag has been detected
    signal centerSet // signals that the map has been moved
    signal tileDownloaded(string loadedTileId, int tileError) // signals that a tile has been downloaded
    signal clearPointMenus
    property bool needsUpdate: false

    // if the map is clicked or double clicked the mapClicked and mapDoubleClicked signals
    // are triggered
    //
    // NOTE: screenX and screenY are display coordinates with 0,0 is in upper left corner
    // of the screen; if you want latitude and longitude of the click use the getCoordFromScreenpoint()
    // conversion function
    //
    // Example:
    //
    //    onMapClicked: {
    //        rWin.log.debug("map clicked, screen coordinates:")
    //        rWin.log.debug(screenX + " " + screenY)
    //        rWin.log.debug("geographic coordinates:")
    //        rWin.log.debug(getCoordFromScreenpoint(screenX, screenY))
    //    }

    signal mapClicked(int screenX, int screenY)
    signal mapLongClicked(int screenX, int screenY)
    signal mapPanEnd

    // register the tile-downloaded handler
    // - PyOtherSide stores the handler ids in a hashtable
    //   so even if many pinch map instances register their
    //   handlers it should not slow down Python -> QML message
    //   handling
    Component.onCompleted: {
        rWin.python.setHandler("tileDownloaded:" + pinchmap.name, pinchmap.tileDownloadedCB)
    }

    function tileDownloadedCB(tileId, tileError) {
        // trigger the tile downloaded signal
        // TODO: could the signal by called directly as the callback ?
        //console.log("PINCH MAP: TILE DOWNLOADED: " + tileId)
        tileDownloaded(tileId, tileError)
    }

    transform: Rotation {
        angle: 0
        origin.x: pinchmap.width/2
        origin.y: pinchmap.height/2
        id: rot
    }

    onMaxZoomLevelChanged: {
        if (pinchmap.maxZoomLevel < pinchmap.zoomLevel) {
            setZoomLevel(maxZoomLevel);
        }
    }

    onStatusChanged: {
        if (status == PageStatus.Active && needsUpdate) {
            needsUpdate = false;
            pinchmap.setCenterLatLon(pinchmap.latitude, pinchmap.longitude);
        }
    }

    onWidthChanged: {
        if (status != PageStatus.Active) {
            needsUpdate = true;
        } else {
            pinchmap.setCenterLatLon(pinchmap.latitude, pinchmap.longitude);
        }
    }

    onHeightChanged: {
        if (status != PageStatus.Active) {
            needsUpdate = true;
        } else {
            pinchmap.setCenterLatLon(pinchmap.latitude, pinchmap.longitude);
        }
    }


    function setZoomLevel(z) {
        setZoomLevelPoint(z, pinchmap.width/2, pinchmap.height/2);
    }

    function zoomIn() {
        setZoomLevel(pinchmap.zoomLevel + 1)
    }

    function zoomOut() {
        setZoomLevel(pinchmap.zoomLevel - 1)
    }

    function setZoomLevelPoint(z, x, y) {
        if (z == zoomLevel) {
            return;
        }
        if (z < pinchmap.minZoomLevel || z > pinchmap.maxZoomLevel) {
            return;
        }
        var p = getCoordFromScreenpoint(x, y);
        zoomLevel = z;
        setCoord(p, x, y);
    }

    function pan(dx, dy) {
        map.offsetX -= dx;
        map.offsetY -= dy;
        canvas.x -= dx
        canvas.y -= dy
    }

    function panEnd() {
        var changed = false;
        var threshold = pinchmap.tileSize;

        while (map.offsetX < -threshold) {
            map.offsetX += threshold;
            cornerTileX += 1;
            changed = true;
        }
        while (map.offsetX > threshold) {
            map.offsetX -= threshold;
            cornerTileX -= 1;
            changed = true;
        }

        while (map.offsetY < -threshold) {
            map.offsetY += threshold;
            cornerTileY += 1;
            changed = true;
        }
        while (map.offsetY > threshold) {
            map.offsetY -= threshold;
            cornerTileY -= 1;
            changed = true;
        }
        updateCenter();

        // reset the canvas origin back to the initial
        // values once the pan ends
        canvas.x = -pinchmap.width
        canvas.y = -pinchmap.height
    }

    function updateCenter() {
        var l = getCenter()
        longitude = l[1]
        latitude = l[0]
    }

    function requestUpdate() {
        var start = getCoordFromScreenpoint(0,0)
        var end = getCoordFromScreenpoint(pinchmap.width,pinchmap.height)
        controller.updateGeocaches(start[0], start[1], end[0], end[1])
        console.debug("Update requested.")
    }

    function requestUpdateDetails() {
        var start = getCoordFromScreenpoint(0,0)
        var end = getCoordFromScreenpoint(pinchmap.width,pinchmap.height)
        controller.downloadGeocaches(start[0], start[1], end[0], end[1])
        console.debug("Download requested.")
    }

    function getScaleBarLength(lat) {
        var destlength = width/5;
        var mpp = getMetersPerPixel(lat);
        var guess = mpp * destlength;
        var base = 10 * -Math.floor(Math.log(guess)/Math.log(10) + 0.00001)
        var length_meters = Math.round(guess/base)*base
        var length_pixels = length_meters / mpp
        return [length_pixels, length_meters]
    }

    function setLayer(layerNumber, newLayerId, newLayerName) {
        // set layer ID and name
        rWin.log.debug("pinchmap: setting layer " + layerNumber + " to " + newLayerId + "/" + newLayerName)
        layers.setProperty(layerNumber, "layerId", newLayerId)
        layers.setProperty(layerNumber, "layerName", newLayerName)
        saveLayers()
    }

    function setLayerById(layerNumber, newLayerId) {
        // set layer ID and name
        rWin.log.debug("pinchmap: setting layer by id " + layerNumber + " to " + newLayerId + "/" + newLayerName)
        var newLayerName = rWin.layerDict[newLayerId].label
        layers.setProperty(layerNumber, "layerId", newLayerId)
        layers.setProperty(layerNumber, "layerName", newLayerName)
        saveLayers()
    }

    function setLayerOpacity(layerNumber, opacityValue) {
        rWin.log.debug("pinchmap: setting layer " + layerNumber + " opacity to " + opacityValue)
        layers.setProperty(layerNumber, "layerOpacity", opacityValue)
        saveLayers()
    }

    function appendLayer(layerId, layerName, opacityValue) {
        // Add layer to the end of the layer list.
        // The layer will be the top-most one,
        // overlaying all other layers.
        rWin.log.debug("pinchmap: appending layer " + layerId + ":" + layerName + " with opacity " + opacityValue)
        layers.append({"layerId" : layerId, "layerName" : layerName, "layerOpacity" : opacityValue })
        saveLayers()
    }

    function removeLayer(layerNumber) {
        // remove layer with given number
        // NOTE: the bottom/background layer
        // can't be removed

        // check if the layer number is larger than 0
        // (we don't allow to remove the background layer)
        // and also if it is not out of the model range
        rWin.log.debug("removing layer " + layerNumber)
        if (layerNumber>0 && layerNumber<layers.count) {
            layers.remove(layerNumber)
        } else {
            rWin.log.error("pinch map: can't remove layer - wrong number: " + layerNumber)
        }
        saveLayers()
    }

    function loadLayers() {
        // load current overlay settings from persistent storage
        rWin.log.info("pinchmap: loading overlay settings for " + pinchmap.overlayGroupName)
        rWin.python.call("modrana.gui.modules.mapLayers.getOverlayGroupAsList", [pinchmap.overlayGroupName], function(result){
            // TODO: verify layer is usable
            // TODO: handle load layers on non initial state, the current implementation
            //       kinda expects the layers model having only a single layer and does not
            //       clear it before appending to it to prevent a race condition with tile
            //       loading
            if(result && result.length>0) {
                // don't clear and vut replace instead
                // TODO: handle non default (1 layer) state
                pinchmap.layers.set(0, result[0])
                for (var i=1; i<result.length; i++) {
                    pinchmap.layers.append(result[i]);
                }
            }
            rWin.log.debug("pinchmap: overlay settings for " + pinchmap.overlayGroupName + " loaded")
            pinchmap.layersReady = true
        })
    }

    function saveLayers() {
        // save current overlay settings to persistent storage
        rWin.log.info("pinchmap: saving overlay settings for " + pinchmap.overlayGroupName)
        var list = []
        for (var i=0; i<layers.count; i++) {
            var thisLayer = layers.get(i);
            list[i] = {layerName : thisLayer.layerName, layerId : thisLayer.layerId, layerOpacity : thisLayer.layerOpacity};
        }
        rWin.python.call("modrana.gui.modules.mapLayers.setOverlayGroup", [pinchmap.overlayGroupName, list], function(){})
    }

    function getMetersPerPixel(lat) {
        return Math.cos(lat * Math.PI / 180.0) * 2.0 * Math.PI * earthRadius / (256 * (maxTileNo + 1))
    }

    function deg2rad(deg) {
        return deg * (Math.PI /180.0);
    }

    function deg2num(lat, lon) {
        var rad = deg2rad(lat % 90);
        var n = maxTileNo + 1;
        var xtile = ((lon % 180.0) + 180.0) / 360.0 * n;
        var ytile = (1.0 - Math.log(Math.tan(rad) + (1.0 / Math.cos(rad))) / Math.PI) / 2.0 * n;
        return [xtile, ytile];
    }

    function setLatLon(lat, lon, x, y) {
        var oldCornerTileX = cornerTileX
        var oldCornerTileY = cornerTileY
        var tile = deg2num(lat, lon);
        var cornerTileFloatX = tile[0] + (map.rootX - x) / tileSize // - numTilesX/2.0;
        var cornerTileFloatY = tile[1] + (map.rootY - y) / tileSize // - numTilesY/2.0;
        cornerTileX = Math.floor(cornerTileFloatX);
        cornerTileY = Math.floor(cornerTileFloatY);
        map.offsetX = -(cornerTileFloatX - Math.floor(cornerTileFloatX)) * tileSize;
        map.offsetY = -(cornerTileFloatY - Math.floor(cornerTileFloatY)) * tileSize;
        updateCenter();
    }

    function setCoord(c, x, y) {
        setLatLon(c[0], c[1], x, y);
    }

    function setCenterLatLon(lat, lon) {
        setLatLon(lat, lon, pinchmap.width/2, pinchmap.height/2);
        centerSet();
    }

    function setCenterCoord(c) {
        setCenterLatLon(c[0], c[1]);
        centerSet();
    }

    function getCoordFromScreenpoint(x, y) {
        var realX = - map.rootX - map.offsetX + x;
        var realY = - map.rootY - map.offsetY + y;
        var realTileX = cornerTileX + realX / tileSize;
        var realTileY = cornerTileY + realY / tileSize;
        return num2deg(realTileX, realTileY);
    }

    function getScreenpointFromCoord(lat, lon) {
        var tile = deg2num(lat, lon)
        var realX = (tile[0] - cornerTileX) * tileSize
        var realY = (tile[1] - cornerTileY) * tileSize
        var x = realX + map.rootX + map.offsetX
        var y = realY + map.rootY + map.offsetY
        return [x, y]
    }

    function getMappointFromCoord(lat, lon) {
        var tile = deg2num(lat, lon)
        var realX = (tile[0] - cornerTileX) * tileSize
        var realY = (tile[1] - cornerTileY) * tileSize
        return [realX, realY]
    }

    function getCenter() {
        return getCoordFromScreenpoint(pinchmap.width/2, pinchmap.height/2);
    }

    function sinh(aValue) {
        return (Math.pow(Math.E, aValue)-Math.pow(Math.E, -aValue))/2;
    }

    function num2deg(xtile, ytile) {
        var n = Math.pow(2, zoomLevel);
        var lon_deg = xtile / n * 360.0 - 180;
        var lat_rad = Math.atan(sinh(Math.PI * (1 - 2 * ytile / n)));
        var lat_deg = lat_rad * 180.0 / Math.PI;
        return [lat_deg % 90.0, lon_deg % 180.0];
    }

    function tileUrl(tileId) {
        return "image://python/tile/" + tileId
    }

    PinchArea {
        id: pincharea;
        property double __oldZoom;
        anchors.fill: parent;

        function calcZoomDelta(p) {
            pinchmap.setZoomLevelPoint(Math.round((Math.log(p.scale)/Math.log(2)) + __oldZoom), p.center.x, p.center.y);
            if (rotationEnabled) {
                rot.angle = p.rotation
            }
            pan(Math.round(p.previousCenter.x - p.center.x), Math.round(p.previousCenter.y - p.center.y));
        }

        onPinchStarted: {
            __oldZoom = pinchmap.zoomLevel;
        }

        onPinchUpdated: {
            calcZoomDelta(pinch);
        }

        onPinchFinished: {
            calcZoomDelta(pinch);
        }

        MouseArea {
            id: mousearea;
            property bool __isPanning: false;
            property int __lastX: -1;
            property int __lastY: -1;
            property int __firstX: -1;
            property int __firstY: -1;
            property bool __wasClick: false;
            // take HiDPI into account
            // (bigger pixel density -> bigger chance of detecting a click as a pan by mistake)
            property int maxClickDistance: 100 * rWin.c.style.m

            propagateComposedEvents : true

            anchors.fill : parent;

            onClicked: {
                mapClicked(Math.round(mouse.x), Math.round(mouse.y))
            }

            onDoubleClicked: {
                setZoomLevelPoint(pinchmap.zoomLevel + 1, Math.round(mouse.x), Math.round(mouse.y));
            }

            onPressAndHold: {
                // prevent map panning from triggering long clicks
                if (__wasClick) {
                    mapLongClicked(Math.round(mouse.x), Math.round(mouse.y))
                }
            }

            onWheel:  {
                var zoom_diff = (wheel.angleDelta.y > 0) ? 1 : -1;
                setZoomLevelPoint(pinchmap.zoomLevel + zoom_diff, wheel.x, wheel.y);
            }

            onPressed: {
                __isPanning = true;
                __lastX = Math.round(mouse.x);
                __lastY = Math.round(mouse.y);
                __firstX = Math.round(mouse.x);
                __firstY = Math.round(mouse.y);
                __wasClick = true;
            }

            onReleased: {
                __isPanning = false;
                if (! __wasClick) {
                    panEnd();
                    mapPanEnd();
                }
            }

            onPositionChanged: {
                if (__isPanning) {
                    // as Qt 5 on Sailfish OS for some reasons returns pointer coordinates as
                    // floating point numbers, convert them all to integers first to prevent
                    // precision loss
                    var dx = Math.round(mouse.x) - __lastX;
                    var dy = Math.round(mouse.y) - __lastY;
                    pan(-dx, -dy);
                    __lastX = Math.round(mouse.x);
                    __lastY = Math.round(mouse.y);
                    /*
                    once the pan threshold is reached, additional checking is unnecessary
                    for the press duration as nothing sets __wasClick back to true
                    */
                    if (__wasClick && Math.pow(Math.round(mouse.x) - __firstX, 2) + Math.pow(Math.round(mouse.y) - __firstY, 2) > maxClickDistance) {
                        __wasClick = false;
                        pinchmap.drag() // send the drag-detected signal

                    }
                }
            }

            onCanceled: {
                __isPanning = false;
            }
        }
    }

    Grid {
        id: map;
        columns: numTilesX;
        width: numTilesX * tileSize;
        height: numTilesY * tileSize;
        property int rootX: -(width - parent.width)/2;
        property int rootY: -(height - parent.height)/2;
        property int offsetX: 0;
        property int offsetY: 0;
        x: rootX + offsetX;
        y: rootY + offsetY;

        Repeater {
            id: tiles
            model: pinchmap.layersReady ? pinchmap.numTilesX * pinchmap.numTilesY : null
            Rectangle {
                id: tile
                property alias source: imgs.source;
                property int tileX: cornerTileX + (index % numTilesX)
                property int tileY: cornerTileY + Math.floor(index / numTilesX)
                property int ind : index

                width: tileSize;
                height: tileSize;
                color: "#c0c0c0";

               Repeater {
                    id: imgs
                    //property string source: tileUrl(model[0].layerId, tileX, tileY)
                    property string source
                    model: pinchmap.layersReady ? pinchmap.layers : null
                    Tile {
                        id : tile
                        tileSize : tileSize
                        tileOpacity : layerOpacity
                        mapInstance : pinchmap
                        // TODO: move to function
                        tileId: pinchmap.name+"/"+layerId+"/"+pinchmap.zoomLevel+"/"+tileX+"/"+tileY
                        // if tile id changes means that the panning reached a threshold that cased
                        // a top-level X/Y coordinate switch
                        // -> this basically means that all columns or rows switch coordinates and
                        //    one row/column has new coordinates while one column/rwo coordinate
                        //    set is discarded
                        // -> like this, we don't have to instantiate and discard a bazillion of
                        //    tile elements, but instantiate them once and then shuffle them around
                        // -> tiles are instantiated and removed only if either viewport size or layer
                        //    count changes
                        onTileIdChanged: {
                            // so we are now a different tile :)
                            // therefore we need to all the asynchronous tile loading properties back
                            // to the default state and try to load the tile, if it is in the cache
                            // it will be loaded at once or the asynchronous loading process will start
                            // * note that any "old" asynchronous loading process still runs and the
                            //   "new" tile that got the "old" coordinates will get the tile-downloaded
                            //   notification, which is actually what we want :)
                            tile.layerName = layerId
                            tile.error = false
                            tile.cache = true
                            tile.retryCount = 0
                            tile.downloading = false
                            tile.source = tileUrl(tileId)
                        }
                    }
                }
            }

        }

        SearchMarkers {
            id: markers
            model : pinchmap.searchMarkerModel
            mapInstance : pinchmap
        }

        PointMenuMarkers {
            id: pointMenuMarkers
            mapInstance : pinchmap
            Connections {
                target : pinchmap
                onMapLongClicked : {
                    var ll = pinchmap.getCoordFromScreenpoint(screenX, screenY)
                    // replace the previously shown menu (if any)
                    pointMenuMarkers.clear()
                    pointMenuMarkers.appendMarker(ll[0], ll[1], "", true)
                }
                onClearPointMenus : {
                    pointMenuMarkers.clear()
                }
            }
        }
    }

    Canvas {
        id: canvas
        visible: true

        // Expand the canvas outside of the visible map area
        // so that the route is not cut-off when the map is
        // being panned.
        width : pinchmap.width*3
        height : pinchmap.height*3
        x : - pinchmap.width
        y : - pinchmap.height

        onVisibleChanged : {
            if (canvas.visible) {
                canvas.requestPaint()
            }
        }

        Connections {
            target: canvas.visible ? pinchmap : null
            onCenterSet: {
                canvas.requestPaint()
            }
            onZoomLevelChanged: {
                canvas.requestPaint()
            }
            onMapPanEnd: {
                canvas.requestPaint()
            }
        }
    }

    Image {
        id: targetIndicator
        source: "image://python/icon/"+ rWin.theme.id +"/target-indicator-cross.png"
        property var t: getMappointFromCoord(showTargetAtLat, showTargetAtLon)
        x: map.x + t[0] - width/2
        y: map.y + t[1] - height/2

        visible: showTargetIndicator
        transform: Rotation {
            id: rotationTarget
            origin.x: targetIndicator.width/2
            origin.y: targetIndicator.height/2
        }
    }

    Rectangle {
        id: positionErrorIndicator
        visible: false
        width: currentPositionError * (1/getMetersPerPixel(currentPositionLat)) * 2
        height: width
        color: "#300000ff"
        border.width: 2
        border.color: "#800000ff"
        x: map.x + positionIndicator.t[0] - width/2
        y: map.y + positionIndicator.t[1] - height/2
        radius: width/2
    }

    Image {
        id: positionIndicator
        source: currentPositionValid ?
                "image://python/icon/"+ rWin.theme.id +"/position-indicator.png" :
                "image://python/icon/"+ rWin.theme.id +"/position-indicator-red.png"
        property var t: getMappointFromCoord(currentPositionLat, currentPositionLon)
        x: map.x + t[0] - width/2
        y: map.y + t[1] - height + positionIndicator.width/2
        smooth: true
        visible: showCurrentPosition
        transform: Rotation {
            origin.x: positionIndicator.width/2
            origin.y: positionIndicator.height - positionIndicator.width/2
            angle: currentPositionAzimuth
        }
    }

    Rectangle {
        id: scaleBar
        anchors.right: parent.right
        anchors.rightMargin: rWin.c.style.main.spacingBig
        anchors.topMargin: rWin.c.style.main.spacingBig
        anchors.top: parent.top
        color: "black"
        border.width: rWin.c.style.map.scaleBar.border
        border.color: "white"
        smooth: false
        height: rWin.c.style.map.scaleBar.height
        width: scaleBarLength[0]
    }

    Text {
        text: F.formatDistance(scaleBarLength[1], pinchmap.tileScale)
        anchors.horizontalCenter: scaleBar.horizontalCenter
        anchors.top: scaleBar.bottom
        anchors.topMargin: rWin.c.style.main.spacing
        style: Text.Outline
        styleColor: "white"
        font.pixelSize: rWin.c.style.map.scaleBar.fontSize
    }
}