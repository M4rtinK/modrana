# -*- coding: utf-8 -*-
# Tile checking & batch download pools
from __future__ import with_statement

import threading
import time
from core import constants
from core import threads
from core import tiles
from core.signal import Signal
from core import utils
from core.pool import ThreadPool
from core.singleton import modrana

import logging
log = logging.getLogger("mod.mapData.pools")

MAX_RETRIES = 3
RETRY_WAIT = 0.1  # 100 ms

DEFAULT_THREAD_POOL_NAME = "modRanaBatchPool"
_threadPoolIndex = 1

class TileNotImageException(Exception):
    def __init__(self, url):
        self.parameter = 1
        self.url = url

    def __str__(self):
        message = "the downloaded tile is not an image as per \
its magic number (it is probably an error response webpage \
returned by the server)\nURL:%s" % self.url

        return message

def getAnUrl(batch, layer):
    """Get a random url from the set so we can init the pool"""
    if batch:
        tile = None
        for t in batch:
            tile = t
            break
        (x, y, z) = (tile[0], tile[1], tile[2])
        url = tiles.getTileUrl((layer, z, x, y))
    else:
        url = ""
    return url

def _getBatchPoolName():
    global _threadPoolIndex
    name = "%s%d" % (DEFAULT_THREAD_POOL_NAME, _threadPoolIndex)
    _threadPoolIndex+=1
    return name

class BatchPool(object):
    def __init__(self, name=None):
        if name is None:
            self._name = _getBatchPoolName()
        else:
            self._name = name
        self._batch = set()
        self._doneCount = 0
        self._running = False
        self._shutdown = False
        self._mutex = threading.RLock()
        self._loaderName = None
        self._pool = None
        self.batchDone = Signal()

    def startBatch(self, batch, **kwargs):
        """Process a batch"""
        with self._mutex:
            if self._running:
                log.debug("can't start another batch - already running")
            else:
                self._running = True
                self._batch = batch

                self._pool = ThreadPool(name=self.name,
                                        maxThreads=self._maxThreads())

                # start the loading thread
                t = threads.ModRanaThread(name=self.name+"Loader", target=self._loadItems)
                self._loaderName = threads.threadMgr.add(t)

    @property
    def name(self):
        return self._name

    @property
    def batchSize(self):
        return len(self._batch)

    @property
    def done(self):
        with self._mutex:
            return self._doneCount

    @property
    def running(self):
        with self._mutex:
            return self._running

    def _loadItems(self):
        self._processBatch()
        # in this moment we either run out of work, in which case
        # we tell the pool to shutdown once all work is processed
        # (now==False) or the batch pool has been explicitly shutdown
        # (self._shutdown=True) in which case we tell the pool to shutdown
        # as quickly as possible (now==True)
        self._pool.shutdown(now=self._shutdown, join=True, asynchronous=False,
                            callback=self._stoppedCallback)
        log.info("%s loader done", self.name)

    def _handleItemWrapper(self, item):
        self._handleItem(item)
        # one item processed
        with self._mutex:
            self._doneCount+=1

    def stop(self):
        """Stop processing as soon as possible"""
        # tell the loading thread to shutdown
        with self._mutex:
            if self._running:
                self._shutdown = True

    def _stoppedCallback(self):
        """Called from a thread once the thread pool is fully stopped"""
        # lets miss-use the callback thread a bit and make it wait for the
        # loader to finish
        self._shutdown = True

        # now we can report we are no longer running & ready for new batch
        with self._mutex:
            # also cleanup so we are back to initial state
            self._cleanup()
            self._running = False
            self._shutdown = False

        # trigger the batch done signal
        self.batchDone()

    def _cleanup(self):
        self._batch = []
        self._doneCount = 0
        self._loaderName = None
        self._pool = None

    # subclassing interface
    def _processBatch(self):
        pass

    def _handleItem(self, item):
        pass

    def _maxThreads(self):
        return 5


class TileBatchPool(BatchPool):
    def __init__(self, name):
        BatchPool.__init__(self, name)
        self._layer = None
        self._connPool = None
        self._mapDataM = None
        self._storeTilesM = None
        self._ended = False
        self.batchDone.connect(self._batchDoneCB)

    @property
    def _mapData(self):
        if not self._mapDataM:
            self._mapDataM = modrana.m.get("mapData")
        return self._mapDataM

    @property
    def _storeTiles(self):
        if not self._storeTilesM:
            self._storeTilesM = modrana.m.get("storeTiles")
        return self._storeTilesM

    @property
    def layer(self):
        return self._layer

    @layer.setter
    def layer(self, layer):
        with self._mutex:
            if self._running:
                log.debug("tile batch pool: can't set layer when batch is running")
            else:
                self._layer = layer

    @property
    def ended(self):
        """Report if the batch did run and ended"""
        return self._ended

    def _batchDoneCB(self):
        self._ended = True

    def reset(self):
        """Reset to initial state"""
        self._ended = False

    def _cleanup(self):
        super(TileBatchPool, self)._cleanup()
        self._layer = None
        self._connPool = None

    def _processBatch(self):
        # setup the connection pool
        if self.layer is None:
            log.error("tile batch pool: layer is None, aborting")
            return
        self._connPool = utils.create_connection_pool(getAnUrl(self._batch, self._layer))

class BatchSizeCheckPool(TileBatchPool):
    def __init__(self):
        TileBatchPool.__init__(self,
                               name=constants.THREAD_POOL_BATCH_SIZE_CHECK
        )
        self._downloadSize = 0
        self._foundLocally = 0

    @property
    def downloadSize(self):
        return self._downloadSize

    @property
    def foundLocally(self):
        return self._foundLocally

    def reset(self):
        super(BatchSizeCheckPool, self).reset()
        # clear variables from previous run
        self._downloadSize = 0
        self._foundLocally = 0

    def _maxThreads(self):
        return int(modrana.get('maxSizeThreads', constants.DEFAULT_THREAD_COUNT_BATCH_SIZE_CHECK))

    def _processBatch(self):
        """When checking the size of the download batch we
        iterate over all the requests while processing them
        and also remove locally available tiles from the
        main batch set
        """
        # if the size check is restarted, it goes over the tiles
        # again, so we need to reset the size estimate
        super(BatchSizeCheckPool, self)._processBatch()
        self._downloadSize = 0
        for item in self._batch:
            if self._shutdown:
                break
            else:
                self._pool.submit(self._handleItemWrapper, item)

    def _handleItem(self, item):
        x, y, z = item
        lzxy = (self._layer, z, x, y)
        size = self._checkTileSize(lzxy)
        if size:
            with self._mutex:
                self._downloadSize+=size
        elif size is None:
            # remove locally available tiles from request set
            self._mapData.removeTileDownloadRequest(item)
            with self._mutex:
                self._foundLocally+=1

    def _checkTileSize(self, lzxy):
        """Get a size of a tile from HTTP header,
        if the tile is locally available remove it form the
        download request set

        :returns: size in bytes, None if tile is available and
                  0 if the header check raised an exception
        :rtype: int or None
        """
        size = 0
        url = "unknown url"
        try:
            url = tiles.getTileUrl(lzxy)
            # does the tile exist ?
            if self._storeTiles.tile_is_stored(lzxy): # if the file does not exist
                size = None # it exists, return None
            else:
                # the tile does not exist, get its HTTP header
                request = self._connPool.urlopen('HEAD', url)
                size = int(request.getheaders()['content-length'])
        except IOError:
            log.error("Could not open document: %s", url)
            # the url errored out, so we just say it  has zero size
            size = 0
        except Exception:
            log.exception("error, while checking size of tile: %s", lzxy)
            size = 0
        return size

    def _cleanup(self):
        super(BatchSizeCheckPool, self)._cleanup()


class BatchTileDownloadPool(TileBatchPool):
    def __init__(self):
        TileBatchPool.__init__(self, name=constants.THREAD_POOL_BATCH_DOWNLOAD)
        self._initialBatchSize = 0
        self._downloadedDataSize = 0
        self._failedCount = 0

    @property
    def downloadedDataSize(self):
        return self._downloadedDataSize

    @property
    def failedDownloadCount(self):
        return self._failedCount

    @property
    def batchSize(self):
        """As we remove items from the batch during the iteration
        we override the batchSize property and report the initial batch size.
        Otherwise the done/from work-in-progress would not make sense.
        """
        return self._initialBatchSize

    def reset(self):
        super(BatchTileDownloadPool, self).reset()
        # clear variables from previous run
        self._downloadedDataSize = 0

    def _maxThreads(self):
        return int(modrana.get('maxDlThreads', constants.DEFAULT_THREAD_COUNT_AUTOMATIC_TILE_DOWNLOAD))

    def _processBatch(self):
        """While processing the download batch we remove
        the requests one by one and process them
        """
        super(BatchTileDownloadPool, self)._processBatch()


        self._initialBatchSize = len(self._batch)

        while not self._shutdown:
            try:
                item = self._batch.pop()
                self._pool.submit(self._handleItemWrapper, item)
            except KeyError:
                break
            except IndexError:
                break

    def _handleItem(self, item):
        x, y, z = item
        # TODO: use zxy for item
        lzxy = (self._layer, z, x, y)
        size = False
        # 1. attempt + 3 retries
        for i in range(0, MAX_RETRIES+1):
            try:
                size = self._saveTileForURL(lzxy)
            except Exception:
                log.exception("exception in batch download thread:")
            if size != False:  # download successful
                with self._mutex:
                    self._downloadedDataSize+=size
                break
            # wait a bit before retry
            time.sleep(RETRY_WAIT)
        if size == False:
            with self._mutex:
                self._failedCount+=1

    def _saveTileForURL(self, lzxy):
        """save a tile for url created from its coordinates"""
        url = tiles.getTileUrl(lzxy)

        goAhead = False
        redownload = int(modrana.get('batchRedownloadAvailableTiles', False))
        # TODO: use constants for the ENUM
        if not redownload:
            # does the the file exist ?
            # -> don't download it if it does
            goAhead = not self._storeTiles.tile_is_stored(lzxy)
        elif redownload == 1: # redownload all
            goAhead = True
        elif redownload == 2: # update
            # only download tiles in the area that already exist
            goAhead = self._storeTiles.tile_is_stored(lzxy)
        if goAhead: # if the file does not exist
            request = self._connPool.request('get', url)
            size = int(request.getheaders()['content-length'])
            content = request.data
            # The tileserver sometimes returns a HTML error page
            # instead of the tile, which is then saved instead of the tile an
            # users are then confused why tiles they have downloaded don't show up.

            # To raise a proper error on this behaviour, we check the tiles magic number
            # and if is not an image we raise the TileNotImageException.

            # TODO: does someone supply non-bitmap/SVG tiles ?
            if utils.is_the_string_an_image(content):
                #its an image, save it
                self._storeTiles.store_tile_data(lzxy, content)
            else:
                # its not ana image, raise exception
                raise TileNotImageException(url)
            return size # something was actually downloaded and saved
        else:
            return False # nothing was downloaded

    def _cleanup(self):
        super(BatchTileDownloadPool, self)._cleanup()
        self._failedCount = 0
        self._initialBatchSize = 0
        # tell the mapData module a batch tile
        # download was in progress and just ended
        self._mapData._batchDone = True
