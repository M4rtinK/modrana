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
import threading
import os
import time
import sys
import traceback

try:  # Python 2
    from urllib2 import urlopen, HTTPError, URLError
except ImportError:  # Python 3
    from urllib.request import urlopen
    from urllib.error import HTTPError, URLError

if sys.version_info[:2] <= (2, 5):
    from core.backports import urllib3_python25 as urllib3
else:
    import urllib3
from core import utils
from core import rectangles
from core import tiles
from core import constants
from core.tilenames import *
from core.backports import six
from core.signal import Signal
from core import threads

from .tile_downloader import Downloader

StringIO = six.moves.cStringIO

#import socket
#timeout = 30 # this sets timeout for all sockets
#socket.setdefaulttimeout(timeout)

import logging
log = logging.getLogger("mod.mapTiles")

# if image manipulation tools are available, import them
# and otherwise disable tile image manipulation
IMAGE_MANIPULATION_IMPORT_SUCCESS = False
NORMAL_TILE = "normal"
LOADING_TILE = "loadingTile"
COMPOSITE_TILE = "composite"
SPECIAL_TILE = "special"

# only import GKT libs if GTK GUI is used
from core import gs

if gs.GUIString == "GTK":
    import gtk
    import cairo

    # as the image manipulation is dependent on GTK being
    # used, only load it if using the GTK GUI
    try:
        import Image
        import ImageOps

        IMAGE_MANIPULATION_IMPORT_SUCCESS = True
    except ImportError:
        log.warning('import of image manipulation tools unsuccessful'
                    ' - tile image manipulation disabled')

TERMINATOR = object()

def getModule(*args, **kwargs):
    return MapTiles(*args, **kwargs)

class MapTiles(RanaModule):
    """Display map images"""


    # TILE COORDINATES
    # - layer, Z, X, Y tuples are used !
    # - they should be called lzxy
    # - basically the same zxy order as with normal
    #   web mercator tile coordinates


    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self.images = [{}, {}] # the first dict contains normal image data, the second contains special tiles
        self.imagesLock = threading.RLock()
        # we need to limit the size of the tile cache to avoid a memory leak
        memoryTileCacheSize = int(self.get("memoryTileCacheSize", constants.DEFAULT_MEMORY_TILE_CACHE_SIZE))
        self.log.info("in memory tile cache size: %d", memoryTileCacheSize)
        self.maxImagesInMemory = memoryTileCacheSize
        self.imagesTrimmingAmount = constants.DEFAULT_MEMORY_TILE_CACHE_TRIM_SIZE
        # how many tiles to remove once the maximum is reached
        # so that trim does not run always run after adding a tile
        # TODO: analyse memory usage,
        #       set appropriate value,
        #       platform dependent value,
        #       user configurable
        self.tileSide = 256 # by default, the tiles are squares, side=256
        self.scalingInfo = (1, 15, 256)
        self.downloadRequestTimeout = 30 # in seconds

        specialTiles = [
            ('tileDownloading', 'themes/default/tile_downloading.png'),
            ('tileDownloadFailed', 'themes/default/tile_download_failed.png'),
            ('tileLoading', 'themes/default/tile_loading.png'),
            ('tileWaitingForDownloadSlot', 'themes/default/tile_waiting_for_download_slot.png'),
            ('tileNetworkError', 'themes/default/tile_network_error.png')
        ]

        if gs.GUIString == "GTK":
            self._loadSpecialTiles(specialTiles) # load the special tiles to the special image cache
            self.loadingTile = self.images[1]['tileLoading']
            self.downloadingTile = self.images[1]['tileDownloading']
            self.waitingTile = self.images[1]['tileWaitingForDownloadSlot']

        self.mapViewModule = None
        self._mapLayersModule = None

        # cache the map folder path
        self.mapFolderPath = self.modrana.paths.getMapFolderPath()
        self.log.info("map folder path: %s" % self.mapFolderPath)

        self._storeTiles = None

        self.connPools = {} # connection pool dictionary

        self.cacheImageSurfaces = gs.GUIString == "GTK"

        self._filterTile = self._nop

        self._tileDownloaded = Signal()

        self._dlRequestQueue = six.moves.queue.Queue()
        self._downloader = None

        if gs.GUIString == "GTK":
            # The in memory tile cache clearing watches
            # are only relevant for the GTK GUI as only the GTK GUI
            # stores special anc composite tiles in the cache.
            # The Qt 5 GUI only uses it as a raw in memory tile cache and does not
            # need it to remove tiles other than the automatic cache size
            # trimming that occurs when the hard cache size limit is reached.
            self.modrana.watch("layer", self._mapStateChangedCB)
            self.modrana.watch("layer2", self._mapStateChangedCB)
            self.modrana.watch("overlay", self._mapStateChangedCB)
            self.modrana.watch("network", self._mapStateChangedCB)

    @property
    def tileDownloaded(self):
        return self._tileDownloaded

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

        maxThreads = int(self.get("maxAutoDownloadThreads2",
                                  constants.DEFAULT_THREAD_COUNT_AUTOMATIC_TILE_DOWNLOAD))
        taskQueueSize = int(self.get("autoDownloadQueueSize",
                                     constants.DEFAULT_AUTOMATIC_TILE_DOWNLOAD_QUEUE_SIZE))
        self.log.debug("automatic tile download queue size: %d", taskQueueSize)
        self._downloader = Downloader(maxThreads,
                                      taskBufferSize=taskQueueSize)
        self._startTileLoadingManager()

        if gs.GUIString == "GTK":
            self.m.get("mapData").downloadPool.batchDone.connect(self._batchDownloadCompleteDB)

    def getTile(self, lzxy, async=False, tag=None, download=True):
        """Return a tile specified by layerID, z, x & y
        * first look if such a tile is available from cache
          or persistent storage
        * if not, download it

        :param tuple lzxy: tile description tuple
        :returns: tile data or None
        :rtype: data or None
        """
        # check if the tile is in the recently-downloaded cache
        cacheItem = self.images[0].get(lzxy, None)
        if cacheItem:
        #      self.log.debug("got tile FROM memory CACHE")
            return cacheItem[0]

        tileData = self._storeTiles.get_tile_data(lzxy)
        if tileData:
            #self.log.debug("got tile FROM disk CACHE")
            # tile was available from storage
            return tileData
        if download:
            if async:
                # asynchronous download
                #self.log.debug("DOWNLOADING tile asynchronously!")
                self.addTileDownloadRequest(lzxy, tag)
                return None
            else:
                # synchronous download
                #self.log.debug("DOWNLOADING tile synchronously!")
                # tile was not available from storage, download it
                return self._downloadTile(lzxy)
        else:
            return None

    def _downloadTile(self, lzxy):
        """Download the a tile from the network

        :param tuple lzxy: tile description tuple
        :returns: tile data or None
        :rtype: data or None
        """

        tileUrl = tiles.getTileUrl(lzxy)
        # self.log.debug("GET TILE")
        # self.log.debug(tileUrl)
        response = self._getConnPool(lzxy[0].id, tileUrl).request('GET', tileUrl)
        # self.log.debug("RESPONSE")
        # self.log.debug(response)
        tileData = response.data
        if tileData:
            # check if the data is actually an image, and not an error page
            if utils.isTheStringAnImage(tileData):
                self._storeTiles.store_tile_data(lzxy, tileData)
                #        self.log.debug("STORED")
                return tileData
            else:
                msg = "tile data returned by remote tileserver was not an image\n"
                msg+= "layer:%s z:%d x:%d y:%d\n" % (lzxy[0].id, lzxy[1], lzxy[2], lzxy[3])
                msg+= "tile url: %s\n" % tileUrl
                msg+= "NOTE: this probably means that the tileserver returned an\n"
                msg+= "error page in place of the tile, because it doesn't like you\n"
                self.log.warning(msg)
                return None
        else:
            return None

    def _getConnPool(self, layerId, baseUrl):
        """Get a connection pool for the given layer id
        Each layer ID has it's own connection pool
        (as each connection pool handles only one base URL)
        and non-existent pools are automatically created once requested
        NOTE: connection pools reuse open connections

        :param str layerId: pool id (mapped to layer id)
        :param str baseUrl: a URL used to initialize the connection pool
                           (basically just the domain name needs to be correct)
        """
        pool = self.connPools.get(layerId, None)
        if pool:
            return pool
        else: # create pool
            #headers = { 'User-Agent' : "Mozilla/5.0 (compatible; MSIE 5.5; Linux)" }
            userAgent = self.modrana.configs.user_agent
            headers = {'User-Agent': userAgent}
            newPool = urllib3.connection_from_url(url=baseUrl, headers=headers, maxsize=10, timeout=10, block=False)
            self.connPools[layerId] = newPool
            return newPool

    def addTileDownloadRequest(self, lzxy, tag=None):
        """Add a download request to the download manager queue
        the download manager will use its download thread pool to process the request
        NOTE: this does not check if the tile is cached or available from storage,
              but the download pool workers will not download tiles that are available
              from storage once the request gets to them

        :param tuple lzxy: tile description tuple
        """
        self._dlRequestQueue.put([(lzxy, tag)])

    def tileInMemory(self, lzxy):
        """Report if a tile is stored in memory cache

        NOTE: the image cache is periodically scrubbed once it becomes
              full, so even if this function reports a tile is in cache
              it might get trimmed right after

        :returns: True if tile is cached, False otherwise
        :rtype: bool
        """
        return lzxy in self.images[0]

    def tileInStorage(self, lzxy):
        """Report if tile is available from local persistent storage

        :returns: True if tile is in storage, False otherwise
        :rtype: bool
        """
        return self._storeTiles.tile_is_stored(lzxy)

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

    def _startTileLoadingManager(self):
        """Start the consumer thread for download requests"""
        t = threads.ModRanaThread(name=constants.THREAD_TILE_DOWNLOAD_MANAGER,
                                  target = self._tileLoadingManager)
        threads.threadMgr.add(t)


    def _tileLoadingManager(self):
        """This function is run by the tile loading request manager thread,
        it handles both loading of tiles from local storage to the image cache
        and submitting download requests for tiles that were not found locally.
        """
        while True:
            request = self._dlRequestQueue.get(block=True)
            if request == TERMINATOR:
                self.log.info("automatic tile download management thread shutting down")
                break
            try:
                for item in request:
                    lzxy, tag = item
                    # first check if the tile is locally available and load it
                    # to the image cache if it is

                    # check if tile loading debugging is on
                    # TODO: use a watch on the loading debug key
                    debug = self.get('tileLoadingDebug', False)
                    if debug:
                        sprint = self._realDebugLog
                    else:
                        sprint = self._fakeDebugLog
                    sprint("looking for tile %s", lzxy)
                    tileData = self._storeTiles.get_tile_data(lzxy)
                    if not tileData:  # TODO: is this actually needed ?
                        sprint("tile not found locally %s", lzxy)
                        # tile not found locally and needs to be downloaded from network
                        # Are we allowed to download it ? (network=='full')
                        if self.get('network', 'full') == 'full':
                            sprint("auto tile dl enabled - adding dl request for %s", lzxy)
                            # switch the status tile to "Waiting for download slot"
                            if self.cacheImageSurfaces:
                                with self.imagesLock:
                                    self.images[0][lzxy] = self.waitingTile
                            droppedRequest = self._downloader.downloadTile(lzxy, tag)
                            if droppedRequest:
                                # this tile download request has been dropped from
                                # the bottom of the request stack, remove its
                                #  "Waiting..." tile from image cache
                                # - if it is not in view, this makes place for new tiles in cache,
                                # - if it is in view, new download request will be added
                                lzxy, tag = droppedRequest
                                sprint("old download request dropped from work request stack: %s", lzxy)
                                self.removeImageFromMemory(lzxy)
                                # also notify any listener that tha tile has been processed
                                self.tileDownloaded(constants.TILE_DOWNLOAD_QUEUE_FULL, droppedRequest[0], droppedRequest[1])
                        else:
                            sprint("auto tile dl disabled - not adding dl request for %s", lzxy)
                    else:
                        # tile found locally and not downloaded, trigger the downloaded signal
                        sprint("%s found locally", lzxy)
                        self.tileDownloaded(constants.TILE_DOWNLOAD_SUCCESS, lzxy, tag)
                        # and cache it in memory
                        if self.cacheImageSurfaces:
                            # if we are using image surfaces, convert the raw image data
                            # into an image surface
                            tileData = self._data2cairoImageSurface(tileData)
                        self.storeInMemory(tileData, lzxy)
            except Exception:
                self.log.exception("exception in tile download manager thread")

    def _loadSpecialTiles(self, specialTiles):
        """Load special tiles from files to the special tile cache

        :param list specialTiles: list of special tiles to load
        """
        for tile in specialTiles:
            (name, path) = tile
            self._loadImageFromFile(path, name, imageType=SPECIAL_TILE, dictIndex=1)

    def beforeDraw(self):
        """We need to synchronize centering with map redraw,
        so we first check if we need to centre the map and then redraw"""

        # TODO: don't redraw the ma layer if it is tha same
        # (viewport, map center, zoomlevel and layer are the same)

        mapViewModule = self.mapViewModule
        if mapViewModule:
            mapViewModule.handleCentring()

        # tile cache status debugging
        if self.get('reportTileCacheStatus', False): # TODO: set to False by default
            self.log.debug("** tile cache status report **")
            self.log.debug("threads: %d, images: %d, special tiles: %d, dl request queue:%d" % (
                self._downloader.maxThreads, len(self.images[0]), len(self.images[1]), self._downloader.qsize))

    def drawMap(self, cr):
        """Draw map tile images"""
        try: # this should get rid of a fair share of the infamous "black screens"
            # get all needed data and objects to local variables
            proj = self.m.get('projection', None)
            drawImage = self._drawImage # method binding to speed back method lookup
            overlay = self.get('overlay', False)
            requests = []
            # if overlay is enabled, we use a special naming
            # function in place of the default one
            # -> like this we don't need additional
            #    overlay/no-overlay branching

            ratio = self.get('transpRatio', "0.5,1").split(',') # get the transparency ratio
            (alphaOver, alphaBack) = (float(ratio[0]), float(ratio[1])) # convert it to floats
            # TODO: cache current layers
            if overlay:
                layer1 = self._mapLayersModule.getLayerById(self.get('layer', 'mapnik'))
                layer2 = self._mapLayersModule.getLayerById(self.get('layer2', 'cycle'))
                layerInfo = ((layer1, alphaBack), (layer2, alphaOver))
            else:
                layerInfo = self._mapLayersModule.getLayerById(self.get('layer', 'mapnik'))

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
                                    name = (layerInfo, z, x, y)
                                    tileImage = self.images[0].get(name)
                                    if tileImage:
                                        # tile found in memory cache, draw it
                                        drawImage(cr, tileImage[0], x1, y1, scale)
                                    else:
                                        # tile not found in memory cache - submit tile loading request
                                        # and draw loading tile
                                        if overlay:
                                            # check if the separate tiles are already cached
                                            # and send loading request/-s if not
                                            # if both tiles are in the cache, combine them, cache and display the result
                                            # and remove the separate tiles from cache
                                            layerBack = layerInfo[0][0]
                                            layerOver = layerInfo[1][0]
                                            nameBack = (layer1, z, x, y)
                                            nameOver = (layer2, z, x, y)
                                            backImage = self.images[0].get(nameBack)
                                            overImage = self.images[0].get(nameOver)
                                            if backImage and overImage: # both images available
                                                # we check the the metadata to filter out the "Downloading... special tiles
                                                if backImage[1]['type'] == "normal" and overImage[1]['type'] == "normal":
                                                    # if both tiles are available, combine them remove the old tiles and cache the new one
                                                    drawImage(cr, self._combine2Tiles(name, backImage[0], nameBack, overImage[0], nameOver, alphaOver), x1, y1, scale)
                                                else: # on or more tiles not usable
                                                    # so at least draw a combined image
                                                    self._drawCompositeImage(cr, backImage[0], overImage[0], x1, y1, scale, alpha1=alphaOver)
                                            else:
                                                if backImage:
                                                    requests.append(((layerBack, z, x, y), None))
                                                    self.storeInMemory(loadingTileImageSurface, nameBack, imageType=LOADING_TILE)
                                                elif overImage:
                                                    requests.append(((layerOver, z, x, y), None))
                                                    self.storeInMemory(loadingTileImageSurface, nameOver, imageType=LOADING_TILE)
                                                else:
                                                    requests.append(((layerBack, z, x, y), None))
                                                    requests.append(((layerOver, z, x, y), None))
                                                drawImage(cr, loadingTileImageSurface, x1, y1, scale)
                                        else:
                                            # tile not found in memory cache, add a loading request
                                            requests.append(((layerInfo, z, x, y), None))
                                            # and cache a loading tile so that we don't spam the same loading r
                                            # request over and over again (the tile request queue is using a stack,
                                            # so this would really not make sense)
                                            self.storeInMemory(loadingTileImageSurface, name, imageType=LOADING_TILE)
                                            drawImage(cr, loadingTileImageSurface, x1, y1, scale)

                        gui = self.modrana.gui
                        if gui and gui.getIDString() == "GTK":
                            if gui.getShowRedrawTime():
                                self.log.debug("currently visible tiles: %d/%d" % (visibleCounter, wTiles * hTiles))

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
                                name = (layerInfo, z, x, y)
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
                                        nameBack = (layer1, z, x, y)
                                        nameOver = (layer2, z, x, y)
                                        backImage = self.images[0].get(nameBack)
                                        overImage = self.images[0].get(nameOver)
                                        if backImage and overImage: # both images available
                                            # we check the the metadata to filter out the "Downloading..." special tiles
                                            if backImage[1]['type'] == "normal" and overImage[1]['type'] == "normal":
                                                # if both tiles are available, combine them remove the old tiles and cache the new one
                                                drawImage(cr, self._combine2Tiles(name, backImage[0], nameBack, overImage[0], nameOver, alphaOver), x1, y1, scale)
                                            else: # on or more tiles not usable
                                                # so at least draw a combined image
                                                self._drawCompositeImage(cr, backImage[0], overImage[0], x1, y1, scale, alpha1=alphaOver)
                                        else:
                                            if backImage:
                                                requests.append(((layerBack, z, x, y), None))
                                                self.storeInMemory(loadingTileImageSurface, nameBack, imageType=LOADING_TILE)
                                            elif overImage:
                                                requests.append(((layerOver, z, x, y), None))
                                                self.storeInMemory(loadingTileImageSurface, nameOver, imageType=LOADING_TILE)
                                            else:
                                                requests.append(((layerBack, z, x, y), None))
                                                requests.append(((layerOver, z, x, y), None))
                                            drawImage(cr, loadingTileImageSurface, x1, y1, scale)
                                    else:
                                        # tile not found in memory cache, add a loading request
                                        requests.append(((layerInfo, z, x, y), None))
                                        # and cache a loading tile so that we don't spam the same loading r
                                        # request over and over again (the tile request queue is using a stack,
                                        # so this would really not make sense)
                                        self.storeInMemory(loadingTileImageSurface, name, imageType=LOADING_TILE)
                                        drawImage(cr, loadingTileImageSurface, x1, y1, scale)
            if requests:
                self._dlRequestQueue.put(requests)

        except:
            self.log.exception("mapTiles: exception while drawing the map layer")

    def _drawImage(self, cr, imageSurface, x, y, scale):
        """draw a map tile image"""
        cr.save() # save the cairo projection context
        cr.translate(x, y)
        cr.scale(scale, scale)
        cr.set_source_surface(imageSurface, 0, 0)
        cr.paint()
        cr.restore() # Return the cairo projection to what it was

    def _combine2Tiles(self, name, backImage, nameBack, overImage, nameOver, alphaOver):
        # transparently combine two tiles
        # WARNING: this modifies the backImage ImageSurface !

        # combine the two images
        ct = cairo.Context(backImage)
        ct2 = gtk.gdk.CairoContext(ct)
        ct2.set_source_surface(overImage, 0, 0)
        ct2.paint_with_alpha(alphaOver)

        #drop the two individual images
        # remove the separate images from cache
        self.removeImageFromMemory(nameBack)
        self.removeImageFromMemory(nameOver)
        # cache the combined image
        self.storeInMemory(backImage, name, imageType=COMPOSITE_TILE)
        # return the composite image
        return backImage

    def removeImageFromMemory(self, name, dictIndex=0):
        """Remove a tile from the in memory tile cache"""

        # remove an image from memory
        if self.cacheImageSurfaces:
            # make sure no one fiddles with the cache while we are working with it
            with self.imagesLock:
                if name in self.images[dictIndex]:
                    del self.images[dictIndex][name]
                else:
                    self.log.debug("can't remove unknown %s from memory tile cache", name)

    def _drawCompositeImage(self, cr, backImage, overImage, x, y, scale, alpha1=1.0, alpha2=1.0, dictIndex1=0, dictIndex2=0):
        """Draw a composited tile image"""

        # Move the cairo projection onto the area where we want to draw the image
        cr.save()
        cr.translate(x, y)
        cr.scale(scale, scale) # scale te tile according to current scale settings

        # Display the image
        cr.set_source_surface(backImage, 0, 0) # draw the background
        cr.paint_with_alpha(alpha2)
        cr.set_source_surface(overImage, 0, 0) # draw the overlay
        cr.paint_with_alpha(alpha1)

        # Return to the cairo projection to what it was before
        cr.restore()

    def _fakeDebugLog(self, *argv):
        """Log function that does nothing"""
        pass

    def _realDebugLog(self, *argv):
        self.log.debug(*argv)

    def _getLayerById(self, layerId):
        """Get layer description from the mapLayers module"""
        return self._mapLayersModule.getLayerById(layerId)

    def _loadImage(self, lzxy):
        """Check that an image is loaded, and try to load it if not"""

        debug = self.get('tileLoadingDebug', False)
        if debug:
            sprint = self._realDebugLog
        else:
            sprint = self._fakeDebugLog

        # at this point, there is only a placeholder image in the image cache
        sprint("###")
        sprint("loading tile %s", lzxy)

        # is the tile in local storage ?
        start1 = time.clock()
        tileData = self._storeTiles.get_tile_data(lzxy)

        if tileData:
            try:
                pixbuf = self._data2pixbuf(tileData)
            except Exception:
                self.log.exception("loading tile image to pixbuf failed, name: %s", lzxy)
                return False
        else:
            sprint("tile not found locally: %s", lzxy)
            return False

        start2 = time.clock()
        self.storeInMemory(self._pixbuf2cairoImageSurface(pixbuf), lzxy)
        if debug:
            storageType = self.get('tileStorageType', self.modrana.dmod.defaultTileStorageType)
            sprint(
                "tile loaded from local storage (%s) in %1.2f ms" % (storageType, (1000 * (time.clock() - start1))))
            sprint("tile cached in memory in %1.2f ms" % (1000 * (time.clock() - start2)))
        return True

    def _loadImageFromFile(self, path, name, imageType=NORMAL_TILE, expireTimestamp=None, dictIndex=0):
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

    def _filePath2Pixbuf(self, filePath):
        """return a pixbuf for a given filePath"""
        try:
            pixbuf = gtk.gdk.pixbuf_new_from_file(filePath)
            return pixbuf
        except Exception:
            self.log.exception("the tile image is corrupted nad/or there are no tiles for this zoomlevel")
            return False

    def storeInMemory(self, surface, name, imageType=NORMAL_TILE, expireTimestamp=None, dictIndex=0):
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
                self._trimCache()
                # new tile available, make redraw request TODO: what overhead does this create ?
            self._tileLoadedNotify(imageType)

    def _tileLoadedNotify(self, imageType):
        """redraw the screen when a new tile is available in the cache
           * redraw only when on map screen (menu == None)
           * redraw only on composite tiles when overlay is on"""
        if self.get('tileLoadedRedraw', True) and self.get('menu', None) is None:
            overlay = self.get('overlay', False)
            if overlay: # only redraw when a composited tile is loaded with overlay on
                if imageType == COMPOSITE_TILE:
                    self.set('needRedraw', True)
            else: # redraw regardless of type with overlay off
                self.set('needRedraw', True)

    def _trimCache(self):
        """To avoid a memory leak, the maximum size of the image cache is fixed
           when we reach the maximum size, we start removing images,
           starting from the oldest ones with an amount of images specified
           in imagesTrimmingAmount, so that trim does not run every time
           an image is added to a full cache
           -> only the normal image cache needs trimming (images[0]),
           as the special image cache (images[1]) is just created once and not updated dynamically
           NOTE: the storeInMemory method which is calling this function
                 already locked images, so we don't have to"""
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
        """completely clear the in memory image cache"""
        with self.imagesLock:
            self.log.info('fully clearing the in memory tile cache (%d tiles)', len(self.images[0]))
            self.images[0] = {}

    def _removeTilesFromCache(self, imageTypes):
        """Remove tiles of the given types from the in memory tile cache.

        :param list imageTypes: list if image types to remove
        """
        with self.imagesLock:
            self.log.info("removing %s from the tile cache", imageTypes)
            removedCounter = 0
            keys = list(self.images[0].keys())
            for key in keys:
                if self.images[0][key][1]["type"] in imageTypes:
                    del self.images[0][key]
                    removedCounter += 1
            self.log.debug("removed %d tiles from total of %d", removedCounter, len(keys))

    def _pixbuf2cairoImageSurface(self, pixbuf):
        """Convert a GTK Pixbuf into a Cairo ImageSurface

        :param pixbuf: a GTK Pixbuf instance
        :type pixbuf: a GTK Pixbuf

        :return: a Cairo ImageSurface instance
        :retype: a Cairo ImageSurface
        """
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

    def _data2pixbuf(self, data):
        """Convert binary image data into a GTK Pixbuf

        :param data: binary image data
        :type data: binary data

        :return: a GTK Pixbuf instance
        :rtype: GTK Pixbuf
        """

        pl = gtk.gdk.PixbufLoader()
        pl.write(data)
        pl.close()
        return pl.get_pixbuf()

    def _data2cairoImageSurface(self, data):
        """Convert binary image data to a Cairo image surface

        :param data: binary image data
        :type data: binary data

        :return: Cairo ImageSurface instance
        :rtype: Cairo ImageSurface

        """
        return self._pixbuf2cairoImageSurface(self._data2pixbuf(data))

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
        """A NOP function used for replacing functions that are not
        currently used for some reason (such as for example _invertPixbuf)
        """
        return arg

    def _invertPixbuf(self, pixbuf):
        """Do image inversion for the given pixbuf
        - why PIL & Numpy -> combined, they give usable performance
        (pure python implementation was about 100x times slower
        10 vs 1000 ms per tile)
        """

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
            pBuff = loader.get_pixbuf()
            loader.close()
            return pBuff

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

    #    self.log.debug("tile negative in %1.2f ms" % (1000 * (time.clock() - start1)))

    def _mapStateChangedCB(self, key, oldValue, newValue):
        if key == "overlay":
            if newValue:
                # for some reason we need to drop the cache or else overlay won't
                # activate properly when turned off and on
                self._clearTileCache()
            else:
                self._removeTilesFromCache([COMPOSITE_TILE])
        elif key in ("layer", "layer2"):
            # clear old composites so that they can be replaced by new ones
            self._removeTilesFromCache([COMPOSITE_TILE])
        elif key == "network":
            self._removeTilesFromCache([LOADING_TILE, SPECIAL_TILE, COMPOSITE_TILE])

    def _batchDownloadCompleteDB(self):
        # Clear all special tiles once batch download finishes,
        # so that any batch downloaded tiles that have been batch-downloaded
        # can be loaded.
        # It might be more efficient to only dump tiles only related to the batch
        # or dump special tiles for tiles that have been downloaded, but full
        # special tile dump seems like a simpler and more robust solution.
        self._removeTilesFromCache([LOADING_TILE, SPECIAL_TILE, COMPOSITE_TILE])

    def shutdown(self):
        #    # shutdown the tile loading thread
        #    try:
        #      self.loadingNotifyQueue.put(('shutdown', ()),block=False)
        #    except Queue.Full:
        #      """the tile loading thread is demonic, so it will be still killed in the end"""
        #      pass
        # notify the automatic tile download manager thread about the shutdown
        self._dlRequestQueue.put(TERMINATOR)

        # tell the tile downloader to shutdown the thread pool
        self._downloader.shutdown()
