import QtQuick 2.0
import UC 1.0
import "../functions.js" as F
import "../map_components"
import "../modrana_components"

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
    property int numTilesX: Math.ceil(width/tileSize) + 1
    property int numTilesY: Math.ceil(height/tileSize) + 1
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

    // scale bar
    property real scaleBarTopOffset : 0
    property var scaleBarLength: getScaleBarLength(latitude);
    
    property alias angle: rot.angle

    // search
    property var searchMarkerModel : ListModel {}

    function addSearchMarker(point) {
        // add a search marker to the map
        searchMarkerModel.append(point)
    }

    function clearSearchMarkers() {
        // clear all search markers from the map
        searchMarkerModel.clear()
    }

    // POI
    property var poiMarkerModel : ListModel {}
    signal poiClicked(var point)

    function addPOIMarker(point) {
        // add a POI marker on the map

        // first check if we already have the POI in the model
        var alreadyAdded = false
        for (var i=0; i<poiMarkerModel.count; i++) {
            if (poiMarkerModel.get(i).db_id == point.db_id) {
                alreadyAdded = true
                break
            }
        }
        if (!alreadyAdded) {
            rWin.log.debug("adding POI to map list model: " + point.name)
            // We need to create a new point instance like this,
            // or else the original point instance might get garbage collected,
            // causing issues later.
            poiMarkerModel.append({
                "name" : point.name,
                "description" : point.description,
                "latitude" : point.latitude,
                "longitude" : point.longitude,
                "elevation" : point.elevation,
                "highlight" : false,
                "mDistance" : 0,
                "db_id" : point.db_id,
                "category_id" : point.category_id
            })
        }
    }

    function removePOIMarkerById(point) {
        // remove a visible POI marked by its id
        // (nothing happens if no such POI is visible)

        // check if we have the POI in the model
        var modelIndex = null
        for (var i=0; i<poiMarkerModel.count; i++) {

            if (poiMarkerModel.get(i).db_id == point.db_id) {
                modelIndex = i
                break
            }
        }
        // if matching marker was found, delete it from the model
        if (modelIndex != null) {
            rWin.log.info("removing visible POI marker (db id " + point.db_id + ")")
            poiMarkerModel.remove(modelIndex)
        }
    }

    function clearPOIMarkers() {
        // clear all POI markers displayed on the map
        poiMarkerModel.clear()
    }

    // a dictionary of tile coordinates that should be current visible
    property var shouldBeOnScreen : {"foo" : true}


    property int mapButtonSize : Math.min(width/8.0, height/8.0)
    property int mapButtonSpacing : mapButtonSize / 4

    // tile status check request staging
    property var tileRequests : []
    property bool tileRequestTimerPause : false
    // Due to the many individual tile status queries triggering a PyOtherSide crash &
    // for general efficiency reasons (it should be more efficient to group the queries
    // and to send them & answer them at once) we group the queries to a batch that is then
    // sent at once.
    //
    // This is achieved by a timer that is reset every time a new request is added,
    // which effectively batches all requests coming inside the given timer interval
    // (currently 10 ms) & sends them once no request comes for 10 ms.
    // NOTE: This could theoretically fail horribly if a request came *at least*
    //       once every 10 seconds, so requests would continuously accumulate
    //       and would never be sent. This is however almost guaranteed to never
    //       happen due to the modRana screen update logic.

    property color backgroundColor : "#cccccc"
    property color gridColor : "#d9d9d9"

    Rectangle {
        id : backgroundColorRectangle
        color : pinchmap.backgroundColor
        anchors.fill : parent

    }

    Timer {
        id : tileRequestTimer
        interval: 10
        running: false
        repeat: false
        property bool paused : false
        onTriggered : {
            var requestBatch = pinchmap.tileRequests.slice()
            pinchmap.tileRequests = []
            rWin.python.call("modrana.gui.areTilesAvailable", [requestBatch], tilesAvailabilityCB)
            running = false
        }
    }

    property bool modelSet : false

    // For some reason on Sailfish OS the tiles repeater
    // won't work correctly if the tilesModel is assigned
    // or bound by a property binding to the repeater model
    // property, but it works correctly if the model is set
    // with a slight delay after the initial updateTilesModel() runs.
    // And of course it all works just fine on desktop...

    Timer {
        id : wtfTimer  // I think this is a fitting name for this timer
        interval : 10
        running : false
        repeat : false
        onTriggered : {
            rWin.log.debug("setting tiles model")
            map.tilesRepeater.model = pinchmap.tilesModel
            modelSet = true
        }
    }


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

    property var tilesModel : ListModel {}
    property var currentTiles : new Object()

    property bool tilesModelUpdateRunning : false
    property bool anotherTilesModelUpdateNeeded : false

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
        // instantiate the nested backing data model for tiles
        updateTilesModel()
    }

    WorkerScript {
        id : updateTilesModelWorker
        property bool workerInitialized: false
        property var replayMessages : []
        source : "../workers/update_tiles_model.js"
        onMessage: {
            // update the shouldBeOnScreen dict with data based
            // on the tiles model update
            pinchmap.shouldBeOnScreen = messageObject.shouldBeOnScreen
            // re-enable the tile requests timer
            tileRequestTimerPause = false
            tileRequestTimer.start()
            // handle the unfortunate but required due to yet another bug
            // in the Sailfish OS version os Qt5 delayed assignment of
            // the tilesModel as a model for the tiles repeater.
            if (!modelSet) {
                wtfTimer.restart()
            }
            tilesModelUpdateRunning = false
            if (anotherTilesModelUpdateNeeded) {
                // do the additional tiles model update
                // just in case that the screen & map geometry
                // changed since this asynchronous tile model
                // update has been triggered
                pinchmap.updateTilesModel()
                anotherTilesModelUpdateNeeded = false
            }
        }

        Component.onCompleted: {
            rWin.log.debug("Tile model worker script has been initialized.")
            updateTilesModelWorker.workerInitialized = true
            // Try to replay a messages that might have been
            // stored due to worker script not being initialized yet.
            // Ignoring such messages might result in no map tiles being shown.
            if (replayMessages != []) {
                rWin.log.debug("Replaying deferred messages to tile model worker script.")
                for (var i=0; i<replayMessages.length; i++) {
                    rWin.log.debug("Replaying message nr.: " + (i+1))
                    updateTilesModelWorker.sendMessage(replayMessages[i])
                }
                replayMessages = []
            }
        }
    }

    function updateTilesModel() {
        // trigger asynchronous tile model update
        if (tilesModelUpdateRunning) {
            // skip duplicate update requests but remember at least
            // one has been requested and run one mor asynchronous tile model
            // update once the current one finishes
            anotherTilesModelUpdateNeeded = true
        } else {
            tilesModelUpdateRunning = true
            // turn off the tile requests timer until the tiles model update is done
            tileRequestTimer.stop()
            tileRequestTimerPause = true
            // start the asynchronous tile model update
            if (updateTilesModelWorker.workerInitialized) {
                updateTilesModelWorker.sendMessage(
                    {
                        cornerX : pinchmap.cornerTileX,
                        cornerY : pinchmap.cornerTileY,
                        tilesX : pinchmap.numTilesX,
                        tilesY : pinchmap.numTilesY,
                        tilesModel : pinchmap.tilesModel,
                        shouldBeOnScreen : pinchmap.shouldBeOnScreen
                    }
                )
            } else {
                rWin.log.debug("Worker script not yet initialized.")
                updateTilesModelWorker.replayMessages.push({
                    cornerX : pinchmap.cornerTileX,
                    cornerY : pinchmap.cornerTileY,
                    tilesX : pinchmap.numTilesX,
                    tilesY : pinchmap.numTilesY,
                    tilesModel : pinchmap.tilesModel,
                    shouldBeOnScreen : pinchmap.shouldBeOnScreen
                })
            }
        }
    }

    function tilesAvailabilityCB(tileAvailabilityDict) {
        for (var tileId in tileAvailabilityDict) {
            var tileAvailable = tileAvailabilityDict[tileId]
            var tile = pinchmap.currentTiles[tileId]
            if (tile) {
                tile.available = tileAvailable
            }
        }
    }

    function tileDownloadedCB(tileId, resoundingSuccess, fatalError) {
        // notify tile delegates waiting for tile data to be available
        var tile = pinchmap.currentTiles[tileId]
        if (tile) {
            tile.tileDownloaded([resoundingSuccess, fatalError])
        }
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
        // update canvas offset when pinchmap width changes
        canvas.x = -pinchmap.width
        if (status != PageStatus.Active) {
            needsUpdate = true;
        } else {
            pinchmap.setCenterLatLon(pinchmap.latitude, pinchmap.longitude);
        }
    }

    onHeightChanged: {
        // update offset position when pinchmap height changes
        canvas.y = -pinchmap.height
        if (status != PageStatus.Active) {
            needsUpdate = true;
        } else {
            pinchmap.setCenterLatLon(pinchmap.latitude, pinchmap.longitude);
        }
    }

    onCornerTileXChanged: {
        updateTilesModel()
    }

    onCornerTileYChanged: {
        updateTilesModel()
    }

    onMapClicked: {
        clearPointMenus()
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

    function panUpdate() {
        var threshold = pinchmap.tileSize;
        if (map.offsetX < 0) {
            var multiplier = Math.floor(Math.abs(map.offsetX)/threshold)
            map.offsetX += threshold * multiplier;
            pinchmap.cornerTileX += multiplier;
        }
        else if (map.offsetX > 0) {
            var multiplier = Math.floor(map.offsetX/threshold) + 1
            map.offsetX -= threshold * multiplier;
            pinchmap.cornerTileX -= multiplier;
        }

        if (map.offsetY < 0) {
            var multiplier = Math.floor(Math.abs(map.offsetY)/threshold)
            map.offsetY += threshold * multiplier;
            pinchmap.cornerTileY += multiplier;
        }
        else if (map.offsetY > 0) {
            var multiplier = Math.floor(map.offsetY/threshold) + 1
            map.offsetY -= threshold * multiplier;
            pinchmap.cornerTileY -= multiplier;
        }
        updateCenter();
    }

    function panEnd() {
        panUpdate()
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
        var newLayerName = rWin.layerDict[newLayerId].label
        rWin.log.debug("pinchmap: setting layer by id " + layerNumber + " to " + newLayerId + "/" + newLayerName)
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

    function deg2num(lat, lon, z) {
        // lat/lon to tile x/y
        var rad = deg2rad(lat % 90);
        var n = Math.pow(2, z);
        var xtile = ((lon % 180.0) + 180.0) / 360.0 * n;
        var ytile = (1.0 - Math.log(Math.tan(rad) + (1.0 / Math.cos(rad))) / Math.PI) / 2.0 * n;
        return [xtile, ytile];
    }

    function setLatLon(lat, lon, x, y) {
        var tile = deg2num(lat, lon, zoomLevel);
        var cornerTileFloatX = tile[0] - x / tileSize
        var cornerTileFloatY = tile[1] - y / tileSize
        cornerTileX = Math.floor(cornerTileFloatX);
        cornerTileY = Math.floor(cornerTileFloatY);
        map.offsetX = -(cornerTileFloatX - Math.floor(cornerTileFloatX)) * tileSize;
        map.offsetY = -(cornerTileFloatY - Math.floor(cornerTileFloatY)) * tileSize;
        // Check if x & y point to map center, if they do then
        // set pinchmap center latitude & longitude directly to lat & lon.
        // Otherwise map center coordinates would move at random due to floating
        // point error when setCenterLatLon calls setLatLon many times
        // in a row, such as when the user (or a window manager animation)
        // seamlessly changes window size.
        var isCenter = (x == pinchmap.width/2) && (y == pinchmap.height/2)
        if (isCenter) {
            pinchmap.latitude = lat
            pinchmap.longitude = lon
        } else {
            updateCenter();
        }
        updateTilesModel()
    }

    function setCoord(c, x, y) {
        setLatLon(c[0], c[1], x, y);
    }

    function setCenterLatLon(lat, lon) {
        setLatLon(lat, lon, pinchmap.width/2, pinchmap.height/2)
        centerSet()
    }

    function setCenterCoord(c) {
        setCenterLatLon(c[0], c[1]);
        centerSet();
    }

/*  longer & easier to read version

    function getCoordFromScreenpoint(x, y) {
        var realX = x - map.offsetX
        var realY = y - map.offsetY
        var realTileX = cornerTileX + realX / tileSize;
        var realTileY = cornerTileY + realY / tileSize;
        return num2deg(realTileX, realTileY, zoomLevel);
    }
*/

    // shorter version without intermediate variables
    function getCoordFromScreenpoint(x, y) {
        return num2deg(cornerTileX + (x - map.offsetX) / tileSize,
                       cornerTileY + (y - map.offsetY) / tileSize,
                       zoomLevel)
    }

    // shorter version without intermediate variables @ zoom level
    function getCoordFromScreenpointAtZ(x, y, z) {
        return num2deg(cornerTileX + (x - map.offsetX) / tileSize,
                       cornerTileY + (y - map.offsetY) / tileSize,
                       z)
    }

    // basically easier to discover equivalent to deg2num
    function getMappointFromCoord(lat, lon) {
        return deg2num(lat, lon, zoomLevel)
    }

     function getMappointFromCoordAtZ(lat, lon, z) {
        return deg2num(lat, lon, z)
    }


/*  longer & easier to read version

    function getScreenpointFromCoord(lat, lon) {
        var tile = deg2num(lat, lon, zoomLevel)
        var realX = ((tile[0] - cornerTileX) * tileSize) + map.offsetX
        var realY = ((tile[1] - cornerTileY) * tileSize) + map.offsetY
        return [realX, realY]
    }
*/

    // shorter version with less intermediate variables
    function getScreenpointFromCoord(lat, lon) {
        var tile = deg2num(lat, lon, zoomLevel)
        return [((tile[0] - cornerTileX) * tileSize) + map.offsetX,
                ((tile[1] - cornerTileY) * tileSize) + map.offsetY]
    }

    // short version with ability to specify zoomlevel
    function getScreenpointFromCoordAtZ(lat, lon, z) {
        var tile = deg2num(lat, lon, z)
        return [((tile[0] - cornerTileX) * tileSize) + map.offsetX,
                ((tile[1] - cornerTileY) * tileSize) + map.offsetY]
    }

    // The correction is needed when we need to convert map point coordinates
    // for some zoomlevel to screen coordinates for the current zoom level.
    // It's basically corner tile XY & zoom difference compensation.
    // The conversion could of course be done in the map point -> screen point function,
    // but the general idea is that a lot of points will be converted at once at the same zl
    // (during route drawing, etc.), meaning that the correction values will be the same
    // for the whole batch. So we just pre-compute the correction and then use it
    // for the whole batch of conversions, saving use some computation and especially
    // the upper left corner tile lookup, which would kinda ruin the whole concept
    // of using map coordinates when drawing the tiles.
    function getMappointCorrection(z) {
        var cornerLL = getCoordFromScreenpoint(0, 0)
        var cornerXY = getMappointFromCoordAtZ(cornerLL[0], cornerLL[1], z)
        var zCorrection = Math.pow(2, (zoomLevel-z))
        return [cornerXY[0], cornerXY[1], zCorrection]
    }

    // Get screen point for the given mappoint & correction.
    // The expected use case is for batch conversion of precomputed map coordinates
    // at some zoom level to screen coordinates for current viewport and zoom level.
    // In such case the corner tile xy & zoom correction stay the same, so we use
    // precomputed values via the correction array.
    function getScreenpointFromMappointCorrected(x, y, correction) {
        return [((x - correction[0]) * tileSize) * correction[2],
                ((y - correction[1]) * tileSize) * correction[2]]
    }

    function getCenter() {
        return getCoordFromScreenpoint(pinchmap.width/2, pinchmap.height/2);
    }

    function sinh(aValue) {
        return (Math.pow(Math.E, aValue)-Math.pow(Math.E, -aValue))/2;
    }

    function num2deg(xtile, ytile, z) {
        var n = Math.pow(2, z);
        var lon_deg = xtile / n * 360.0 - 180;
        var lat_rad = Math.atan(sinh(Math.PI * (1 - 2 * ytile / n)));
        var lat_deg = lat_rad * 180.0 / Math.PI;
        return [lat_deg % 90.0, lon_deg % 180.0];
    }

    function tileUrl(tileId) {
        return "image://python/tile/" + tileId
    }

    function isTileAvailable(tileId, callback) {
        // check if the tile is available from local storage
        // TODO: make this Python independent
        pinchmap.tileRequests.push(tileId)
        // In some cases where a lot of tiles are checked at once
        // (screen panning or zooming, etc.) we want to batch these
        // check requests as effectively as possible, so we "pause"
        // the timer and "unpause" it once done.
        // So no need to bother the timer until it is unpaused.
        if (!tileRequestTimerPause) {
            tileRequestTimer.restart()
        }
    }

    function downloadTile(tileId) {
        // download the tile
        // TODO: make this Python independent
        rWin.python.call("modrana.gui.addTileDownloadRequest", [tileId], function(){})
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
                // prevent map panning from triggering clicks
                if (__wasClick) {
                    mapClicked(Math.round(mouse.x), Math.round(mouse.y))
                }
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

                    // a new tile row/column has become visible - trigger an
                    // asynchronous tile model update
                    if (map.offsetX > 0 || map.offsetX < -pinchmap.tileSize || map.offsetY > 0 || map.offsetY < -pinchmap.tileSize) {
                        panUpdate()
                    }
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

    Item {
        id: map;
        width: numTilesX * tileSize;
        height: numTilesY * tileSize;
        property int offsetX: 0;
        property int offsetY: 0;

        property alias tilesRepeater : tilesX
        x: 0
        y: 0
        Repeater {
            id: tilesX

            Rectangle {
                id: tile

                // tileID is a "<map x>/<map y>" string
                property string tileID : ""
                // Basically alias for the tile_coords field from the model
                // so that we can bind to it & react changes.
                property var tileCoords : tile_coords
                // current map coordinates of the tile (upper left corner)
                property int tileX: 0
                property int tileY: 0

                onTileCoordsChanged : {
                    // The idea is simple - we need to first change the tileID before changing
                    // the tile coordinates, otherwise there will be intermittent artifacts
                    // visible on the map when a tile is recycled in the tile model.
                    //
                    // The tileID change switches the tile to the no-image state (and starts tile
                    // image lookup), effectively blanking the tile. Only after this is done we can update the
                    // screen coordinates of the tile, to avoid artifacts.

                    // so first step - update tileID
                    tileID = tileCoords.id
                    // second step - trigger screen coordinate update
                    tileX = tileCoords.x
                    tileY = tileCoords.y
                }

                // screen coordinates of the tile (upper left corner)
                x : ((tileX - pinchmap.cornerTileX) * tile.width) + map.offsetX
                y : ((tileY - pinchmap.cornerTileY) * tile.height) + map.offsetY

                property int ind : index

                width: pinchmap.tileSize;
                height: pinchmap.tileSize;
                border.width : 1
                //border.color : "#e5e5e5"
                border.color : pinchmap.gridColor
                color : pinchmap.backgroundColor
                /*
                Text {
                    anchors.horizontalCenter : parent.horizontalCenter
                    anchors.verticalCenter : parent.verticalCenter
                    text : tile_coords.x + "/" + tile_coords.y
                    font.pixelSize : 24
                }
                */

                Repeater {
                    id: tileRepeater
                    model : pinchmap.layers
                    Tile {
                        id : tileImage
                        tileSize : pinchmap.tileSize
                        tileOpacity : layerOpacity
                        zoomLevel : pinchmap.zoomLevel
                        mapInstance : pinchmap
                        tileXY : tileID
                        mapLayerId : layerId
                        mapLayerName : layerName
                    }
                }
            }
        }
        POIMarkers {
            id: poiMarkers
            mapButtonSize : pinchmap.mapButtonSize
            mapButtonSpacing : pinchmap.mapButtonSpacing
            model : pinchmap.poiMarkerModel
            mapInstance : pinchmap

            onPoiClicked : {
                rWin.log.debug("POI CLICKED!")
                pinchmap.poiClicked(point)
            }
        }
        SearchMarkers {
            id: markers
            mapButtonSize : pinchmap.mapButtonSize
            mapButtonSpacing : pinchmap.mapButtonSpacing
            model : pinchmap.searchMarkerModel
            mapInstance : pinchmap
        }

        PointMenuMarkers {
            id: pointMenuMarkers
            mapButtonSize : pinchmap.mapButtonSize
            mapButtonSpacing : pinchmap.mapButtonSpacing
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

    MapCanvas {
        id: canvas
        visible: true

        // Expand the canvas outside of the visible map area
        // so that the route is not cut-off when the map is
        // being panned.
        width : pinchmap.width*3
        height : pinchmap.height*3
        x : - pinchmap.width
        y : - pinchmap.height

        pinchmap : pinchmap
    }

    Image {
        id: targetIndicator
        source: "image://python/icon/"+ rWin.theme.id +"/target-indicator-cross.png"
        property var t: getScreenpointFromCoord(showTargetAtLat, showTargetAtLon)
        x: map.x + t[0] - width/2
        y: map.y + t[1] - height/2

        visible: showTargetIndicator
        transform: Rotation {
            id: rotationTarget
            origin.x: targetIndicator.width/2
            origin.y: targetIndicator.height/2
        }
    }

/*
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
*/

    Image {
        id: positionIndicator
        property string iconName : currentPositionValid ?
                "position-indicator.svg" :
                "position-indicator-red.svg"

        // TODO: use Python image provider once PyOtherSide 1.5+ is available on Sailfish OS
        // That way we can also use only a single copy of the position indicator SVG files.
        source : if (rWin.qrc) {
            "qrc:/themes/" + rWin.theme.id +"/modrana.svg"
        } else {
            "file://" + rWin.platform.themesFolderPath + "/" + rWin.theme.id + "/" + iconName
        }

        property var t: getScreenpointFromCoord(currentPositionLat, currentPositionLon)
        x: map.x + t[0] - width/2
        y: map.y + t[1] - height + positionIndicator.width/2
        smooth: true
        sourceSize.width : 22 * rWin.c.style.m
        sourceSize.height : 50 * rWin.c.style.m
        visible: showCurrentPosition
        transform: Rotation {
            origin.x: positionIndicator.width/2
            origin.y: positionIndicator.height - positionIndicator.width/2
            angle: currentPositionAzimuth
        }
    }

    ScaleBar {
        id: scaleBar
        anchors.right: parent.right
        anchors.rightMargin: rWin.c.style.main.spacingBig
        anchors.topMargin: rWin.c.style.main.spacingBig + scaleBarTopOffset
        anchors.top: parent.top
        lengthPixels : scaleBarLength[0]
        lengthMeters : scaleBarLength[1]
    }
}
