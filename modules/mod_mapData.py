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
from core.tilenames import *
from time import clock
import time
import os
from core import geo
from threading import Thread
import threading
from modules import urllib3
from core import utils

# socket timeout
import socket

timeout = 30 # this sets timeout for all sockets
socket.setdefaulttimeout(timeout)


class TileNotImageException(Exception):
    def __init__(self):
        self.parameter = 1

    def __str__(self):
        message = "the downloaded tile is not an image as per \
its magic number (it is probably an error response webpage \
returned by the server)"

        return message


def getModule(m, d, i):
    return MapData(m, d, i)


class MapData(RanaModule):
    """Handle downloading of map data"""

    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)
        self.stopThreading = True
        self.dlListLock = threading.Lock() # well, its actually a set
        self.currentDownloadList = [] # list of files and urls for the current download batch
        #    self.currentTilesToGet = [] # used for reporting the (actual) size of the tiles for download
        self.sizeThread = None
        self.getFilesThread = None
        self.aliasForSet = self.set
        self.lastMenuRedraw = 0
        self.notificateOnce = True
        self.scroll = 0
        self.onlineRequestTimeout = 30
        # how often should the download info be
        # updated during batch download, in seconds
        self.batchInfoUpdateInterval = 0.5
        self.mapFolderPath = None
        self._mapLayersModule = None

        self.x = None
        self.y = None
        self.z = None
        self.tiles = []
        self.totalSize = 0

    def firstTime(self):
        # cache the map folder path
        self.mapFolderPath = self.modrana.paths.getMapFolderPath()
        self._mapLayersModule = self.m.get('mapLayers', None) # get the map layers module

    def _getTileFolderPath(self):
        """return path to the map folder"""
        return self.mapFolderPath

    def _getLayerById(self, layerId):
        """Get layer description from the mapLayers module"""
        return self._mapLayersModule.getLayerById(layerId)

    def listTiles(self, route):
        """List all tiles touched by a polyline"""
        tiles = {}
        for pos in route:
            (lat, lon) = pos
            (tx, ty) = tileXY(lat, lon, 15)
            tile = "%d,%d" % (tx, ty)
            if not tiles.has_key(tile):
                tiles[tile] = True
        return tiles.keys()

    def checkTiles(self, tilesToDownload):
        """
        Get tiles that need to be downloaded and look if we don't already have some of these tiles,
        then generate a set of ('url','filename') tuples and send them to the threaded downloader
        """
        print("Checking if there are duplicated tiles")
        start = clock()
        tileFolder = self._getTileFolderPath() # where should we store the downloaded tiles
        if tileFolder is None:
            print("mapData: tile folder path unknown or unusable")
            return []
        layerId = self.get('layer', "mapnik") # TODO: manual layer setting
        layer = self._getLayerById(layerId)
        extension = layer.type # what is the extension for the current layer ?
        folderName = layer.folderName # what is the extension for the current layer ?

        mapTiles = self.m.get('mapTiles', None)

        neededTiles = []

        for tile in tilesToDownload: # check what tiles are already stored
            (z, x, y) = (tile[2], tile[0], tile[1])
            filePath = tileFolder + mapTiles.getImagePath(x, y, z, folderName, extension)
            if not os.path.exists(filePath): # we don't have this file
                neededTiles.append(tile)

        print("Downloading %d new tiles." % len(neededTiles))
        print("Removing already available tiles from dl took %1.2f ms" % (1000 * (clock() - start)))
        return neededTiles


    def getTileUrlAndPath(self, x, y, z, layerId):
        mapTiles = self.m.get('mapTiles', None)
        layer = self._getLayerById(layerId)
        extension = layer.type # what is the extension for the current layer ?
        folderName = layer.folderName # what is the extension for the current layer ?
        url = self.getTileUrl(x, y, z, layerId) # generate url
        tileFolder = self._getTileFolderPath() # where should we store the downloaded tiles
        filePath = os.path.join(tileFolder, mapTiles.getImagePath(x, y, z, folderName, extension))
        fileFolder = os.path.join(tileFolder, mapTiles.getImageFolder(x, z, folderName))
        return url, filePath, fileFolder, folderName, extension

    def addToQueue(self, neededTiles):
        """load urls and filenames to download queue,
           optionally check for duplicates
        """

        tileFolder = self._getTileFolderPath() # where should we store the downloaded tiles
        print("tiles for the batch will be downloaded to: %s" % tileFolder)

        check = self.get('checkTiles', False)
        if check:
            neededTiles = self.checkTiles(neededTiles)
        with self.dlListLock: # make sure the set of needed tiles is accessed in an atomic way
            self.currentDownloadList = neededTiles # load the files to the download queue variable

    def getTileUrl(self, x, y, z, layer):
        """Return url for given tile coordinates and layer"""
        mapTiles = self.m.get('mapTiles', None)
        if mapTiles:
            url = mapTiles.getTileUrl(x, y, z, layer)
            return url
        else:
            return None

    def handleMessage(self, message, messageType, args):
        if message == "refreshTilecount":
            size = int(self.get("downloadSize", 4))
            messageType = self.get("downloadType")
            if messageType != "data":
                print("Error: mod_mapData can't download %s" % messageType)
                return

            # update the info when refreshing tilecount and and no dl/size estimation is active

            if self.sizeThread:
                if self.sizeThread.isAlive() == False:
                    self.sizeThread = None

            if self.getFilesThread:
                if self.getFilesThread.isAlive() == False:
                    self.getFilesThread = None

            location = self.get("downloadArea", "here") # here or route

            maxZoomLimit = 17
            layerId = self.get('layer', None)
            mapLayers = self.m.get('mapLayers', None)
            if mapLayers:
                layer = mapLayers.getLayerById(layerId)
                if layer:
                    maxZoomLimit = layer.maxZoom

            z = self.get('z', 15) # this is the current zoomlevel as show on the map screen
            minZ = z - int(
                self.get('zoomUpSize', 0)) # how many zoomlevels up (from current zoomelevel) should we download ?
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
            print("max: %d, min: %d, diff: %d, middle:%d" % (maxZ, minZ, diffZ, midZ))

            if location == "here":
                # Find which tile we're on
                pos = self.get("pos", None)
                if pos is not None:
                    (lat, lon) = pos
                    # be advised: the xy in this case are not screen coordinates but tile coordinates
                    (x, y) = ll2xy(lat, lon, midZ)
                    tilesAroundHere = set(self.spiral(x, y, midZ, size)) # get tiles around our position as a set
                    # now get the tiles from other zoomlevels as specified
                    zoomlevelExtendedTiles = self.addOtherZoomlevels(tilesAroundHere, midZ, maxZ, minZ)
                    self.addToQueue(zoomlevelExtendedTiles) # load the files to the download queue
            elif location == "track":
                loadTl = self.m.get('loadTracklogs', None) # get the tracklog module
                GPXTracklog = loadTl.getActiveTracklog()
                # get all tracklog points
                trackpointsListCopy = map(lambda x: (x.latitude, x.longitude, None), GPXTracklog.trackpointsList[0])[:]
                tilesToDownload = self.getTilesForRoute(trackpointsListCopy, size, midZ)
                zoomlevelExtendedTiles = self.addOtherZoomlevels(tilesToDownload, midZ, maxZ, minZ)
                self.addToQueue(zoomlevelExtendedTiles) # load the files to the download queue
            elif location == "route": # download around
                routeModule = self.m.get('route', None) # get the tracklog module
                if routeModule:
                    route = routeModule.getDirections()
                    if route:
                        tilesToDownload = self.getTilesForRoute(route.getPointsLLE(), size, midZ)
                        zoomlevelExtendedTiles = self.addOtherZoomlevels(tilesToDownload, midZ, maxZ, minZ)
                        self.addToQueue(zoomlevelExtendedTiles) # load the files to the download queue
                    else:
                        self.set('menu', 'main')
                        self.notify("No active route", 3000)
            elif location == "view":
                proj = self.m.get('projection', None)
                (screenCenterX, screenCenterY) = proj.screenPos(0.5, 0.5) # get pixel coordinates for the screen center
                (lat, lon) = proj.xy2ll(screenCenterX, screenCenterY) # convert to geographic coordinates
                (x, y) = ll2xy(lat, lon, midZ) # convert to tile coordinates
                tilesAroundView = set(self.spiral(x, y, midZ, size)) # get tiles around these coordinates
                # now get the tiles from other zoomlevels as specified
                zoomlevelExtendedTiles = self.addOtherZoomlevels(tilesAroundView, midZ, maxZ, minZ)

                self.addToQueue(zoomlevelExtendedTiles) # load the files to the download queue

        elif message == "getSize":
            # will now ask the server and find the combined size if tiles in the batch
            self.set("sizeStatus", 'unknown') # first we set the size as unknown
            neededTiles = self.currentDownloadList
            layerId = self.get('layer', None)
            print("getting size")
            if len(neededTiles) == 0:
                print("cant get combined size, the list is empty")
                return

            if self.sizeThread is not None:
                if self.sizeThread.finished == False:
                    print("size check already in progress")
                    return

            self.totalSize = 0
            maxThreads = self.get('maxSizeThreads', 5)
            sizeThread = self.GetSize(self, neededTiles, layerId,
                                      maxThreads) # the second parameter is the max number of threads TODO: tweak this
            print( "getSize received, starting sizeThread")
            sizeThread.start()
            self.sizeThread = sizeThread

        elif message == "download":
            # get tilelist and download the tiles using threads
            neededTiles = self.currentDownloadList
            layerId = self.get('layer', None)
            print("starting download")
            if len(neededTiles) == 0:
                print("cant download an empty list")
                return

            if self.getFilesThread is not None:
                if self.getFilesThread.finished == False:
                    print("download already in progress")
                    return

            maxThreads = self.get('maxDlThreads', 5)
            # 2.Oct.2010 2:41 :D
            # after a lot of effort spent, I still can't get threaded download to reliably
            # work with sqlite storage without getting stuck
            # this currently happens only on the N900, not on PC (or I was simply not able to to reproduce it)
            # therefore, when on N900 with sqlite tile storage, use only simple single-threaded download

            #      if self.device=='n900':
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
            getFilesThread = self.GetFiles(self, neededTiles, layerId, maxThreads)
            getFilesThread.start()
            self.getFilesThread = getFilesThread

        elif message == "stopDownloadThreads":
            self.stopBatchDownloadThreads()

        elif message == 'stopSizeThreads':
            self.stopSizeThreads()

        elif message == "up":
            if self.scroll > 0:
                self.scroll -= 1
                self.set('needRedraw', True)
        elif message == "down":
            print("down")
            self.scroll += 1
            self.set('needRedraw', True)
        elif message == "reset":
            self.scroll = 0
            self.set("needRedraw", True)

        elif message == 'dlAroundRoute':
            routeModule = self.m.get('route', None)
            if routeModule:
                route = routeModule.getDirections()
                notification = "Using current route"
                if route:
                    self.set('menu', 'data2')
                    mLength = route.getLength()
                    if mLength:
                        units = self.m.get('units', None)
                        if units:
                            lengthString = units.m2CurrentUnitString(mLength, dp=1, short=True)
                            notification = "%s (%s)" % (notification, lengthString)
                    self.notify(notification, 2000)
                else:
                    self.notify("No active route", 3000)

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
        print("splitting down")
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
            print("we are at z=%d, %d new tiles from %d" % (z, len(newTilesFromSplit), z + 1))
            previousZoomlevelTiles = newTilesFromSplit # set the new tiles s as prev. tiles for next iteration

        # start of the tile coordinates rounding code
        previousZoomlevelTiles = None # we will the tile coordinates to get tiles for the upper level
        print("rounding up")
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
            print("we are at z=%d, %d new tiles" % (z, len(newTilesFromRounding)))
            previousZoomlevelTiles = newTilesFromRounding # set the new tiles s as prev. tiles for next iteration

            print("nr of tiles after extend: %d" % len(extendedTiles))
        print("Extend took %1.2f ms" % (1000 * (clock() - start)))

        del tiles

        return extendedTiles

    class GetSize(Thread):
        """a class used for estimating the size of tiles for given set of coordinates,
           it also removes locally available tiles from the set"""

        def __init__(self, callback, neededTiles, layer, maxThreads):
            Thread.__init__(self)
            self.callback = callback
            self.callbackSet = neededTiles # reference to the actual global set
            self.neededTiles = neededTiles.copy() # local version
            self.maxThreads = maxThreads
            self.layer = layer
            self.processed = 0
            self.urlCount = len(neededTiles)
            self.totalSize = 0
            self.finished = False
            self.quit = False
            url = self.getAnUrl(neededTiles)
            self.connPool = self.createConnectionPool(url)

        def createConnectionPool(self, url):
            """create the connection pool -> to facilitate socket reuse"""
            timeout = self.callback.onlineRequestTimeout
            #headers = { 'User-Agent' : "Mozilla/5.0 (compatible; MSIE 5.5; Linux)" }
            userAgent = self.callback.modrana.configs.getUserAgent()
            headers = {'User-Agent': userAgent}
            connPool = urllib3.connection_from_url(url, headers=headers, timeout=timeout, maxsize=self.maxThreads,
                                                   block=False)
            return connPool

        def getAnUrl(self, neededTiles):
            """get a random url so we can init the pool"""
            if neededTiles:
                tile = None
                for t in neededTiles:
                    tile = t
                    break
                (x, y, z) = (tile[0], tile[1], tile[2])
                url = self.callback.getTileUrl(x, y, z, self.layer)
            else:
                url = ""
            return url

        def run(self):
            print("**!! batch tile size estimation is starting !!**")
            maxThreads = self.maxThreads
            shutdown = threading.Event()
            localDlListLock = threading.Lock()
            incrementLock = threading.Lock()
            threads = []
            for i in range(0, maxThreads): # start threads
                # start download thread
                t = Thread(target=self.getSizeWorker, args=(shutdown, incrementLock, localDlListLock))
                t.daemon = True
                t.start()
                threads.append(t)
            print("Added %d URLS to check for size." % self.urlCount)
            while True:
                time.sleep(
                    self.callback.batchInfoUpdateInterval) # this governs how often we check status of the worker threads
                print("Batch size working...")
                print("(threads: %i)" % (threading.activeCount() - 1, ))
                print("pending: %d, done: %d" % (len(self.neededTiles), self.processed))
                if self.quit == True: # we were ordered to quit
                    print("***get size quiting")
                    shutdown.set() # dismiss all workers
                    self.finished = True
                    break
                if not self.neededTiles: # we processed everything
                    print("***get size finished")
                    shutdown.set()
                    self.finished = True
                    break

        def getSizeWorker(self, shutdown, incrementLock, localDlListLock):
            """a worker thread method for estimating tile size"""
            while 1:
                if shutdown.isSet():
                    print("file size estimation thread is shutting down")
                    break
                    # try to get some work
                with localDlListLock:
                    if self.neededTiles:
                        item = self.neededTiles.pop()
                    else:
                        print("no more work, worker quiting")
                        break
                        # try to retrieve size of a tile
                size = 0
                try:
                    size = self.getSizeForURL(item)
                except Exception:
                    import sys

                    e = sys.exc_info()[1]
                    print("exception in a get size worker thread:\n%s" % e)

                # increment the counter or remove an available tile in a thread safe way
                if size is None: #this signalizes that the tile is available
                    with self.callback.dlListLock:
                        self.callbackSet.discard(item)
                    size = 0 # tiles we don't have don't need to be downloaded, therefore 0
                with incrementLock:
                    self.processed += 1
                    self.totalSize += size

        def getSizeForURL(self, tile):
            """get a size of a tile from its metadata
                 return size
                 return None if the tile is available
                 return 0 if there is an Exception"""
            size = 0
            url = "unknown url"
            try:
                # xet the coordinates
                (z, x, y) = (tile[2], tile[0], tile[1])
                # get the url and other info
                (url, filename, folder, folderPrefix, layerType) = self.callback.getTileUrlAndPath(x, y, z, self.layer)
                m = self.callback.m.get('storeTiles', None) # get the tile storage module
                # get the store tiles module
                if m:
                    # does the tile exist ?
                    if m.tileExists(filename, folderPrefix, z, x, y, layerType,
                                    fromThread=True): # if the file does not exist
                        size = None # it exists, return None
                    else:
                        # the tile does not exist, get ist http header
                        request = self.connPool.urlopen('HEAD', url)
                        size = int(request.getheaders()['content-length'])
            except IOError:
                print("Could not open document: %s" % url)
                size = 0 # the url errored out, so we just say it  has zero size
            except Exception:
                import sys

                e = sys.exc_info()[1]
                print("error, while checking size of a tile")
                print(e)
                size = 0
            return size


    class GetFiles(Thread):
        """a class used for downloading tiles based on a given set of coordinates"""

        def __init__(self, callback, neededTiles, layer, maxThreads):
            Thread.__init__(self)
            self.callback = callback
            self.neededTiles = neededTiles
            self.maxThreads = maxThreads
            self.layer = layer

            self.retryCount = 3

            self.retryInProgress = 0

            self.urlCount = len(neededTiles)
            self.finished = False
            self.quit = False
            url = self.getAnUrl(neededTiles)
            self.connPool = self.createConnectionPool(url)

            # only access following variables with the incrementLock
            self.processed = 0 # counter for processed tiles
            self.found = 0 # number of tiles found locally
            self.downloaded = 0 # counter for downloaded tiles
            self.failedDownloads = []
            self.transfered = 0

        def _resetCounts(self):
            self.processed = 0
            self.urlCount = len(self.neededTiles)
            self.failedDownloads = []

        def getProgress(self):
            return self.processed, self.urlCount, self.transfered, self.getFailedDownloadCount()

        def getFailedDownloads(self):
            return self.failedDownloads

        def getFailedDownloadCount(self):
            return len(self.failedDownloads)

        def getDownloadCount(self):
            return self.downloaded

        def getRetryInProgress(self):
            """return 0 if normal download is in progress
            or 1-n for 1 - n-th retry"""
            return self.retryInProgress

        def isFinished(self):
            return self.finished

        def getAnUrl(self, neededTiles):
            """get a random url so we can init the pool"""
            if neededTiles:
                tile = None
                for t in neededTiles:
                    tile = t
                    break
                (x, y, z) = (tile[0], tile[1], tile[2])
                url = self.callback.getTileUrl(x, y, z, self.layer)
            else:
                url = ""
            return url

        def createConnectionPool(self, url):
            """create the connection pool -> to facilitate socket reuse"""
            timeout = self.callback.onlineRequestTimeout
            connPool = urllib3.connection_from_url(url, timeout=timeout, maxsize=self.maxThreads, block=False)
            return connPool

        def run(self):
            print("**!! batch tile download is starting !!**")
            maxThreads = self.maxThreads
            shutdown = threading.Event()
            incrementLock = threading.Lock()
            workFinished = False

            threads = []
            for i in range(0, maxThreads): # start threads
                # start download threads
                t = Thread(target=self.getTilesWorker, args=(shutdown, incrementLock))
                t.daemon = True
                t.start()
                threads.append(t)
            self.callback.notificateOnce = False
            print("minipool initialized")
            print("Added %d URLS to download." % self.urlCount)
            while True:
                time.sleep(self.callback.batchInfoUpdateInterval)
                print("Batch tile dl working...")
                print("(threads: %i)" % (threading.activeCount() - 1, ))
                print("pending: %d, done: %d" % (len(self.neededTiles), self.processed))
                # there is some downloading going on so a notification will be needed
                self.callback.notificateOnce = True
                if self.quit == True: # we were ordered to quit
                    print("***get tiles quiting")
                    shutdown.set() # dismiss all workers
                    self.finished = True
                    break
                if not self.neededTiles: # we processed everything
                    if self.failedDownloads: # retry failed downloads
                        if self.retryCount > 0:
                            # retry failed tiles
                            self.retryCount -= 1
                            self.retryInProgress += 1
                            self.neededTiles = list(self.failedDownloads) # make a copy
                            self._resetCounts()
                        else: # retries exhausted, quit
                            workFinished = True

                    else: # no failed downloads, just quit
                        workFinished = True

                if workFinished: # check if we are done
                    print("***get tiles finished")
                    if self.callback.notificateOnce:
                        self.callback.sendMessage('ml:notification:m:Batch download complete.;7')
                        self.callback.notificateOnce = False
                    shutdown.set()
                    self.finished = True
                    break


        def getTilesWorker(self, shutdown, incrementLock):
            while 1:
                if shutdown.isSet():
                    print("file download thread is shutting down")
                    break
                    # try to get some work
                try:
                    with self.callback.dlListLock:
                        item = self.neededTiles.pop()
                except: # start the loop from beginning, so that shutdown can be checked and the thread can exit
                    print("waiting for more work")
                    time.sleep(2)
                    continue

                # try to retrieve and store the tile
                failed = False
                try:
                    dlSize = self.saveTileForURL(item)
                except Exception:
                    import sys

                    e = sys.exc_info()[1]
                    failed = True
                    # TODO: try to re-download failed tiles
                    print("exception in get tiles thread:\n%s" % e)
                    #          import traceback, sys
                #          traceback.print_exc(file=sys.stdout) # find what went wrong
                # increment the counter in a thread safe way
                with incrementLock:
                    self.processed += 1
                    if failed:
                        self.failedDownloads.append(item)
                    elif dlSize != False:
                        self.downloaded += 1
                        self.transfered += dlSize

        def saveTileForURL(self, tile):
            """save a tile for url created from its coordinates"""
            (z, x, y) = (tile[2], tile[0], tile[1])
            (url, filename, folder, folderPrefix, layerType) = self.callback.getTileUrlAndPath(x, y, z, self.layer)
            m = self.callback.m.get('storeTiles', None) # get the tile storage module
            if m:
                goAhead = False
                redownload = int(self.callback.get('batchRedownloadAvailableTiles', False))
                if not redownload:
                    # does the the file exist ?
                    # -> don't download it if it does
                    goAhead = not m.tileExists(filename, folderPrefix, z, x, y, layerType, fromThread=True)
                elif redownload == 1: # redownload all
                    goAhead = True
                elif redownload == 2: # update
                    # only download tiles in the area that already exist
                    goAhead = m.tileExists(filename, folderPrefix, z, x, y, layerType, fromThread=True)
                    # TODO: maybe make something like tile objects so we don't have to pass so many parameters ?
                if goAhead: # if the file does not exist
                    request = self.connPool.request('get', url)
                    size = int(request.getheaders()['content-length'])
                    content = request.data
                    # The tileserver sometimes returns a HTML error page
                    # instead of the tile, which is then saved instead of the tile an
                    # users are then confused why tiles they have downloaded don't show up.

                    # To raise a proper error on this behaviour, we check the tiles magic number
                    # and if is not an image we raise the TileNotImageException.

                    # TODO: does someone supply non-bitmap/SVG tiles ?
                    if utils.isTheStringAnImage(content):
                        #its an image, save it
                        m.automaticStoreTile(content, folderPrefix, z, x, y, layerType, filename)
                    else:
                        # its not ana image, raise exception
                        raise TileNotImageException()
                    return size # something was actually downloaded and saved
                else:
                    return False # nothing was downloaded

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
        print("Listing tiles took %1.2f ms" % (1000 * (clock() - start)))
        print("unique tiles %d" % len(tilesToDownload))
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

    def drawMenu(self, cr, menuName, args=None):
        # is this menu the correct menu ?
        if menuName == 'batchTileDl':
            # in order for the threads to work normally, it is needed to pause the main loop for a while
            # * this works only for this menu, in other menus (even the edit  menu) the threads will be slow to start
            # * when looking at map, the threads behave as expected :)
            # * so, when downloading:
            # -> look at the map OR the batch progress :)**
            time.sleep(0.5)
            self.set('needRedraw', True)
            (x1, y1, w, h) = self.get('viewport', None)
            self.set('dataMenu', 'edit')
            menus = self.m.get("menu", None)
            sizeThread = self.sizeThread
            getFilesThread = self.getFilesThread
            self.set("batchMenuEntered", True)

            if w > h:
                cols = 4
                rows = 3
            elif w < h:
                cols = 3
                rows = 4
            else: # w == h
                cols = 4
                rows = 4

            dx = w / cols
            dy = h / rows
            # * draw "escape" button
            menus.drawButton(cr, x1, y1, dx, dy, "", "back", "menu:rebootDataMenu|set:menu:main")
            # * draw "edit" button
            menus.drawButton(cr, (x1 + w) - 2 * dx, y1, dx, dy, "edit", "tools",
                             "menu:setupEditBatchMenu|set:menu:editBatch")
            # * draw "start" button
            if self.getFilesThread:
                if self.getFilesThread.isFinished():
                    menus.drawButton(cr, (x1 + w) - 1 * dx, y1, dx, dy, "retry", "start", "mapData:download")
                else:
                    menus.drawButton(cr, (x1 + w) - 1 * dx, y1, dx, dy, "stop", "stop", "mapData:stopDownloadThreads")
            else:
                menus.drawButton(cr, (x1 + w) - 1 * dx, y1, dx, dy, "start", "start", "mapData:download")
                # * draw the combined info area and size button (aka "box")
            boxX = x1
            boxY = y1 + dy
            boxW = w
            boxH = h - dy
            if self.sizeThread:
                menus.drawButton(cr, boxX, boxY, boxW, boxH, "", "generic", "mapData:stopSizeThreads")
            else:
                menus.drawButton(cr, boxX, boxY, boxW, boxH, "", "generic", "mapData:getSize")
                # * display information about download status
            getFilesText = self.getFilesText(getFilesThread)
            sizeText = self.getSizeText(sizeThread)
            getFilesTextX = boxX + dx / 8
            getFilesTextY = boxY + boxH * 1 / 10
            menus.showText(cr, "%s\n\n%s" % (getFilesText, sizeText), getFilesTextX, getFilesTextY, w - dx / 4, 40)

            #      # * display information about size of the tiles
            #      sizeTextX = boxX + dx/8
            #      sizeTextY = boxY + boxH*2/4
            #      menus.showText(cr, sizeText, sizeTextX, sizeTextY, w-dx/4, 40)

            # * display information about free space available (for the filesystem with tilefolder)
            freeSpaceText = self.getFreeSpaceText()
            freeSpaceTextX = boxX + dx / 8
            freeSpaceTextY = boxY + boxH * 3 / 4
            menus.showText(cr, freeSpaceText, freeSpaceTextX, freeSpaceTextY, w - dx / 4, 40)

        if menuName == 'chooseRouteForDl':
            menus = self.m.get('menu', None)
            tracks = self.m.get('loadTracklogs', None).getTracklogList()
            print(tracks)

            def describeTracklog(index, category, tracks):
                """describe a tracklog list item"""
                track = tracks[index]

                action = "set:activeTracklogPath:%s|loadTracklogs:loadActive" % track['path']

                status = self.get('editBatchMenuActive', False)
                if status == True:
                    action += '|menu:setupEditBatchMenu|set:menu:editBatch'
                else:
                    action += '|set:menu:data2'
                name = tracks[index]['filename']
                desc = 'cat.: ' + track['cat'] + '   size:' + track['size'] + '   last modified:' + track[
                    'lastModified']
                #        if track.perElevList:
                #          length = track.perElevList[-1][0]
                #          units = self.m.get('units', None)
                #          desc+=", %s" % units.km2CurrentUnitString(length)
                return name, desc, action


            status = self.get('editBatchMenuActive', False)
            if status == True:
                parent = 'editBatch'
            else:
                parent = 'data'
            scrollMenu = 'mapData'
            menus.drawListableMenuControls(cr, menuName, parent, scrollMenu)
            menus.drawListableMenuItems(cr, tracks, self.scroll, describeTracklog)

    def getFilesText(self, getFilesThread):
        """return a string describing status of the download threads"""
        text = ""
        tileCount = len(self.currentDownloadList)
        if getFilesThread is None:
            if tileCount:
                text = "Press <b>Start</b> to download ~ <b>%d</b> tiles." % tileCount
            else:
                text = "Download queue empty."
        else:
            (currentTileCount, totalTileCount, BTotalTransferred, failedCount) = getFilesThread.getProgress()
            if getFilesThread.isAlive() == True:
                MBTotalTransferred = BTotalTransferred / float(1048576)
                totalTileCount = getFilesThread.urlCount
                currentTileCount = getFilesThread.processed
                retryNumber = getFilesThread.getRetryInProgress()
                if retryNumber:
                    action = "Retry nr. %d" % retryNumber
                else:
                    action = "Downloading"

                # handle singular versus plural
                if failedCount == 1:
                    failedCountString = "1 download failed"
                else:
                    failedCountString = "%d downloads failed" % failedCount
                text = "<b>%s</b>: <b>%d</b> of <b>%d</b> tiles done\n<b>%1.2f MB</b> transferred, %s" % (
                    action, currentTileCount, totalTileCount, MBTotalTransferred, failedCountString)
            elif getFilesThread.isAlive() == False: #TODO: send an alert that download is complete
                if getFilesThread.getDownloadCount():
                    # some downloads occurred
                    text = "<b>Download complete.</b>"
                else:
                    # no downloads occurred
                    if failedCount:
                        # no downloads + failed downloads
                        text = "<b>Download of all tiles failed.</b>"
                    else:
                        # no downloads and no failed downloads
                        text = "<b>All tiles were locally available.</b>"
        return text

    def getSizeText(self, sizeThread):
        """return a string describing status of the size counting threads"""
        tileCount = len(self.currentDownloadList)
        if tileCount == 0:
            return ""
        if sizeThread is None:
            return "Total size of tiles is unknown (<i>click to compute</i>)."
        elif sizeThread.isAlive():
            totalTileCount = sizeThread.urlCount
            currentTileCount = sizeThread.processed
            currentSize = sizeThread.totalSize / 1048576 # = 1024.0*1024.0
            text = "Checking: %d of %d tiles complete(<b>%1.0f MB</b>)" % (
            currentTileCount, totalTileCount, currentSize)
            return text
        elif sizeThread.isAlive() == False:
            sizeInMB = sizeThread.totalSize / (1024.0 * 1024.0)
            text = "Total size for download: %1.2f MB" % sizeInMB
            return text

    def getFreeSpaceText(self):
        """return a string describing the space available on the filesystem where the tile-folder is"""
        path = self._getTileFolderPath()
        f = os.statvfs(path)
        freeSpaceInBytes = (f.f_bsize * f.f_bavail)
        freeSpaceInMB = freeSpaceInBytes / (1024.0 * 1024.0)
        text = "Free space available: %1.1f MB" % freeSpaceInMB
        return text

    def stopSizeThreads(self):
        if self.sizeThread:
            try:
                self.sizeThread.quit = True
            except Exception:
                import sys

                e = sys.exc_info()[1]
                print("error while shutting down size thread")
                print(e)

        time.sleep(0.1) # make place for the tread to handle whats needed
        self.sizeThread = None

    def stopBatchDownloadThreads(self):
        if self.getFilesThread:
            try:
                self.getFilesThread.quit = True
            except Exception:
                import sys

                e = sys.exc_info()[1]
                print("error while shutting down files thread")
                print(e)

        time.sleep(0.1) # make place for the tread to handle whats needed
        self.getFilesThread = None

    def shutdown(self):
        self.stopSizeThreads()
        self.stopBatchDownloadThreads()
