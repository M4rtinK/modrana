# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Display map tile images (+ position cursor)
#----------------------------------------------------------------------------
# Copyright 2007-2008, Oliver White
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
from threading import Thread
import threading
import os
import time
import string
import sys
import traceback

try:  # Python 2
    from urllib2 import urlopen, HTTPError, URLError
except ImportError:  # Python 3
    from urllib.request import urlopen
    from urllib.error import HTTPError, URLError

from modules import urllib3
from core import utils
from core import rectangles
from core.tilenames import *
from core.backports import six

StringIO = six.moves.cStringIO

#import socket
#timeout = 30 # this sets timeout for all sockets
#socket.setdefaulttimeout(timeout)


# if image manipulation tools are available, import them
# and otherwise disable tile image manipulation
IMAGE_MANIPULATION_IMPORT_SUCCESS = False

# only import GKT libs if GTK GUI is used
from core import gs

if gs.GUIString == "GTK":
    import gtk
    import gobject
    import cairo

    # as the image manipulation is dependent on GTK being
    # used, only load it if using the GTK GUI
    try:
        import Image
        import ImageOps

        IMAGE_MANIPULATION_IMPORT_SUCCESS = True
    except ImportError:
        e = sys.exc_info()[1]
        print('mapTiles: import of image manipulation tools unsuccessful'
              ' - tile image manipulation disabled')
        print(e)


def getModule(m, d, i):
    return MapTiles(m, d, i)


class MapTiles(RanaModule):
    """Display map images"""

    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)
        self.images = [{}, {}] # the first dict contains normal image data, the second contains special tiles
        self.imagesLock = threading.RLock()
        self.threads = {}
        self.threadListCondition = threading.Condition(threading.Lock())
        self.maxImagesInMemory = 150 # to avoid a memory leak
        self.imagesTrimmingAmount = 30 # how many tiles to remove once the maximum is reached
        self.loadRequestCStackSize = 10 # size for the circular loading request stack
        """so that trim does not run always run after adding a tile"""
        self.tileSide = 256 # by default, the tiles are squares, side=256
        """ TODO: analyse memory usage,
                  set appropriate value,
                  platform dependent value,
                  user configurable
        """
        self.loadRequestCStack = utils.SynchronizedCircularStack(self.loadRequestCStackSize)
        #    self.loadingNotifyQueue = Queue.Queue(1)
        self.downloadRequestPool = []
        self.downloadRequestPoolLock = threading.Lock()
        self.downloadRequestTimeout = 30 # in seconds
        self.startTileDownloadManagementThread()
        self.idleLoaderActive = False # report the idle tile loader is running

        self.shutdownAllThreads = False # notify the threads that shutdown is in progress

        specialTiles = [
            ('tileDownloading', 'themes/default/tile_downloading.png'),
            ('tileDownloadFailed', 'themes/default/tile_download_failed.png'),
            ('tileLoading', 'themes/default/tile_loading.png'),
            ('tileWaitingForDownloadSlot', 'themes/default/tile_waiting_for_download_slot.png'),
            ('tileNetworkError', 'themes/default/tile_network_error.png')
        ]

        if gs.GUIString == "GTK":
            self.loadSpecialTiles(specialTiles) # load the special tiles to the special image cache
            self.loadingTile = self.images[1]['tileLoading']
            self.downloadingTile = self.images[1]['tileDownloading']
            self.waitingTile = self.images[1]['tileWaitingForDownloadSlot']

        self.mapViewModule = None
        self._mapLayersModule = None

        # cache the map folder path
        self.mapFolderPath = self.modrana.paths.getMapFolderPath()
        print(" @ mapTiles: map folder path: %s" % self.mapFolderPath)

        self._storeTiles = None

        self.connPools = {} # connection pool dictionary

        self.cacheImageSurfaces = gs.GUIString == "GTK"

    def firstTime(self):
        self.mapViewModule = self.m.get('mapView', None)
        scale = self.get('mapScale', 1)
        self._updateScalingCB('mapScale', scale, scale)
        self.modrana.watch('mapScale', self._updateScalingCB)
        self.modrana.watch('z', self._updateScalingCB)
        self._storeTiles = self.m.get('storeTiles', None) # get the tile storage module
        self._mapLayersModule = self.m.get('mapLayers', None) # get the map layers module

        # map tile filtering
        self.modrana.watch('currentTheme', self._updateTileFilteringCB, runNow=True)
        self.modrana.watch('invertMapTiles', self._updateTileFilteringCB, runNow=True)
        # check if tile filtering is enabled or should be enabled with current theme

    def getTile(self, layerId, z, x, y):
        """return a tile specified by layerID, z, x & y
        * first look if such a tile is available from storage
        * if not, download it"""
        # check if the tile is in the recently-downloaded cache
        name = self.getTileName(layerId, z, x, y)
        cacheItem = self.images[0].get(name, None)
        if cacheItem:
        #      print("got tile FROM memory CACHE")
            return cacheItem[0]

        # get the layer object
        layer = self._getLayerById(layerId)
        if layer is None:
            print("mapTiles: invalid layer")
            return None
        if layer is None: # is the layer info valid ?
            print("mapTiles: error: layer with id: %s not found" % layerId)
            return None
        layerPrefix = layer.folderName
        layerType = layer.type
        tileData = self._storeTiles.getTileData(layerPrefix, z, x, y, layerType)
        if tileData:
            #print("got tile FROM disk CACHE")
            # tile was available from storage
            return tileData
        else: # download
            #print("download")
            return self.downloadTile(layerId, z, x, y)

    def downloadTile(self, layerId, z, x, y):
        # get the layer object
        layer = self._getLayerById(layerId)
        if layer is None:
            print("mapTiles: invalid layer")
            return
        if layer is None: # is the layer info valid ?
            print("mapTiles: error: layer with id: %s not found" % layerId)
            return
        layerPrefix = layer.folderName
        layerType = layer.type
        tileUrl = self.getTileUrl(x, y, z, layerId)
        # print("GET TILE")
        # print(tileUrl)
        response = self._getConnPool(layerId, tileUrl).request('GET', tileUrl)
        # print("RESPONSE")
        # print(response)
        tileData = response.data
        if tileData:
            # check if the data is actually an image, and not an error page
            if utils.isTheStringAnImage(tileData):
                tileFolder = self.modrana.paths.getMapFolderPath()
                filePath = os.path.join(tileFolder, self.getImagePath(x, y, z, layerPrefix, layerType))
                self._storeTiles.automaticStoreTile(tileData, layerPrefix, z, x, y, layerType, filePath)
                #        print("STORED")
                return tileData
            else:
                print("mapTiles: tile data returned by remote tileserver was not an image")
                print("NOTE: this probably means that the tileserver returned an"
                      "error page in place of the tile, because it doesn't like you")
                return None
        else:
            return None

    def _getConnPool(self, layerId, baseUrl):
        """get a connection pool for the given layer
        NOTE: connection pools reuse open connections

        :param baseUrl a URL used to initialize the connection pool
        (basically just the domain name needs to be correct)
        """
        pool = self.connPools.get(layerId, None)
        if pool:
            return pool
        else: # create pool
            #headers = { 'User-Agent' : "Mozilla/5.0 (compatible; MSIE 5.5; Linux)" }
            userAgent = self.modrana.configs.getUserAgent()
            headers = {'User-Agent': userAgent}
            newPool = urllib3.connection_from_url(url=baseUrl, headers=headers, maxsize=10, timeout=10, block=False)
            self.connPools[layerId] = newPool
            return newPool

    def addTileDownloadRequest(self, layerId, z, x, y):
        """add a download request to the download manager queue
        the download manager will use its download thread pool to process the request
        NOTE: no checking if tile exists in local storage is done past this point,
        you have to do this beforehand or you might download an already available tile :)"""

        #    print("mapTiles: DOWNLOAD queued")
        name = self.getTileName(layerId, z, x, y)
        # check if the tile is being downloaded
        if name in self.threads or name in self.images[0]:
            return
            # as we check both in thread list and image cache (where download threads deposit tiles) we don't
        # use the corresponding image cache and thread list locks
        # - the window for collision is ver small
        # - possible collisions:
        # -> falsely discarding a request for a thread that actually just errored out
        # -> adding a request for a thread that actually just started (dl manager will kill such requests, np)
        # - so basically nothing serious, also even when ve falsely discard a loading request,
        # it will probably be soon repeated (this is by design to flush the no longer relevant tiles from the
        # download queue)
        layer = self._getLayerById(layerId)
        if layer is None: # is the layer info valid ?
            print("mapTiles: can't add dl request - layerOd not found %s" % layerId)
            return
        layerPrefix = layer.folderName
        layerType = layer.type
        # Are we allowed to download it ? (network=='full')
        # -> no need to submit a download request if network access is disabled
        if self.get('network', 'full') == 'full':
            filename = os.path.join(self._getTileFolderPath(), (self.getImagePath(x, y, z, layerPrefix, layerType)))
            # add tile download request
            with self.threadListCondition:
                timestamp = time.time()
                request = (name, x, y, z, layerId, layerPrefix, layerType, filename, timestamp)
                with self.downloadRequestPoolLock: # add a download request
                    self.downloadRequestPool.append(request)
                self.threadListCondition.notifyAll() # wake up the download manager

    def tileInProgress(self, layerId, z, x, y):
        """report if tile is being downloaded"""
        name = self.getTileName(layerId, z, x, y)
        return name in self.threads

    def tileInMemory(self, layerId, z, x, y):
        """report if tile is stored in memory cache"""
        name = self.getTileName(layerId, z, x, y)
        return name in self.images[0]

    def tileInStorage(self, layerId, z, x, y):
        """report if tile is available from storage"""
        return self._storeTiles.tileExists2(layerId, z, x, y)

    def _updateScalingCB(self, key='mapScale', oldValue=1, newValue=1):
        """as this only needs to be updated once on startup and then only
        when scaling settings change this callback driven method is used"""
        if key == 'mapScale':
            scale = int(newValue)
        else:
            scale = int(self.get('mapScale', 1))
        if scale == 1: # this will be most of the time, so it is first
            z = int(self.get('z', 15))
        elif scale == 2: # tiles are scaled to 512*512 and represent tiles from zl-1
            z = int(self.get('z', 15)) - 1
        elif scale == 4: # tiles are scaled to 1024*1024 and represent tiles from zl-2
            z = int(self.get('z', 15)) - 2
        else:
            z = int(self.get('z', 15))

        tileSide = self.tileSide * scale

        self.scalingInfo = (scale, z, tileSide)

    def startTileDownloadManagementThread(self):
        """start the consumer thread for download requests"""
        t = Thread(target=self.tileDownloadManager, name='automatic tile download management thread')
        t.setDaemon(True) # we need that the worker dies with the program
        t.start()

    def tileDownloadManager(self):
        """this is a tile loading request consumer thread"""
        while True:
            with self.threadListCondition:
                try:
                    # wait for notification that there might be download requests or free download slots
                    self.threadListCondition.wait()
                    if self.shutdownAllThreads:
                        print("\nmapTiles: automatic tile download management thread shutting down")
                        break
                    with self.downloadRequestPoolLock:
                        activeThreads = len(self.threads)
                        maxThreads = int(self.get("maxAutoDownloadThreads2", 10))
                        if activeThreads < maxThreads: # can we start new threads ?
                            # ** there are free download slots **
                            availableSlots = maxThreads - activeThreads
                            #fill all available slots
                            for i in range(0, availableSlots):
                                if self.downloadRequestPool:
                                    request = self.downloadRequestPool.pop() # download most recent requests first
                                    (name, x, y, z, layer, layerPrefix, layerType, filename, timestamp) = request
                                    if name in self.threads.keys():
                                    #                    print("TILE DISCARDED")
                                        continue
                                        # start a new thread
                                    self.threads[name] = self.TileDownloader(name, x, y, z, layer, layerPrefix,
                                                                             layerType, filename, self)
                                    self.threads[name].daemon = True
                                    self.threads[name].start()
                                    if self.cacheImageSurfaces:
                                        # change the status tile to "Downloading..."
                                        if self.cacheImageSurfaces:
                                            with self.imagesLock:
                                                self.images[0][name] = self.downloadingTile
                        else:
                            # ** all download slots are full **
                            # remove old requests
                            currentTime = time.time()
                            cleanPool = []

                            def notOld(currentTime, request):
                                timestamp = request[8]
                                dt = (currentTime - timestamp)
                                return dt < self.downloadRequestTimeout

                            for request in self.downloadRequestPool:
                                if notOld(currentTime, request):
                                    cleanPool.append(request)
                                else:
                                    # this request timed out,
                                    # remove its "Waiting..." tile from image cache,
                                    # so that is can be retried
                                    name = request[0]
                                    self.removeImageFromMemory(name)
                            self.downloadRequestPool = cleanPool
                except Exception:
                    e = sys.exc_info()[1]
                    print("exception in tile download manager thread:\n%s" % e)
                    #          traceback.print_exc()

    def _startIdleTileLoader(self):
        """add the tile loader as a gobject mainloop idle callback"""
        if not self.idleLoaderActive: # one idle loader is enough
            self.idleLoaderActive = True
            gobject.idle_add(self._idleTileLoaderCB)

    def _idleTileLoaderCB(self):
        """get loading requests from the circular stack,
        quit when the stack is empty"""
        try:
            # check for modRana shutdown
            if self.shutdownAllThreads:
                self.idleLoaderActive = False
                return False
            (item, valid) = self.loadRequestCStack.popValid()
            if valid:
                (name, x, y, z, layer) = item
                self.loadImage(name, x, y, z, layer)
                #        print("loaded")
                return True # don't stop the idle handle
            else:
            #        print("quiting")
                self.idleLoaderActive = False
                return False # the stack is empty, remove this callback
        except Exception:
            e = sys.exc_info()[1]
            # on an error, we need to shut down or else idleLoaderActive might get stuck
            # and no loader will be started
            print("mapTiles: exception in idle loader\n", e)
            self.idleLoaderActive = False
            traceback.print_exc()
            return False

    def loadSpecialTiles(self, specialTiles):
        """load special tiles from files to the special tiles cache"""
        for tile in specialTiles:
            (name, path) = tile
            self.loadImageFromFile(path, name, imageType="special", dictIndex=1)

            #  def _checkAutomaticTileDownloads(self):
            #    """monitor if the automatic tile downloads finished and then remove them from the dictionary
            #    (also automagically refreshes the screen once new tiles are available, even when not centered)"""
            #
            #
            #    """seems that some added error handling in the download thread class can replace this,
            #       but it left here for testing purposes"""
            #    z = self.get('z', 15)
            #    """when we change zoomlevel and the number of threads does not change,
            #       we clear the threads set, this is useful, because:
            #       * failed downloads don't accumulate and will be tried again when we visit this zoomlevel again
            #       * tile downloads that don't actually exist (eq tiles from max+1 zoomlevel) don't accumulate
            #       it is important to have the "self.threads" set empty when we are not downloading anything,
            #       because otherwise we are wasting time on the "refresh on finished tile download" logic and also
            #       the set could theoretically cause a memory leak if not periodically cleared from wrong items
            #
            #       this method was chosen instead of a timeout, because it would be hard to set a timeout,
            #       that would work on GPRS and a fast connection
            #    """
            #    if self.oldZ != z:
            ##      print("resetting z")
            #      self.oldZ = z
            #      if len(self.threads) == self.oldThreadCount:
            #        print("clearing thread set")
            #        self.threads = {}
            #        self.oldThreadCount = len(self.threads)
            #    self.oldThreadCount = len(self.threads)

    def beforeDraw(self):
        """we need to synchronize centering with map redraw,
        so we first check if we need to centre the map and then redraw"""
        mapViewModule = self.mapViewModule
        if mapViewModule:
            mapViewModule.handleCentring()

        # tile cache status debugging
        if self.get('reportTileCacheStatus', False): # TODO: set to False by default
            print("** tile cache status report **")
            print("threads: %d, images: %d, special tiles: %d, downloadRequestPool:%d" % (
                len(self.threads), len(self.images[0]), len(self.images[1]), len(self.downloadRequestPool)))

    def drawMap(self, cr):
        """Draw map tile images"""
        try: # this should get rid of a fair share of the infamous "black screens"
            # get all needed data and objects to local variables
            proj = self.m.get('projection', None)
            drawImage = self.drawImage # method binding to speed back method lookup
            overlay = self.get('overlay', False)
            requests = []
            # if overlay is enabled, we use a special naming
            # function in place of the default one

            singleGetName = self.getTileName
            ratio = self.get('transpRatio', "0.5,1").split(',') # get the transparency ratio
            (alphaOver, alphaBack) = (float(ratio[0]), float(ratio[1])) # convert it to floats
            if overlay:
                layer1 = self.get('layer', 'mapnik')
                layer2 = self.get('layer2', 'cycle')
                layerInfo = ((layer1, alphaBack), (layer2, alphaOver))
                getName = self.getCompositeTileName
            else:
                layerInfo = self.get('layer', 'mapnik')
                getName = self.getTileName

            if proj and proj.isValid():
                loadingTileImageSurface = self.loadingTile[0]
                (sx, sy, sw, sh) = self.get('viewport') # get screen parameters

                # adjust left corner coordinates if centering shift is on
                (shiftX, shiftY) = self.modrana.gui.centerShift
                sx = -shiftX
                sy = -shiftY
                # get the current scale and related info
                (scale, z, tileSide) = self.scalingInfo

                if scale == 1: # this will be most of the time, so it is first
                    (px1, px2, py1, py2) = (proj.px1, proj.px2, proj.py1, proj.py2) #use normal projection bbox
                    cleanProjectionCoords = (px1, px2, py1, py2) # we need the unmodified coords for later use
                else:
                    # we use tiles from an upper zl and stretch them over a lower zl
                    (px1, px2, py1, py2) = proj.findEdgesForZl(z, scale)
                    cleanProjectionCoords = (px1, px2, py1, py2) # wee need the unmodified coords for later use

                # upper left tile
                cx = int(px1)
                cy = int(py1)
                # we need the "clean" coordinates for the following conversion
                (px1, px2, py1, py2) = cleanProjectionCoords
                (pdx, pdy) = (px2 - px1, py2 - py1)
                # upper left tile coordinates to screen coordinates
                cx1, cy1 = (sw * (cx - px1) / pdx,
                            sh * (cy - py1) / pdy) #this is basically the pxpy2xy function from mod_projection inlined
                cx1, cy1 = int(cx1), int(cy1)

                if self.get("rotateMap", False) and (self.get("centred", False)):
                    # due to the rotation, the map must be larger
                    # we take the longest side and render tiles in a square

                    # get the rotation angle
                    angle = self.get('bearing', 0.0)
                    if angle is None:
                        angle = 0.0
                        # get the rotation angle from the main class (for synchronization purposes)
                    radAngle = radians(self.modrana.mapRotationAngle)

                    # we use polygon overlap testing to only load@draw visible tiles

                    # screen center point
                    (shiftX, shiftY) = self.modrana.gui.centerShift
                    (centerX, centerY) = ((sw / 2.0), (sh / 2.0))
                    scP = rectangles.Point(centerX, centerY)

                    # create a polygon representing the viewport and rotate around
                    # current rotation center it to match the rotation and align with screen
                    p1 = rectangles.Point(sx, sy)
                    p2 = rectangles.Point(sx + sw, sy)
                    p3 = rectangles.Point(sx, sy + sh)
                    p4 = rectangles.Point(sx + sw, sy + sh)
                    p1 = p1.rotate_about(scP, radAngle)
                    p2 = p2.rotate_about(scP, radAngle)
                    p3 = p3.rotate_about(scP, radAngle)
                    p4 = p4.rotate_about(scP, radAngle)

                    v1 = rectangles.Vector(*p1.as_tuple())
                    v2 = rectangles.Vector(*p2.as_tuple())
                    v3 = rectangles.Vector(*p3.as_tuple())
                    v4 = rectangles.Vector(*p4.as_tuple())
                    polygon = rectangles.Polygon((v1, v2, v3, v4))

                    #          v1 = rectangles.Vector(*p1.as_tuple())
                    #          v2 = rectangles.Vector(*p2.as_tuple())
                    #          v3 = rectangles.Vector(*p3.as_tuple())
                    #          v4 = rectangles.Vector(*p4.as_tuple())

                    # enlarge the area of possibly visible tiles due to rotation
                    add = self.modrana.gui.expandViewportTiles
                    (px1, px2, py1, py2) = (px1 - add, px2 + add, py1 - add, py2 + add)
                    cx = int(px1)
                    cy = int(py1)
                    (pdx, pdy) = (px2 - px1, py2 - py1)
                    cx1, cy1 = (cx1 - add * tileSide, cy1 - add * tileSide)

                    wTiles = len(range(int(floor(px1)), int(ceil(px2)))) # how many tiles wide
                    hTiles = len(range(int(floor(py1)), int(ceil(py2)))) # how many tiles high

                    visibleCounter = 0
                    with self.imagesLock:
                        for ix in range(0, wTiles):
                            for iy in range(0, hTiles):
                                tx = cx + ix
                                ty = cy + iy
                                stx = cx1 + tileSide * ix
                                sty = cy1 + tileSide * iy
                                tv1 = rectangles.Vector(stx, sty)
                                tv2 = rectangles.Vector(stx + tileSide, sty)
                                tv3 = rectangles.Vector(stx, sty + tileSide)
                                tv4 = rectangles.Vector(stx + tileSide, sty + tileSide)
                                tempPolygon = rectangles.Polygon((tv1, tv2, tv3, tv4))
                                if polygon.intersects(tempPolygon):
                                    visibleCounter += 1
                                    (x, y, x1, y1) = (tx, ty, cx1 + tileSide * ix, cy1 + tileSide * iy)
                                    name = getName(layerInfo, z, x, y)
                                    tileImage = self.images[0].get(name)
                                    if tileImage:
                                        # tile found in memory cache, draw it
                                        drawImage(cr, tileImage[0], x1, y1, scale)
                                    else:
                                        if overlay:
                                            # check if the separate tiles are already cached
                                            # and send loading request/-s if not
                                            # if both tiles are in the cache, combine them, cache and display the result
                                            # and remove the separate tiles from cache
                                            layerBack = layerInfo[0][0]
                                            layerOver = layerInfo[1][0]
                                            nameBack = singleGetName(layer1, z, x, y)
                                            nameOver = singleGetName(layer2, z, x, y)
                                            backImage = self.images[0].get(nameBack)
                                            overImage = self.images[0].get(nameOver)
                                            if backImage and overImage: # both images available
                                                if backImage[1]['type'] == "normal" and overImage[1][
                                                    'type'] == "normal":
                                                    combinedImage = self.combine2Tiles(backImage[0], overImage[0],
                                                                                       alphaOver)
                                                    # remove the separate images from cache
                                                    self.removeImageFromMemory(nameBack)
                                                    self.removeImageFromMemory(nameOver)
                                                    # cache the combined image
                                                    self.storeInMemory(combinedImage, name, "composite")
                                                    # draw the composite image
                                                    drawImage(cr, combinedImage, x1, y1, scale)
                                                else:
                                                    drawImage(cr, loadingTileImageSurface, x1, y1, scale)
                                            else:
                                                requests.append((nameBack, x, y, z, layerBack))
                                                requests.append((nameOver, x, y, z, layerOver))
                                                drawImage(cr, loadingTileImageSurface, x1, y1, scale)
                                        else:
                                            # tile not found in memory cache, add a loading request
                                            requests.append((name, x, y, z, layerInfo))
                        gui = self.modrana.gui
                        if gui and gui.getIDString() == "GTK":
                            if gui.getShowRedrawTime():
                                print("currently visible tiles: %d/%d" % (visibleCounter, wTiles * hTiles))

                                #            cr.set_source_rgba(0,1,0,0.5)
                                #            cr.move_to(*p1.as_tuple())
                                #            cr.line_to(*p2.as_tuple())
                                #            cr.line_to(*p4.as_tuple())
                                #            cr.line_to(*p3.as_tuple())
                                #            cr.line_to(*p1.as_tuple())
                                #            cr.close_path()
                                #            cr.fill()
                                #
                                #            cr.set_source_rgba(1,0,0,1)
                                #            cr.rectangle(scP.x-10,scP.y-10,20,20)
                                #            cr.fill()

                else:
                    # draw without rotation
                    wTiles = len(range(int(floor(px1)), int(ceil(px2)))) # how many tiles wide
                    hTiles = len(range(int(floor(py1)), int(ceil(py2)))) # how many tiles high

                    with self.imagesLock: # just one lock per frame
                        # draw the normal layer
                        for ix in range(0, wTiles):
                            for iy in range(0, hTiles):
                                # get tile coordinates by incrementing the upper left tile coordinates
                                x = cx + ix
                                y = cy + iy

                                # get screen coordinates by incrementing upper left tile screen coordinates
                                x1 = cx1 + tileSide * ix
                                y1 = cy1 + tileSide * iy

                                # Try to load and display images
                                name = getName(layerInfo, z, x, y)
                                tileImage = self.images[0].get(name)
                                if tileImage:
                                    # tile found in memory cache, draw it
                                    drawImage(cr, tileImage[0], x1, y1, scale)
                                else:
                                    # tile not found im memory cache, do something else
                                    if overlay:
                                        # check if the separate tiles are already cached
                                        # and send loading request/-s if not
                                        # if both tiles are in the cache, combine them, cache and display the result
                                        # and remove the separate tiles from cache
                                        layerBack = layerInfo[0][0]
                                        layerOver = layerInfo[1][0]
                                        nameBack = singleGetName(layer1, z, x, y)
                                        nameOver = singleGetName(layer2, z, x, y)
                                        backImage = self.images[0].get(nameBack)
                                        overImage = self.images[0].get(nameOver)
                                        if backImage and overImage: # both images available
                                            if backImage[1]['type'] == "normal" and overImage[1]['type'] == "normal":
                                                # we check the the metadata to filter out the "Downloading..."
                                                # special tiles
                                                combinedImage = self.combine2Tiles(backImage[0], overImage[0],
                                                                                   alphaOver)
                                                # remove the separate images from cache
                                                self.removeImageFromMemory(nameBack)
                                                self.removeImageFromMemory(nameOver)
                                                # cache the combined image
                                                self.storeInMemory(combinedImage, name, "composite")
                                                # draw the composite image
                                                drawImage(cr, combinedImage, x1, y1, scale)
                                            else: # on or more tiles not usable
                                                drawImage(cr, loadingTileImageSurface, x1, y1, scale)
                                        else:
                                            requests.append((nameBack, x, y, z, layerBack))
                                            requests.append((nameOver, x, y, z, layerOver))
                                            drawImage(cr, loadingTileImageSurface, x1, y1, scale)
                                    else:
                                        # tile not found in memory cache, add a loading request
                                        requests.append((name, x, y, z, layerInfo))
                                        drawImage(cr, loadingTileImageSurface, x1, y1, scale)

            if requests:
                self.loadRequestCStack.batchPush(requests)
                # can the loadRequestCStack get full ?
                # NO :)
                # it takes the list, reverses it, extends its old internal
                # list with it - from this list a slice conforming to
                # its size limit is taken and set as the new internal list

                # notify the loading thread using the notify Queue
                #        self.loadingNotifyQueue.put("load", block=False)
                # try to start the idle tile loader
                self._startIdleTileLoader()

                #    except Queue.Full:
                #      """as we use the queue as a notification mechanism, we don't actually need to
                #      process all the "load" notifications """
                #      pass

        except Exception:
            e = sys.exc_info()[1]
            print("mapTiles: exception while drawing the map layer: %s" % e)
            traceback.print_exc()

    def drawImage(self, cr, imageSurface, x, y, scale):
        """draw a map tile image"""
        cr.save() # save the cairo projection context
        cr.translate(x, y)
        cr.scale(scale, scale)
        cr.set_source_surface(imageSurface, 0, 0)
        cr.paint()
        cr.restore() # Return the cairo projection to what it was

    def getTileName(self, layerId, z, x, y):
        return "%s_%d_%d_%d" % (layerId, z, x, y)

    def getCompositeTileName(self, layers, z, x, y):
        (layer1, layer2) = layers
        return "%s-%d+%s-%d:%d_%d_%d" % (layer1[0], layer1[1], layer2[0], layer2[1], z, x, y)

    def combine2Tiles(self, backImage, overImage, alphaOver):
        # transparently combine two tiles
        ct = cairo.Context(backImage)
        ct2 = gtk.gdk.CairoContext(ct)
        ct2.set_source_surface(overImage, 0, 0)
        ct2.paint_with_alpha(alphaOver)
        return backImage

    def removeImageFromMemory(self, name, dictIndex=0):
        # remove an image from memory
        if self.cacheImageSurfaces:
            with self.imagesLock: #make sure no one fiddles with the cache while we are working with it
                if name in self.images:
                    del self.images[dictIndex][name]

    def drawCompositeImage(self, cr, nameOver, nameBack, x, y, scale, alpha1=1, alpha2=1, dictIndex1=0, dictIndex2=0):
        """Draw a composited tile image"""

        # Move the cairo projection onto the area where we want to draw the image
        cr.save()
        cr.translate(x, y)
        cr.scale(scale, scale) # scale te tile according to current scale settings

        # Display the image
        cr.set_source_surface(self.images[dictIndex1][nameBack][0], 0, 0) # draw the background
        cr.paint_with_alpha(alpha2)
        cr.set_source_surface(self.images[dictIndex2][nameOver][0], 0, 0) # draw the overlay
        cr.paint_with_alpha(alpha1)

        # Return the cairo projection to what it was
        cr.restore()

    def _fakePrint(self, text):
        """print that does nothing"""
        pass

    def _realPrint(self, text):
        print(text)

    def _getLayerById(self, layerId):
        """Get layer description from the mapLayers module"""
        return self._mapLayersModule.getLayerById(layerId)

    def loadImage(self, name, x, y, z, layerId):
        """Check that an image is loaded, and try to load it if not"""

        # at this point, there is only a placeholder image in the memory cache

        # check if tile loading debugging is on
        debug = self.get('tileLoadingDebug', False)
        if debug:
            sprint = self._realPrint
        else:
            sprint = self._fakePrint

        sprint("###")
        sprint("loading tile %s" % name)

        # first, is it already in the process of being downloaded?
        with self.threadListCondition:
            if name in self.threads.keys():
                sprint("tile is being downloaded")
                if not self.threads[name].finished:
                    with self.imagesLock: # substitute the "loading" tile with a "downloading" tile
                        downloadingTile = self.downloadingTile
                        downloadingTile[1]['addedTimestamp'] = time.time()
                        downloadingTile[1]['type'] = "downloading"

                        self.images[0][name] = downloadingTile
                    return 'OK'

        # second, is it in the disk cache?  (including ones recently-downloaded)
        layerInfo = self._getLayerById(layerId)
        if layerInfo is None: # is the layer info valid
            return 'NOK'

        layerPrefix = layerInfo.folderName
        layerType = layerInfo.type

        start1 = time.clock()
        pixbuf = self._storeTiles.getTile(layerPrefix, z, x, y, layerType)

        # None from getTiles means the tile was not found
        # False means loading the tile from file to pixbuf failed
        if pixbuf:
            start2 = time.clock()
            self.storeInMemory(self.pixbuf2cairoImageSurface(pixbuf), name)
            if debug:
                storageType = self.get('tileStorageType', 'files')
                sprint(
                    "tile loaded from local storage (%s) in %1.2f ms" % (storageType, (1000 * (time.clock() - start1))))
                sprint("tile cached in memory in %1.2f ms" % (1000 * (time.clock() - start2)))
            return 'OK'

        # Image not found anywhere locally - resort to downloading it
        filename = os.path.join(self._getTileFolderPath(), (self.getImagePath(x, y, z, layerPrefix, layerType)))
        sprint("image not found locally - trying to download")

        # Are we allowed to download it ? (network=='full')
        if self.get('network', 'full') == 'full':
            sprint("automatic tile download enabled - starting download")
            # use threads

            # the thread list condition is used to signalize to the download manager,
            # that here is a new download request
            with self.threadListCondition:
                timestamp = time.time()
                request = (name, x, y, z, layerId, layerPrefix, layerType, filename, timestamp)

                with self.imagesLock: # display the "Waiting for download slot..." status tile
                    waitingTile = self.waitingTile
                    waitingTile[1]['addedTimestamp'] = time.time()
                    self.images[0][name] = waitingTile

                with self.downloadRequestPoolLock: # add a download request
                    self.downloadRequestPool.append(request)

                self.threadListCondition.notifyAll() # wake back the download manager
        else:
            sprint("automatic tile download disabled - not starting download")

    def loadImageFromFile(self, path, name, imageType="normal", expireTimestamp=None, dictIndex=0):
        pixbuf = gtk.gdk.pixbuf_new_from_file(path)
        #x = pixbuf.get_width()
        #y = pixbuf.get_height()
        # Google sat images are 256 by 256 px, we don't need to check the size
        x = 256
        y = 256
        # create a new cairo surface to place the image on
        surface = cairo.ImageSurface(0, x, y)
        # create a context to the new surface
        ct = cairo.Context(surface)
        # create a GDK formatted Cairo context to the new Cairo native context
        ct2 = gtk.gdk.CairoContext(ct)
        # draw from the pixbuf to the new surface
        ct2.set_source_pixbuf(pixbuf, 0, 0)
        ct2.paint()
        # surface now contains the image in a Cairo surface
        self.storeInMemory(surface, name, imageType, expireTimestamp, dictIndex)

    def filePath2Pixbuf(self, filePath):
        """return a pixbuf for a given filePath"""
        try:
            pixbuf = gtk.gdk.pixbuf_new_from_file(filePath)
            return pixbuf
        except Exception:
            e = sys.exc_info()[1]
            print("the tile image is corrupted nad/or there are no tiles for this zoomlevel, exception:\n%s" % e)
            return False

    def storeInMemory(self, surface, name, imageType="normal", expireTimestamp=None, dictIndex=0):
        """store a given image surface in the memory image cache
           dictIndex = 0 -> normal map tiles + tile specific error tiles
           dictIndex = 1 -> special tiles that exist in only once in memory and are drawn directly
           (like "Downloading...",Waiting for download slot..:", etc.) """
        metadata = {'addedTimestamp': time.time(), 'type': imageType}
        if expireTimestamp:
            metadata['expireTimestamp'] = expireTimestamp
        with self.imagesLock: #make sure no one fiddles with the cache while we are working with it
            self.images[dictIndex][name] = (surface, metadata) # store the image in memory

            # check cache size,
            # if there are too many images, delete them
            if len(self.images[0]) > self.maxImagesInMemory:
                self.trimCache()
                # new tile available, make redraw request TODO: what overhead does this create ?
            self._tileLoadedNotify(imageType)

    def _tileLoadedNotify(self, imageType):
        """redraw the screen when a new tile is available in the cache
           * redraw only when on map screen (menu == None)
           * redraw only on composite tiles when overlay is on"""
        if self.get('tileLoadedRedraw', True) and self.get('menu', None) is None:
            overlay = self.get('overlay', False)
            if overlay: # only redraw when a composited tile is loaded with overlay on
                if imageType == "composite":
                    self.set('needRedraw', True)
            else: # redraw regardless of type with overlay off
                self.set('needRedraw', True)

    def trimCache(self):
        """to avoid a memory leak, the maximum size of the image cache is fixed
           when we reach the maximum size, we start removing images,
           starting from the oldest ones
           we an amount of images specified in imagesTrimmingAmount,
           so that trim does not run every time an image is added to a full cache
           -> only the normal image cache needs trimming (images[0]),
           as the special image cache (images[1]) is just created once and not updated dynamically
           NOTE: the storeInMemory method already locked images, so we don't have to"""
        trimmingAmount = self.imagesTrimmingAmount
        imagesLength = len(self.images[0])
        if trimmingAmount >= imagesLength:
            # this means that the trimming amount was set higher,
            # than current length of the cache
            # the result is basically flushing the cache every time it fills back
            # well, I don't have an idea why would someone want to do that
            self.images[0] = {}
        else:
            oldestKeys = sorted(self.images[0], key=lambda image: self.images[0][image][1]['addedTimestamp'])[
                         0:trimmingAmount]
            for key in oldestKeys:
                del self.images[0][key]

    def _clearTileCache(self):
        """completely clear the in-memory image cache"""
        print('mapTiles: clearing the in-memory tile cache')
        self.images[0] = {}

    def pixbuf2cairoImageSurface(self, pixbuf):
        # this solution has been found on:
        # http://www.ossramblings.com/loading_jpg_into_cairo_surface_python

        # NOTE: Using pixbufs in place of surface_from_png seems to be MUCH faster
        # for JPEGSs and PNGs alike, therefore we use it as default

        # do any filtering on the pixbuf
        pixbuf = self._filterTile(pixbuf)

        # Tile images are mostly 256 by 256 px, we don't need to check the size
        x = 256
        y = 256
        # create a new cairo surface to place the image on '''
        surface = cairo.ImageSurface(0, x, y)
        # create a context to the new surface
        ct = cairo.Context(surface)
        # create a GDK formatted Cairo context to the new Cairo native context
        ct2 = gtk.gdk.CairoContext(ct)
        # draw from the pixbuf to the new surface
        ct2.set_source_pixbuf(pixbuf, 0, 0)
        ct2.paint()
        return surface

    def _updateTileFilteringCB(self, key='mapScale', oldValue=1, newValue=1):
        if key == 'invertMapTiles':
            if newValue == True:
                self._enableTileFiltering()
            elif newValue == False:
                self._disableTileFiltering()
            elif newValue == "withNightTheme":
                theme = self.get('currentTheme', 'default')
                # TODO: get this from theme config
                if theme == "night":
                    self._enableTileFiltering()
                else:
                    self._disableTileFiltering()
        elif key == "currentTheme":
            invertMapTiles = self.get('invertMapTiles', False)
            if invertMapTiles == "withNightTheme":
                # if switching from night to other -> disable
                if oldValue == "night" and newValue != "night":
                    self._disableTileFiltering()
                # switching from other to night -> enable
                elif oldValue != "night" and newValue == "night":
                    self._enableTileFiltering()
                    # else: switching form some other theme to another theme
                    # -> do nothing

    def _enableTileFiltering(self):
        """assign the real filtering method, if possible
        and flush the cache afterwards"""
        if IMAGE_MANIPULATION_IMPORT_SUCCESS:
            self._filterTile = self._invertPixbuf
            self._clearTileCache()

    def _disableTileFiltering(self):
        """assign the NOP filtering method
        and flush the cache if needed"""
        if IMAGE_MANIPULATION_IMPORT_SUCCESS:
            self._filterTile = self._nop
            # as image manipulation is possible,
            # a cache flush is needed
            self._clearTileCache()

    def _filterTile(self, tilePb):
        """function hook for image tile processing"""
        return tilePb

    def _nop(self, arg):
        """a NOP function used for replacing functions that are not
        currently used for some reason (such as for example _invertPixbuf)"""
        return arg

    def _invertPixbuf(self, pixbuf):
        """do image inversion for the given pixbuf
        - why PIL & Numpy -> combined, they give usable performance
        (pure python implementation was about 100x times slower
        10 vs 1000 ms per tile)"""

        #    start1 = time.clock()
        def pixbuf2Image(pb):
            return Image.fromstring("RGB", (256, 256), pb.get_pixels())

        def image2pixbuf(im):
            file1 = StringIO()
            im.save(file1, "ppm")
            contents = file1.getvalue()
            file1.close()
            loader = gtk.gdk.PixbufLoader("pnm")
            loader.write(contents, len(contents))
            pixbuf = loader.get_pixbuf()
            loader.close()
            return pixbuf

            #  arr = numpy.array(im)
        #  return gtk.gdk.pixbuf_new_from_array(arr, gtk.gdk.COLORSPACE_RGB, 8)
        # Why are we using StringIO here ?
        #
        # The above mentioned method works just fine with recent GTK2 on PC
        # but doesn't work with the highly patched and old version of GTK on
        # Maemo 5 fremantle.
        # Other than that, even on the N900 StringIO seems to still be really fast
        # so it is used even on desktop, eliminating the Numpy dependency.
        # Also "premature optimization" and all that. :)

        image = pixbuf2Image(pixbuf)
        image = ImageOps.invert(image)
        return image2pixbuf(image)

    #    print("tile negative in %1.2f ms" % (1000 * (time.clock() - start1)))

    def imageName(self, x, y, z, layer):
        """Get a unique name for a tile image
        (suitable for use as part of filenames, dictionary keys, etc)"""
        return "%s_%d_%d_%d" % (layer, z, x, y)

    def getImagePath(self, x, y, z, prefix, extension):
        """Get a unique name for a tile image
        (suitable for use as part of filenames, dictionary keys, etc)"""
        #    return("%s/%d/%d/%d.%s" % (prefix,z,x,y,extension))
        return os.path.join(prefix, str(z), str(x), "%d.%s" % (y, extension))

    def getImageFolder(self, x, z, prefix):
        """Get a unique name for a tile image
        (suitable for use as part of filenames, dictionary keys, etc)"""
        return os.path.join(prefix, str(z), str(x))

    def _getTileFolderPath(self):
        """helper function that returns path to the tile folder"""
        return self.mapFolderPath

    def imageY(self, z, extension):
        return '%d.%s' % (z, extension)

    def getTileUrl(self, x, y, z, layerId):
        """Return url for given tile coordinates and layer"""
        layer = self._getLayerById(layerId)
        if layer is None:
            return None
        coords = layer.coordinates
        if coords == 'google':
            url = '%s&x=%d&y=%d&z=%d' % (
                layer.url,
                x, y, z)
        elif coords == 'web_mercator_substitution':
            template = string.Template(layer.url)
            url = str(template.substitute(z=z, x=x, y=y))
        elif coords == 'quadtree_substitution': # handle Virtual Earth with substitution
            quadKey = quadTree(x, y, z)
            template = string.Template(layer.url)
            url = str(template.substitute(quadindex=quadKey))

        # the "quadtree" method is depreciated by quadtree_substitution
        # , drop this some time in the future
        elif coords == 'quadtree': # handle Virtual Earth maps and satellite
            quadKey = quadTree(x, y, z)
            #  don't know what the g argument is, maybe revision ? but its not optional
            url = '%s%s?g=452' % ( layer.url, quadKey )
        elif coords == 'yahoo': # handle Yahoo maps, sat, overlay
            y = ((2 ** (z - 1) - 1) - y)
            z += 1
            # I have no idea what the r parameter is, r=0 or no r => grey square
            url = '%s&x=%d&y=%d&z=%d&r=1' % (layer.url, x, y, z)
        #    elif coords == 'chartbundle': # chartbundle
        ##      print("CHARTBUNDLE")
        #      y = ((2 ** (z - 1) - 1) - y)
        #      # TODO: fix projection so this is usable
        #      # NOTE: looks like with the y fix from Yahoo tilenames,
        #      # the map is drawn correctly, but current position is somewhere in Antarctica
        #      # -> thi probably means some projection lat lon -> x y errors for this layer
        #
        #      url = '%s%d/%d/%d.%s' % (
        #      layerDetails['tiles'],
        #      z, x, y,
        #      layerDetails.get('type', 'png'))
        else: # OSM, Open Cycle, T@H -> equivalent to coords == osm
            url = '%s%d/%d/%d.%s' % (layer.url, z, x, y, layer.type)

        #    print("__%s__" % coords)
        #     print("TILE URL: %s" % url)
        return url

    def shutdown(self):
        # shutdown the worker/consumer threads
        self.shutdownAllThreads = True

        #    # shutdown the tile loading thread
        #    try:
        #      self.loadingNotifyQueue.put(('shutdown', ()),block=False)
        #    except Queue.Full:
        #      """the tile loading thread is demonic, so it will be still killed in the end"""
        #      pass
        # notify the automatic tile download manager thread about the shutdown
        with self.threadListCondition:
            self.threadListCondition.notifyAll()

    class TileDownloader(Thread):
        """Downloads an image (in a thread)"""

        def __init__(self, name, x, y, z, layerId, layerName, layerType, filename, callback):
            Thread.__init__(self)
            self.name = name
            self.x = x
            self.y = y
            self.z = z
            self.layerId = layerId
            self.layerName = layerName
            self.layerType = layerType
            self.finished = 0
            self.filename = filename
            self.callback = callback
            self.useImageSurface = callback.cacheImageSurfaces

        def run(self):
            try:
                self.downloadTile(
                    self.name,
                    self.x,
                    self.y,
                    self.z,
                    self.layerId,
                    self.filename)
                self.finished = 1
            # something is wrong with the server or url
            except urllib3.exceptions.HTTPError:
                if self.useImageSurface:
                    tileDownloadFailedSurface = self.callback.images[1]['tileDownloadFailed'][0]
                    expireTimestamp = time.time() + 10
                    self.callback.storeInMemory(tileDownloadFailedSurface, self.name, 'semiPermanentError',
                                                expireTimestamp)
                    # like this, when tile download fails due to a http error,
                    # the error tile is loaded instead
                    # like this:
                    #  - modRana does not immediately try to download a tile that errors out
                    #  - the error tile is shown without modifying the pipeline too much
                    #  - modRana will eventually try to download the tile again,
                    #    after it is flushed with old tiles from the memory
            except URLError:
                if self.useImageSurface:
                    tileNetworkErrorSurface = self.callback.images[1]['tileNetworkError'][0]
                    expireTimestamp = time.time() + 10
                    self.callback.storeInMemory(tileNetworkErrorSurface, self.name, 'error',
                                                expireTimestamp) # retry after 10 seconds
                    # as not to DOS the system when we temporarily loose internet connection or other such error occurs,
                    # we load a temporary error tile with expiration timestamp instead of the tile image
                    # TODO: actually remove tiles according to expiration timestamp :)

            # something other is wrong (most probably a corrupted tile)
            except Exception:
                e = sys.exc_info()[1]
                self.printErrorMessage(e)
                # remove the status tile
                self.callback.removeImageFromMemory(self.name)

            finally: # make really sure we don't get any zombie threads
                self.finished = 1 # finished thread can be removed from the set and retried
                self.removeSelf()

        def removeSelf(self):
            with self.callback.threadListCondition:
                # try to remove its own instance from the thread list, so that the instance could be garbage collected
                if self.name in self.callback.threads.keys():
                    del self.callback.threads[self.name]
                    # notify the download manager that a download slot is now free
                    self.callback.threadListCondition.notifyAll()

        def printErrorMessage(self, e):
            url = self.callback.getTileUrl(self.x, self.y, self.z, self.layerId)
            print("mapTiles: download thread reports error")
            print("** we were doing this, when an exception occurred:")
            print("** downloading tile: x:%d,y:%d,z:%d, layer:%s, filename:%s, url: %s" % (
                self.x,
                self.y,
                self.z,
                self.layerId,
                self.filename,
                url))
            print("** this exception occurred: %s\n" % e)
            print("** traceback:\n")
            traceback.print_exc()

        def downloadTile(self, name, x, y, z, layerId, filename):
            """Downloads an image"""
            content = self.callback.downloadTile(layerId, z, x, y)
            if content is None:
                raise urllib3.exceptions.HTTPError
            if self.useImageSurface:
                pl = gtk.gdk.PixbufLoader()

                pl.write(content)

                pl.close() # this  blocks until the image is completely loaded
                # http://www.ossramblings.com/loading_jpg_into_cairo_surface_python
                surface = self.callback.pixbuf2cairoImageSurface(pl.get_pixbuf())
                self.callback.storeInMemory(surface, name)
                # like this, corrupted tiles should not get past the pixbuf loader and be stored
            else:
                # cache the raw data
                self.callback.storeInMemory(content, name)

            m = self.callback._storeTiles
            if m:
                m.automaticStoreTile(content, self.layerName, self.z, self.x, self.y, self.layerType, filename)

# modified from: http://www.maptiler.org/google-maps-coordinates-tile-bounds-projection/globalmaptiles.py (GPL)
def quadTree(tx, ty, zoom):
    """Converts OSM type tile coordinates to Microsoft QuadTree"""
    quadKey = ""
    #		ty = (2**zoom - 1) - ty
    for i in range(zoom, 0, -1):
        digit = 0
        mask = 1 << (i - 1)
        if (tx & mask) != 0:
            digit += 1
        if (ty & mask) != 0:
            digit += 2
        quadKey += str(digit)
    return quadKey
