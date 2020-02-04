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


from urllib.request import urlopen
from urllib.error import HTTPError, URLError
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

        self.mapViewModule = None
        self._mapLayersModule = None

        # cache the map folder path
        self.mapFolderPath = self.modrana.paths.map_folder_path
        self.log.info("map folder path: %s" % self.mapFolderPath)

        self._storeTiles = None

        self.connPools = {} # connection pool dictionary

        self.cacheImageSurfaces = False  # only GTK GUI used this

        self._filterTile = self._nop

        self._tileDownloaded = Signal()

        self._dlRequestQueue = six.moves.queue.Queue()
        self._downloader = None

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

    def getTile(self, lzxy, asynchronous=False, tag=None, download=True):
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
            if asynchronous:
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
        response = self._getConnPool(lzxy[0], tileUrl).request('GET', tileUrl)
        # self.log.debug("RESPONSE")
        # self.log.debug(response)
        tileData = response.data
        if tileData:
            # check if the data is actually an image, and not an error page
            if utils.is_the_string_an_image(tileData):
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

    def _getConnPool(self, layer, baseUrl):
        """Get a connection pool for the given layer id
        Each layer ID has it's own connection pool
        (as each connection pool handles only one base URL)
        and non-existent pools are automatically created once requested
        NOTE: connection pools reuse open connections

        :param str layerId: pool id (mapped to layer id)
        :param str baseUrl: a URL used to initialize the connection pool
                           (basically just the domain name needs to be correct)
        """
        pool = self.connPools.get(layer.id, None)
        if pool:
            return pool
        else: # create pool
            #headers = { 'User-Agent' : "Mozilla/5.0 (compatible; MSIE 5.5; Linux)" }
            userAgent = self.modrana.configs.user_agent
            headers = {'User-Agent': userAgent}
            connection_timeout = constants.TILE_DOWNLOAD_TIMEOUT
            if layer.connection_timeout is not None:  # some value was set in the config
                if layer.connection_timeout < 0:  # -1 == no timeout
                    connection_timeout = None  # None means no timeout for Urllib 3 connection pools
                else:
                    connection_timeout = layer.connection_timeout
            if connection_timeout is None:
                self.log.debug("creating tile download pool for %s without a connection timeout", layer.id)
            else:
                self.log.debug("creating tile download pool for %s with connection timeout %s s", layer.id, connection_timeout)
            newPool = urllib3.connection_from_url(url=baseUrl,
                                                  headers=headers,
                                                  maxsize=10,
                                                  timeout=connection_timeout,
                                                  block=False)
            self.connPools[layer.id] = newPool
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

    def _fakeDebugLog(self, *argv):
        """Log function that does nothing"""
        pass

    def _realDebugLog(self, *argv):
        self.log.debug(*argv)

    def _getLayerById(self, layerId):
        """Get layer description from the mapLayers module"""
        return self._mapLayersModule.getLayerById(layerId)

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
        # TODO: is this still needed ?
        pass

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