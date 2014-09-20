# -*- coding: utf-8 -*-
# Tile downloader
#
# TODO:
# * cache successfully downloaded tiles, so that we don't have to
#   query tile storage every time we want to make sure a tile has
#   not yet been downloaded, but only once it is not found in the
#   cache
# * implement request timeout support - if a request is older than a given
#   time delta, discard it
# * overwrite support - we want to download tiles for
#   some layers even if they are already stored locally
#   (traffic, weather overlay, etc.)

from __future__ import with_statement

try:  # Python 2
    from urllib2 import urlopen, HTTPError, URLError
except ImportError:  # Python 3
    from urllib.request import urlopen
    from urllib.error import HTTPError, URLError

import threading
import time
import sys
if sys.version_info[:2] <= (2, 5):
    from core.backports import urllib3_python25 as urllib3
else:
    import urllib3
from core.pool import LifoThreadPool
from core.singleton import modrana
from core import tiles
from core import gs
from core import constants

import logging
log = logging.getLogger("mod.mapTiles.tile_downloader")

# needed fro pixbuf handling
if gs.GUIString == "GTK":
    import gtk

class Downloader(object):
    def __init__(self, maxThreads, taskBufferSize=0,
                 taskTimeout=0):
        self._mapTiles = modrana.m.get("mapTiles")
        self._storeTiles = modrana.m.get("storeTiles")
        # if task buffer size is set, start leaking
        # old tile download requests from the bottom of the
        # request stack once it becomes full, as we don't want
        # the work queue to block and discarding old tile
        # download requests is not an issue
        leak = taskBufferSize >= 0
        self._pool = LifoThreadPool(maxThreads,
                                    name=constants.THREAD_POOL_AUTOMATIC_TILE_DOWNLOAD,
                                    taskBufferSize=taskBufferSize,
                                    leak=leak)
        # in seconds, 0 == no task timeout
        self._taskTimeout = taskTimeout
        self._running = set()
        self._runningLock = threading.RLock()
        # due to GIL, we don't have a lock
        # for the set of tile downloads
        # in progress (hopefully)
        self._imageSurface = self._mapTiles.cacheImageSurfaces

    def shutdown(self):
        self._pool.shutdown(now=True)

    def _tileDownloaded(self, error, lzxy, tag):
        #log.debug("DOWNLOADER: CALLING SIGNAL: %s %s" % (tag, success))
        self._mapTiles.tileDownloaded(error, lzxy, tag)

    def downloadTile(self, lzxy, tag=None, overwrite=False):
        """Add a tile download request, if this download
        request replaces another not yet handled request
        from the bottom of the work stack, the old
        lzxy will be returned

        :param tuple lzxy: tile to download represented by a tuple
        :param str tag: tracking tag for the download request
        :param bool overwrite: download tile even if locally available
        :returns: None or a tuple that was removed because of the new one
        :rtype: None or tuple
        """
        discardedRequest = None
        discardedTile = None
        with self._runningLock:
            if lzxy not in self._running:
                # drop download requests for tiles that are already
                # being downloaded
                discardedRequest = self._pool.submit(
                    self._handleDownload, lzxy, tag, time.time(), overwrite
                )
        # return lzxy & tag for any discarded request or return None
        # if no request was discarded
        if discardedRequest:
            discardedTile = discardedRequest[1][0], discardedRequest[1][1]
        return discardedTile

    def _handleDownload(self, lzxy, tag, timestamp, overwrite):
        download = True
        error = constants.TILE_DOWNLOAD_ERROR
        with self._runningLock:
            if (lzxy, tag) in self._running:
                # tile is already being downloaded
                download = False
            else:
                # tile is not yet being downloaded
                # so register we are handling it
                self._running.add((lzxy, tag))

        if self._taskTimeout:
            dt = time.time() - timestamp
            if dt >= self._taskTimeout:
                # download request timed out
                download = False

        if not download and not overwrite:
            # check if the tile has been already downloaded
            download = not self._storeTiles.tileExists2(lzxy, fromThread=True)

        if download:
            # download tile
            try:
                self._downloadTile(lzxy)
                error = constants.TILE_DOWNLOAD_SUCCESS
            except urllib3.exceptions.HTTPError:
                # server returned a HTTP error, this means we got
                # to the server but it didn't like us for some reason,
                error = self._fatalDownloadError(lzxy)
            except URLError:
                # this is most probably caused by a loss of network connectivity
                error = self._temporaryDownloadError(lzxy)

            # something other is wrong (most probably a corrupt tile)
            except Exception:
                import sys
                e = sys.exc_info()[1]
                self._printErrorMessage(e, lzxy)
                # remove the status tile
                self._mapTiles.removeImageFromMemory(self._mapTiles.imageName(lzxy))
                error = constants.TILE_DOWNLOAD_ERROR
            finally:
                # done, unregister the tile from the tracking set
                with self._runningLock:
                    try:
                        self._running.remove((lzxy, tag))
                    except KeyError:
                        pass
                        # TODO: find why this happens (well, it appears to be harmless)
                        #       and maybe forward it to debug log once we have one ?
                        #print("auto tile dl pool: warning, tuple already removed from tracking!")
                        #print(lzxy)
                # report that tha tile has or has not bee successfully downloaded
                self._tileDownloaded(error, lzxy, tag)
        else:
            # don't download tile and remove
            # any "downloading" tiles that might
            # be in the image cache
            self._mapTiles.removeImageFromMemory(self._mapTiles.imageName(lzxy))
            # report the tile as not been downloaded
            self._tileDownloaded(error, lzxy, tag)


    def _downloadTile(self, lzxy):
            """Downloads a tile image image from network"""
            self._downloadInProgress(lzxy)
            content = self._mapTiles.downloadTile(lzxy)
            if content is None:
                raise urllib3.exceptions.HTTPError
            cacheName = self._mapTiles.imageName(lzxy)
            if self._imageSurface:
                pl = gtk.gdk.PixbufLoader()
                pl.write(content)
                pl.close() # this  blocks until the image is completely loaded
                # http://www.ossramblings.com/loading_jpg_into_cairo_surface_python
                surface = self._mapTiles.pixbuf2cairoImageSurface(pl.get_pixbuf())
                self._mapTiles.storeInMemory(surface, cacheName)
                # like this, corrupted tiles should not get past the pixbuf loader and be stored
            else:
                # cache the raw data
                self._mapTiles.storeInMemory(content, cacheName)
            self._storeTiles.automaticStoreTile(content, lzxy)

    def _downloadInProgress(self, lzxy):
        if self._imageSurface:
            cacheName = self._mapTiles.imageName(lzxy)
            # change the status tile to "Downloading..."
            self._mapTiles.storeInMemory(self._mapTiles.downloadingTile[0], cacheName, imageType="downloading")

    def _temporaryDownloadError(self, lzxy):
        if self._imageSurface:
            tileNetworkErrorSurface = self._mapTiles.images[1]['tileNetworkError'][0]
            expireTimestamp = time.time() + 10
            cacheName = self._mapTiles.imageName(lzxy)
            self._mapTiles.storeInMemory(tileNetworkErrorSurface, cacheName, 'error',
                                         expireTimestamp) # retry after 10 seconds
            # as not to DOS the system when we temporarily loose internet connection or other such error
            # occurs, we load a temporary error tile with expiration timestamp instead of the tile image
            # TODO: actually remove tiles according to expiration timestamp :)
        return constants.TILE_DOWNLOAD_TEMPORARY_ERROR

    def _fatalDownloadError(self, lzxy):
        if self._imageSurface:
            tileDownloadFailedSurface = self._mapTiles.images[1]['tileDownloadFailed'][0]
            expireTimestamp = time.time() + 10
            cacheName = self._mapTiles.imageName(lzxy)
            self._mapTiles.storeInMemory(tileDownloadFailedSurface, cacheName, 'semiPermanentError',
                                         expireTimestamp)
            # like this, when tile download fails due to a http error,
            # the error tile is loaded instead
            # like this:
            #  - modRana does not immediately try to download a tile that errors out
            #  - the error tile is shown without modifying the pipeline too much
            #  - modRana will eventually try to download the tile again,
            #    after it is flushed with old tiles from the memory
        return constants.TILE_DOWNLOAD_ERROR

    def _printErrorMessage(self, e, lzxy):
        url = tiles.getTileUrl(lzxy)
        error = "mapTiles: download thread reports error\n"
        error+= "** we were doing this, when an exception occurred:\n"
        error+= "** downloading tile: x:%d,y:%d,z:%d, layer:%s, url: %s" % (
            lzxy[1],
            lzxy[2],
            lzxy[3],
            lzxy[0].id,
            url)
        log.exception(error)

    @property
    def maxThreads(self):
        return self._pool.maxThreads

    @property
    def qsize(self):
        return self._pool.qsize()