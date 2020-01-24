# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Handles downloading of map data
#----------------------------------------------------------------------------
# Copyright 2008, Oliver White
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#---------------------------------------------------------------------------
from __future__ import with_statement # for python 2.5
from modules.base_module import RanaModule
from time import clock
import time
import os
import copy
from core import geo
from core import utils
from core import tiles
from core import constants
from core.tilenames import *
import threading
from .pools import BatchSizeCheckPool
from .pools import BatchTileDownloadPool

# socket timeout
import socket

timeout = 30 # this sets timeout for all sockets
socket.setdefaulttimeout(timeout)

DL_LOCATION_HERE = "here"
DL_LOCATION_VIEW = "view"
DL_LOCATION_TRACK = "track"
DL_LOCATION_ROUTE = "route"

# maximum zoom level used when no maximum is specified for a layer
MAX_ZOOMLEVEL = 17

def getModule(*args, **kwargs):
    return MapData(*args, **kwargs)


class MapData(RanaModule):
    """Handle downloading of map data"""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self._tileDownloadRequests = set()
        self._tileDownloadRequestsLock = threading.RLock()

        self._checkPool = BatchSizeCheckPool()
        self._downloadPool = BatchTileDownloadPool()

        self.notificateOnce = True
        self.scroll = 0

        self.x = None
        self.y = None
        self.z = None
        self.tiles = []
        self.totalSize = 0

        self.minZ = 0
        self.midZ = 15
        self.maxZ = MAX_ZOOMLEVEL

    def addDownloadRequests(self, requests):
        """Add download requests to the download request set

        :param list requests: a list of lzxy tuples representing download requests
        """

        with self._tileDownloadRequestsLock:
            self._tileDownloadRequests.update(requests)

    def removeTileDownloadRequest(self, request):
        with self._tileDownloadRequestsLock:
            self._tileDownloadRequests.discard(request)

    def clearRequests(self):
        """Clear the download request set"""
        with self._tileDownloadRequestsLock:
            self._tileDownloadRequests.clear()

    @property
    def requestCount(self):
        return len(self._tileDownloadRequests)

    @property
    def checkSizeRunning(self):
        return self._checkPool.running

    @property
    def batchDownloadRunning(self):
        return self._downloadPool.running

    @property
    def running(self):
        return self.checkSizeRunning or self.batchDownloadRunning

    @property
    def checkSizePool(self):
        return self._checkPool

    @property
    def downloadPool(self):
        return self._downloadPool

    def _getLayerById(self, layerId):
        """Get layer description from the mapLayers module"""
        return self.m.get("mapLayers").getLayerById(layerId)

    def listTiles(self, route):
        """List all tiles touched by a polyline"""
        _tiles = {}
        for pos in route:
            (lat, lon) = pos
            (tx, ty) = tileXY(lat, lon, 15)
            tile = "%d,%d" % (tx, ty)
            if not tile in _tiles:
                _tiles[tile] = True
        return _tiles.keys()

    def handleMessage(self, message, messageType, args):
        if message == "refreshTilecount":
            self.refreshTilecount()
        elif message == "getSize":
            self.startBatchSizeEstimation()

        elif message == "download":
            self.startBatchDownload()

        elif message == "stopDownloadThreads":
            self.stopBatchDownload()

        elif message == 'stopSizeThreads':
            self.stopBatchSizeEstimation()

        elif message == 'dlAroundRoute':
            self._downloadAroundCurrentRoute()

    def addOtherZoomlevels(self, tiles, tilesZ, maxZ, minZ):
        """expand the tile coverage to other zoomlevels
        maxZ = maximum NUMERICAL zoom, 17 for example
        minZ = minimum NUMERICAL zoom, 0 for example
        we use two different methods to get the needed tiles:
        * splitting the tiles from one zoomlevel down to the other
        * rounding the tiles coordinates to get tiles from one zoomlevel up
        we choose a zoomlevel (tilesZ) and then split down and round down from it
        * tilesZ is determined in the handle message method,
        it is the zoomlevel on which we compute which tiles are in our download radius
        -> if tilesZ is too low, this initial tile finding can take too long
        -> if tilesZ is too high, the tiles could be much larger than our dl. radius and we would
        be downloading much more tiles than needed
        => for now, if we get tilesZ (called midZ in handle message) that is lower than 15,
        we set it to the lowest zoomlevel, so we get don't get too much unneeded tiles when splitting
        """
        start = clock()
        extendedTiles = tiles.copy()

        # start of the tile splitting code
        previousZoomlevelTiles = None # we will split the tiles from the previous zoomlevel
        self.log.info("splitting down")
        for z in range(tilesZ, maxZ): # to max zoom (fo each z we split one zoomlevel down)
            newTilesFromSplit = set() # tiles from the splitting go there
            if previousZoomlevelTiles is None: # this is the first iteration
                previousZoomlevelTiles = tiles.copy()
            for tile in previousZoomlevelTiles:
                x = tile[0]
                y = tile[1]
                # now we split each tile to 4 tiles on a higher zoomlevel nr
                # see: http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Subtiles
                # for a tile with coordinates x,y:
                # 2x,2y  |2x+1,2y
                # 2x,2y+1|2x+1,2y+1
                leftUpperTile = (2 * x, 2 * y, z + 1)
                rightUpperTile = (2 * x + 1, 2 * y, z + 1)
                leftLowerTile = (2 * x, 2 * y + 1, z + 1)
                rightLowerTile = (2 * x + 1, 2 * y + 1, z + 1)
                newTilesFromSplit.add(leftUpperTile)
                newTilesFromSplit.add(rightUpperTile)
                newTilesFromSplit.add(leftLowerTile)
                newTilesFromSplit.add(rightLowerTile)
            extendedTiles.update(newTilesFromSplit) # add the new tiles to the main set
            self.log.info("we are at z=%d, %d new tiles from %d", z, len(newTilesFromSplit), z + 1)
            previousZoomlevelTiles = newTilesFromSplit # set the new tiles s as prev. tiles for next iteration

        # start of the tile coordinates rounding code
        previousZoomlevelTiles = None # we will the tile coordinates to get tiles for the upper level
        self.log.info("rounding up")
        r = range(minZ, tilesZ) # we go from the tile-z up, e.g. a sequence progressively smaller integers
        r.reverse()
        for z in r:
            newTilesFromRounding = set() # tiles from the rounding go there
            if previousZoomlevelTiles is None: # this is the first iteration
                previousZoomlevelTiles = tiles.copy()
            for tile in previousZoomlevelTiles:
                x = tile[0]
                y = tile[1]
                # as per: http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Subtiles
                # we divide each coordinate with 2 to get the upper tile
                # some upper tiles can be found up to four times, so this could be most probably
                # optimized if need be (for charting the Jupiter, Sun or a Dyson sphere ? :)"""
                upperTileX = int(x / 2.0)
                upperTileY = int(y / 2.0)
                upperTile = (upperTileX, upperTileY, z)
                newTilesFromRounding.add(upperTile)
            extendedTiles.update(newTilesFromRounding) # add the new tiles to the main set
            self.log.info("we are at z=%d, %d new tiles", z, len(newTilesFromRounding))
            previousZoomlevelTiles = newTilesFromRounding # set the new tiles s as prev. tiles for next iteration

            self.log.info("nr of tiles after extend: %d", len(extendedTiles))
        self.log.info("Extend took %1.2f ms", 1000 * (clock() - start))

        del tiles

        return extendedTiles

    def expand(self, tileset, amount=1):
        """Given a list of tiles, expand the coverage around those tiles"""
        tiles = {}
        tileset = [[int(b) for b in a.split(",")] for a in tileset]
        for tile in tileset:
            (x, y) = tile
            for dx in range(-amount, amount + 1):
                for dy in range(-amount, amount + 1):
                    tiles["%d,%d" % (x + dx, y + dy)] = True
        return tiles.keys()

    def spiral(self, x, y, z, distance):
        (x, y) = (int(round(x)), int(round(y)))
        # for now we are downloading just tiles,
        # so I modified this to round the coordinates right after we get them

        class spiraller(object):
            def __init__(self, x, y, z):
                self.x = x
                self.y = y
                self.z = z
                self.tiles = [(x, y, z)]

            def moveX(self, dx, direction):
                for i in range(dx):
                    self.x += direction
                    self.touch(self.x, self.y, self.z)

            def moveY(self, dy, direction):
                for i in range(dy):
                    self.y += direction
                    self.touch(self.x, self.y, self.z)

            def touch(self, x, y, z):
                self.tiles.append((x, y, z))

        s = spiraller(x, y, z)
        for d in range(1, distance + 1):
            s.moveX(1, 1) # 1 right
            s.moveY(d * 2 - 1, -1) # d*2-1 up
            s.moveX(d * 2, -1)   # d*2 left
            s.moveY(d * 2, 1)    # d*2 down
            s.moveX(d * 2, 1)    # d*2 right
        return s.tiles

    def getTilesForRoute(self, route, radius, z):
        """get tilenames for tiles around the route for given radius and zoom"""
        # now we look whats the distance between each two trackpoints,
        # if it is larger than the tracklog radius, we add additional interpolated points,
        # so we get continuous coverage for the tracklog
        first = True
        interpolatedPoints = []
        for point in route:
            if first: # the first point has no previous point
                (lastLat, lastLon) = point[0], point[1]
                first = False
                continue
            thisLat, thisLon = point[0], point[1]
            distBtwPoints = geo.distance(lastLat, lastLon, thisLat, thisLon)
            # if the distance between points was greater than the given radius for tiles,
            # there would be no continuous coverage for the route
            if distBtwPoints > radius:
                # so we call this recursive function to interpolate points between
                # points that are too far apart
                interpolatedPoints.extend(self.addPointsToLine(lastLat, lastLon, thisLat, thisLon, radius))
            (lastLat, lastLon) = (thisLat, thisLon)
            # because we don't care about what order are the points in this case,
        # we just add the interpolated points to the end
        route.extend(interpolatedPoints)
        start = clock()
        tilesToDownload = set()
        for point in route: #now we iterate over all points of the route
            lat, lon = point[0], point[1]
            # be advised: the xy in this case are not screen coordinates but tile coordinates
            (x, y) = ll2xy(lat, lon, z)
            # the spiral gives us tiles around coordinates for a given radius
            currentPointTiles = self.spiral(x, y, z, radius)
            # now we take the resulting list  and process it in such a way,
            # that the tiles coordinates can be stored in a set,
            # so we will save only unique tiles
            outputSet = set(map(lambda x: tuple(x), currentPointTiles))
            tilesToDownload.update(outputSet)
        self.log.info("Listing tiles took %1.2f ms", 1000 * (clock() - start))
        self.log.info("unique tiles %d", len(tilesToDownload))
        return tilesToDownload

    def addPointsToLine(self, lat1, lon1, lat2, lon2, maxDistance):
        """experimental (recursive) function for adding additional points between two coordinates,
        until their distance is less or or equal to maxDistance
        (this is actually a wrapper for a local recursive function)"""
        pointsBetween = []

        def localAddPointsToLine(lat1, lon1, lat2, lon2, maxDistance):
            distance = geo.distance(lat1, lon1, lat2, lon2)
            if distance <= maxDistance: # the termination criterion
                return
            else:
                middleLat = (lat1 + lat2) / 2.0 # fin the midpoint between the two points
                middleLon = (lon1 + lon2) / 2.0
                pointsBetween.append((middleLat, middleLon))
                # process the 2 new line segments
                localAddPointsToLine(lat1, lon1, middleLat, middleLon, maxDistance)
                localAddPointsToLine(middleLat, middleLon, lat2, lon2, maxDistance)

        localAddPointsToLine(lat1, lon1, lat2, lon2, maxDistance) # call the local function
        return pointsBetween


    @property
    def approxDownloadSize(self):
        """Return approximate download size based on the average tile size so far

        In short:
        <avg tile size> = <downloaded so far> / <nr tiles done>
        <approx download size> = <avg tile size> * <nr of tiles in batch>

        :return int: approximate download size
        """
        if self.batchDownloadRunning and self._downloadPool.done:
            return (self._downloadPool.downloadedDataSize/float(self._downloadPool.done))*self._downloadPool.batchSize
        else:
            return -1

    def getFreeSpaceString(self):
        """Return a string describing the space available on the filesystem
        where the tile-folder is located

        :returns: string describing free space in tile folder
        :rtype: str
        """
        path = self.modrana.paths.map_folder_path
        free_space = utils.free_space_in_path(path)
        if free_space is not None:
            prettySpace = utils.bytes_to_pretty_unit_string(utils.free_space_in_path(path))
            return prettySpace
        else:
            return "unknown"

    def shutdown(self):
        self.stopBatchDownload()
        self.stopBatchSizeEstimation()

    def refreshTilecount(self):
        """The batch download parameters were changed,
        refresh the current tilecount
        """
        messageType = self.get("downloadType")
        if messageType != "data":
            self.log.error("can't download %s (wrong download type)", messageType)
            return

        # dump previous requests first
        self.clearRequests()

        # don't refresh if an operation is already running
        if self.running:
            self.log.error("not refreshing - a operation is currently running")
            return

        location = self.get("downloadArea", "here") # here or route

        maxZoomLimit = 17
        layerId = self.get('layer', None)
        mapLayers = self.m.get('mapLayers', None)
        if mapLayers:
            layer = mapLayers.getLayerById(layerId)
            if layer:
                maxZoomLimit = layer.max_zoom

        # for some reason z might be a float sometimes,
        # so we need to make sure it is an integer
        z = int(self.get('z', 15)) # this is the current zoomlevel as show on the map screen
        minZ = z - int(
            self.get('zoomUpSize', 0)
        ) # how many zoomlevels up (from current zoomelevel) should we download ?
        if minZ < 0:
            minZ = 0
            # how many zoomlevels down (from current zoomlevel) should we download ?

        zoomDownSize = int(self.get('zoomDownSize', 0))
        if zoomDownSize < 0: # negative value means maximum zoom for the layer
            maxZ = maxZoomLimit
        else:
            maxZ = z + zoomDownSize

        if maxZ > maxZoomLimit:
            maxZ = 17 #TODO: make layer specific
            #      z = currentZ # current Zoomlevel
        diffZ = maxZ - minZ
        midZ = int(minZ + (diffZ / 2.0))

        # well, its not exactly middle, its jut a value that decides, if we split down or just round up
        # splitting from a zoomlevel too high can lead to much more tiles than requested
        # for example, we want tiles for a 10 km radius but we choose to split from a zoomlevel, where a tile is
        # 20km*20km and our radius intersects four of these tiles, when we split these tiles, we get tiles for an
        # are of 40km*40km, instead of the requested 10km
        # therefore, zoom level 15 is used as the minimum number for splitting tiles down
        # when the maximum zoomlevel from the range requested is less than 15, we don't split at all
        if midZ < 15 and maxZ < 15:
            midZ = maxZ
        else:
            midZ = 15
        self.log.info("max: %d, min: %d, diff: %d, middle:%d", maxZ, minZ, diffZ, midZ)
        self.minZ = minZ
        self.midZ = midZ
        self.maxZ = maxZ

        if location == DL_LOCATION_HERE:
            self._addTilesAroundPosition()

        elif location == DL_LOCATION_TRACK:
            self._addTilesAroundTrack()

        elif location == DL_LOCATION_ROUTE: # download around
            self._addTilesAroundRoute()

        elif location == DL_LOCATION_VIEW:
            self._addTilesAroundView()

        self._checkPool.reset()
        self._downloadPool.reset()

        self.set("needsRefresh", True)

    def _addTilesAroundPosition(self):
        """Add tiles around current geographic coordinates (if known)"""
        # Find which tile we're on
        size = int(self.get("downloadSize", 4))
        pos = self.get("pos", None)
        if pos is not None:
            (lat, lon) = pos
            # be advised: the xy in this case are not screen coordinates but tile coordinates
            (x, y) = ll2xy(lat, lon, self.midZ)
            tilesAroundHere = set(self.spiral(x, y, self.midZ, size)) # get tiles around our position as a set
            # now get the tiles from other zoomlevels as specified
            zoomlevelExtendedTiles = self.addOtherZoomlevels(tilesAroundHere, self.midZ, self.maxZ, self.minZ)
            self.addDownloadRequests(zoomlevelExtendedTiles) # load the files to the download queue

    def _addTilesAroundTrack(self):
        """Get tiles around the active (?) tracklog
        TODO: this looks kinda weird :)
        """
        loadTl = self.m.get('loadTracklogs', None) # get the tracklog module
        GPXTracklog = loadTl.get_active_tracklog()
        size = int(self.get("downloadSize", 4))
        # get all tracklog points
        trackpointsListCopy = map(lambda x: (x.latitude, x.longitude, None), GPXTracklog.trackpointsList[0])[:]
        tilesToDownload = self.getTilesForRoute(trackpointsListCopy, size, self.midZ)
        zoomlevelExtendedTiles = self.addOtherZoomlevels(tilesToDownload, self.midZ, self.maxZ, self.minZ)
        self.addDownloadRequests(zoomlevelExtendedTiles) # load the files to the download queue

    def _addTilesAroundRoute(self):
        """Add tiles around currently active turn-by-turn route (if any)"""
        routeModule = self.m.get('route', None) # get the tracklog module
        size = int(self.get("downloadSize", 4))
        if routeModule:
            route = routeModule.get_directions()
            if route:
                tilesToDownload = self.getTilesForRoute(route.points_lle, size, self.midZ)
                zoomlevelExtendedTiles = self.addOtherZoomlevels(tilesToDownload, self.midZ, self.maxZ, self.minZ)
                self.addDownloadRequests(zoomlevelExtendedTiles) # load the files to the download queue
            else:
                self.set('menu', 'main')
                self.notify("No active route", 3000)

    def _addTilesAroundView(self):
        """Add tiles around center of the current main map view"""
        proj = self.m.get('projection', None)
        size = int(self.get("downloadSize", 4))
        (screenCenterX, screenCenterY) = proj.screenPos(0.5, 0.5) # get pixel coordinates for the screen center
        (lat, lon) = proj.xy2ll(screenCenterX, screenCenterY) # convert to geographic coordinates
        (x, y) = ll2xy(lat, lon, self.midZ) # convert to tile coordinates
        tilesAroundView = set(self.spiral(x, y, self.midZ, size)) # get tiles around these coordinates
        # now get the tiles from other zoomlevels as specified
        zoomlevelExtendedTiles = self.addOtherZoomlevels(tilesAroundView, self.midZ, self.maxZ, self.minZ)
        self.addDownloadRequests(zoomlevelExtendedTiles) # load the files to the download queue

    def startBatchDownload(self):
        """Start threaded batch tile download"""
        layerId = self.get('layer', "mapnik")
        self._downloadPool.layer = self._getLayerById(layerId)

        self.log.info("starting download")
        if len(self._tileDownloadRequests) == 0:
            self.log.error("can't do batch download - no requests")
            return

        if self._downloadPool.running:
            self.log.error("batch download already in progress")
            return
        elif self._checkPool.running:
            self.log.error("check size running, not starting size check")
            return

        self.log.info("starting batch tile download")
        # process all download request and discard processed requests from the pool
        self._downloadPool.startBatch(self._tileDownloadRequests)

        # For historical note (29.Mar.2014):
        # 2.Oct.2010 2:41 :D
        # after a lot of effort spent, I still can't get threaded download to reliably
        # work with sqlite storage without getting stuck
        # this currently happens only on the N900, not on PC (or I was simply not able to to reproduce it)
        # therefore, when on N900 with sqlite tile storage, use only simple single-threaded download

        #      if self.dmod.device_id == 'n900':
        #        storageType = self.get('tileStorageType', None)
        #        if storageType=='sqlite':
        #          mode='singleThreaded'
        #        else:
        #          mode='multiThreaded'
        #      else:
        #        mode='multiThreaded'

        # 2.Oct.2010 3:42 ^^
        # scratch this
        # well, looks like the culprit was just the urlib3 socket pool with blocking turned on
        # so all the threads (even when doing it with a single thread) hanged on the block
        # it seems to be working alright + its pretty fast too

    def stopBatchDownload(self):
        """Stop threaded batch tile download"""
        self.log.info("stopping batch tile download")
        self._downloadPool.stop()

    def _downloadAroundCurrentRoute(self):
        """Use currently active route as batch download target"""
        routeModule = self.m.get('route', None)
        if routeModule:
            route = routeModule.get_directions()
            notification = "Using current route"
            if route:
                self.set('menu', 'data2')
                mLength = route.length
                if mLength:
                    units = self.m.get('units', None)
                    if units:
                        lengthString = units.m2CurrentUnitString(mLength, dp=1, short=True)
                        notification = "%s (%s)" % (notification, lengthString)
                self.notify(notification, 2000)
            else:
                self.notify("No active route", 3000)

    def startBatchSizeEstimation(self):
        """Start threaded batch size estimation"""
        # will now ask the server and find the combined size if tiles in the batch
        # and also remove locally available tiles from the request set
        self.set("sizeStatus", 'unknown') # first we set the size as unknown
        layerId = self.get('layer', "mapnik")
        self._checkPool.layer = self._getLayerById(layerId)

        self.log.info("getting size")
        if len(self._tileDownloadRequests) == 0:
            self.log.error("can't check size - no requests")
            return

        if self._checkPool.running:
            self.log.error("size check already in progress")
            return
        elif self._downloadPool.running:
            self.log.error("batch download running, not starting size check")
            return

        with self._tileDownloadRequestsLock:
            # start check on a shallow copy that we can process
            # iterate over it but also pop locally available
            # tiles from the the original set
            requestsCopy = copy.copy(self._tileDownloadRequests)
        self.log.info("starting batch size estimation")
        self._checkPool.startBatch(requestsCopy)

    def stopBatchSizeEstimation(self):
        """Stop the threaded batch size estimation"""
        self.log.info("stopping batch size estimation")
        self._checkPool.stop()
