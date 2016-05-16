# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# A modRana Qt 5 QtQuick 2.0 GUI module
# * it inherits everything in the base GUI module
# * overrides default functions and handling
#----------------------------------------------------------------------------
# Copyright 2013, Martin Kolman
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
from __future__ import with_statement
import os
import re

import pyotherside

try:
    from StringIO import StringIO # python 2
except ImportError:
    from io import StringIO # python 3

# modRana imports
import math
from modules.gui_modules.base_gui_module import GUIModule
import time
import threading

from core import signal
from core import constants
from core.threads import threadMgr
from core import geo
from core import modrana_log
from core import utils
from core import paths

import logging
log = logging.getLogger("mod.gui.qt5")
qml_log = logging.getLogger("mod.gui.qt5.qml")

SEARCH_STATUS_PREFIX = "search:status:"
SEARCH_RESULT_PREFIX = "search:result:"

def newlines2brs(text):
    """ QML uses <br> instead of \n for linebreak """
    return re.sub('\n', '<br>', text)

def getModule(*args, **kwargs):
    return QMLGUI(*args, **kwargs)

def point2dict(point):
    """ Convert a Point instance to a dict

        :param Point point: a Point object instance
        :returns dict: a dict representation of the point
    """
    return {
        "name" : point.name,
        "description" : point.description,
        "latitude" : point.lat,
        "longitude" : point.lon,
        "elevation" : point.elevation,
        "highlight" : False
    }


class QMLGUI(GUIModule):
    """A Qt + QML GUI module"""

    def __init__(self, *args, **kwargs):
        GUIModule.__init__(self, *args, **kwargs)

        # some constants
        self.msLongPress = 400
        self.centeringDisableThreshold = 2048
        self.firstTimeSignal = signal.Signal()
        size = (800, 480) # initial window size

        # positioning related
        self._pythonPositioning = False

        # we handle notifications by forwarding them to the QML context
        self.modrana.notificationTriggered.connect(self._dispatchNotificationCB)

        # register exit handler
        #pyotherside.atexit(self._shutdown)
        # FIXME: for some reason the exit handler is never
        # called on Sailfish OS, so we use a onDestruction
        # handler on the QML side to trigger shutdown

        # window state
        self._fullscreen = False

        # get screen resolution
        # TODO: implement this
        #screenWH = self.getScreenWH()
        #self.log.debug(" @ screen size: %dx%d" % screenWH)
        #if self.highDPI:
        #    self.log.debug(" @ high DPI")
        #else:
        #    self.log.debug(" @ normal DPI")

        # NOTE: what about multi-display devices ? :)

        ## add image providers

        self._imageProviders = {
            "icon" : IconImageProvider(self),
            "tile" : TileImageProvider(self),
        }

        ## register the actual callback, that
        ## will call the appropriate provider base on
        ## image id prefix
        pyotherside.set_image_provider(self._selectImageProviderCB)

        # initialize theming
        self._theme = Theme(self)

        ## make constants accessible
        #self.constants = self.getConstants()
        #rc.setContextProperty("C", self.constants)

        ## connect to the close event
        #self.window.closeEvent = self._qtWindowClosed
        ##self.window.show()

        self._notificationQueue = []

        # provides easy access to modRana modules from QML
        self.modules = Modules(self)

        # search functionality for the QML context
        self.search = Search(self)

        # make the log manager easily accessible
        self.log_manager = modrana_log.log_manager

        # log for log messages from the QML context
        self.qml_log = qml_log
        # queue a notification to QML context that
        # a Python loggers is available
        pyotherside.send("loggerAvailable")

        # tracklogs
        self.tracklogs = Tracklogs(self)

        #routing
        self.routing = Routing(self)

    def firstTime(self):
        # trigger the first time signal
        self.firstTimeSignal()

        self.modules.location.positionUpdate.connect(self._pythonPositionUpdateCB)

    def _shutdown(self):
        """Called by PyOtherSide once the QML side is shutdown.
        """
        self.log.info("Qt 5 GUI module shutting down")
        self.modrana.shutdown()

    def getIDString(self):
        return "Qt5"

    def needsLocalhostTileserver(self):
        """
        the QML GUI needs the localhost tileserver
        for efficient and responsive tile loading
        """
        return False

    def isFullscreen(self):
        return self._fullscreen

    def toggleFullscreen(self):
        # TODO: implement this
        pass

    def setFullscreen(self, value):
        pass

    def setCDDragThreshold(self, threshold):
        """set the threshold which needs to be reached to disable centering while dragging
        basically, larger threshold = longer drag is needed to disable centering
        default value = 2048
        """
        self.centeringDisableThreshold = threshold

    def hasNotificationSupport(self):
        return True

    def _dispatchNotificationCB(self, text, msTimeout=5000, icon=""):
        """Let the QML context know that it should show a notification

        :param str text: text of the notification message
        :param int msTimeout: how long to show the notification in ms
        """

        self.log.debug("notify:\n message: %s, timeout: %d" % (text, msTimeout))
        pyotherside.send("pythonNotify", {
            "message" : newlines2brs(text),  # QML uses <br> in place of \n
            "timeout" : msTimeout
        })

    def openUrl(self, url):
        # TODO: implement this
        pass

    def _getTileserverPort(self):
        m = self.m.get("tileserver", None)
        if m:
            return m.getServerPort()
        else:
            return None

    def getScreenWH(self):
        # TODO: implement this
        pass

    def getModRanaVersion(self):
        """
        report current modRana version or None if version info is not available
        """
        version = self.modrana.paths.getVersionString()
        if version is None:
            return "unknown"
        else:
            return version

    def setPosition(self, posDict):
        if self._pythonPositioning:
            # ignore the setPosition call if Python-side positioning
            # is used as the Python side already has fresh position data
            return
        lat, lon = float(posDict["latitude"]), float(posDict["longitude"])
        elevation = float(posDict["elevation"])
        metersPerSecSpeed = float(posDict["speedMPS"])  # m/s
        # report that we have 3D fix
        # (looks like we can't currently reliably discern between 2D
        # and 3D fix on the Jolla, might be good to check what other
        # Sailfish OS running devices report)
        self.set("fix", 3)

        self.set("pos", (lat, lon))

        # check if elevation is valid
        if not math.isnan(elevation):
            self.set("elevation", elevation)
        else:
            self.set("elevation", None)

        # check if speed is valid
        if not math.isnan(metersPerSecSpeed):
            self.set("speed", metersPerSecSpeed*3.6)
            self.set("metersPerSecSpeed", metersPerSecSpeed)
        else:
            self.set("speed", None)
            self.set("metersPerSecSpeed", None)

        # update done
        self.set('locationUpdated', time.time())
        # TODO: move part of this to the location module ?

    def _pythonPositionUpdateCB(self, fix):
        self._pythonPositioning = True
        if fix.position:
            (lat, lon) = fix.position
        else:
            (lat, lon) = None
        pyotherside.send("pythonPositionUpdate", {
            "latitude" : lat,
            "longitude" : lon,
            "altitude" : fix.altitude,
            "speed" : fix.speed,
            "horizontalAccuracy" : fix.horizontal_accuracy,
            "verticalAccuracy" : fix.vertical_accuracy,
            "timestamp" : fix.timestamp,
            "valid" : bool(fix.position)
        })

    def _selectImageProviderCB(self, imageId, requestedSize):
        originalImageId = imageId
        providerId = ""
        #self.log.debug("SELECT IMAGE PROVIDER")
        #self.log.debug(imageId)
        #self.log.debug(imageId.split("/", 1))
        try:
            # split out the provider id
            providerId, imageId = imageId.split("/", 1)
            # get the provider and call its getImage()
            return self._imageProviders[providerId].getImage(imageId, requestedSize)
        except ValueError:  # provider id missing or image ID overall wrong
            self.log.error("provider ID missing: %s", originalImageId)
        except AttributeError:  # missing provider (we are calling methods of None ;) )
            if providerId:
                self.log.error("image provider for this ID is missing: %s", providerId)
            else:
                self.log.error("image provider broken, image id: %s", originalImageId)
        except Exception:  # catch and report the rest
            self.log.exception("image loading failed, imageId: %s", originalImageId)

    def _tileId2lzxy(self, tileId):
        """Convert tile id string to the "standard" lzxy tuple

        :param str tileId: map instance name/layer id/z/x/y

        :returns: lzxy tuple
        :rtype: tuple
        """
        split = tileId.split("/")
        # pinchMapId = split[0]
        layerId = split[1]
        z = int(split[2])
        x = int(split[3])
        y = int(split[4])
        # TODO: local id:layer cache ?
        layer = self.modules.mapLayers.getLayerById(layerId)
        return layer, z, x, y

    def areTilesAvailable(self, tile_ids):
        """Report if tiles are available & request download for those that are not.

        :param list tile_ids: list of tile ids to check
        :return: a distionary of tile states, True = available, False = will be downloaded
        :rtype: dict
        """
        available_tiles = {}
        for tile_id in tile_ids:
            available_tiles[tile_id] = self.isTileAvailable(tile_id)
        return available_tiles

    def isTileAvailable(self, tileId):
        """Check if tile is available and add download request if not.

        NOTE: If automatic tile downloads are disabled tile download
              request will not be queued.

        :param str tileId: tile identificator
        :return: True if the tile is locally available, False if not
        :rtype: bool
        """
        lzxy = self._tileId2lzxy(tileId)
        if self.modules.mapTiles.tileInStorage(lzxy):
            return True
        else:
            self._addTileDownloadRequest(lzxy, tileId)
            return False


    def _addTileDownloadRequest(self, lzxy, tileId):
        """Add an asynchronous download request, the tile will be
        notified once the download is finished or fails
        :param string tileId: unique tile id
        """
        try:
            self.modules.mapTiles.addTileDownloadRequest(lzxy, tileId)
        except Exception:
            self.log.exception("adding tile download request failed")

    def _getStartupValues(self):
        """ Return a dict of values needed by the Qt 5 GUI right after startup.
        By grouping the requested values in a single dict we reduce the number
        of Python <-> QML roundtrips and also make it possible to more easily
        get these values asynchronously (values arrive all at the same time,
        not in random order at random time).

        :returns: a dict gathering the requested values
        :rtype dict:
        """
        values = {
            "modRanaVersion" : self.getModRanaVersion(),
            "constants" : self.getConstants(),
            "showQuitButton": self.showQuitButton(),
            "fullscreenOnly": self.modrana.dmod.fullscreenOnly(),
            "shouldStartInFullscreen": self.shouldStartInFullscreen(),
            "needsBackButton": self.modrana.dmod.needsBackButton(),
            "needsPageBackground": self.modrana.dmod.needsPageBackground(),
            "lastKnownPos" : self.get("pos", None),
            "gpsEnabled" : self.get("GPSEnabled", True),
            "posFromFile" : self.get("posFromFile", None),
            "nmeaFilePath" : self.get("NMEAFilePath", None),
            "layerTree" : self.modules.mapLayers.getLayerTree(),
            "dictOfLayerDicts" : self.modules.mapLayers.getDictOfLayerDicts(),
            "themesFolderPath" : os.path.abspath(self.modrana.paths.getThemesFolderPath()),
            "sailfish" : self.dmod.getDeviceIDString() == "jolla",
            "hiDPI" : self.highDPI,
            "defaultTileStorageType" : self.modrana.dmod.defaultTileStorageType
        }
        return values


class Modules(object):
    """A class that provides access to modRana modules from the QML context,
       using the __getattr__ method so that QML can access all modules dynamically
       with normal dot notation
    """

    def __init__(self, gui):
        self._info = None
        self._stats = None
        self._mapLayers = None
        self._storeTiles = None
        self.gui = gui

    def __getattr__(self, moduleName):
        return self.gui.m.get(moduleName, None)


class Search(object):
    """An easy to use search interface for the QML context"""

    def __init__(self, gui):
        self.gui = gui
        self._threadsInProgress = {}
        # register the thread status changed callback
        threadMgr.threadStatusChanged.connect(self._threadStatusCB)

    def search(self, searchId, query):
        """Trigger an asynchronous search (specified by search id)
        for the given term

        :param str query: search query
        """
        online = self.gui.m.get("onlineServices", None)
        if online:
            # construct result handling callback
            callback = lambda x : self._searchCB(searchId, x)
            # get search function corresponding to the search id
            searchFunction = self._getSearchFunction(searchId)
            # start the search and remember the search thread id
            # so we can use it to track search progress
            # (there might be more searches in progress so we
            #  need to know the unique search thread id)
            threadId = searchFunction(query, callback)
            self._threadsInProgress[threadId] = searchId
            return threadId

    def _searchCB(self, searchId, results):
        """Handle address search results

        :param list results: address search results
        """
        # try to sort local search results by distance
        # TODO: make this configurable
        if searchId == "local":
            pos = self.gui.get("pos", None)
            if pos:
                distanceList = []
                for result in results:
                    distanceList.append((geo.distanceP2LL(result,pos[0], pos[1]), result))
                distanceList.sort()
                results = map(lambda x: x[1], distanceList)
        # covert the Points in the results to a list of dicts
        resultList = []
        for result in results:
            resultList.append(point2dict(result))

        resultId = SEARCH_RESULT_PREFIX + searchId
        pyotherside.send(resultId, resultList)
        thisThread = threading.currentThread()
        # remove the finished thread from tracking
        if thisThread.name in self._threadsInProgress:
            del self._threadsInProgress[thisThread.name]

    def cancelSearch(self, threadId):
        """Cancel the given asynchronous search thread"""
        log.info("canceling search thread: %s", threadId)
        threadMgr.cancel_thread(threadId)
        if threadId in self._threadsInProgress:
            del self._threadsInProgress[threadId]

    def _threadStatusCB(self, threadName, threadStatus):
        # check if the event corresponds to some of the
        # in-progress search threads
        recipient = self._threadsInProgress.get(threadName)
        if recipient:
            statusId = SEARCH_STATUS_PREFIX + recipient
            pyotherside.send(statusId, threadStatus)

    def _getSearchFunction(self, searchId):
        """Return the search function object for the given searchId"""
        online = self.gui.m.get("onlineServices", None)
        if online:
            if searchId == "address":
                return online.geocodeAsync
            elif searchId == "wikipedia":
                return online.wikipediaSearchAsync
            elif searchId == "local":
                return online.localSearchAsync
            else:
                log.error("search function for id: %s not found", searchId)
                return None
        else:
            log.error("onlineServices module not found")


class ImageProvider(object):
    """PyOtherSide image provider base class"""
    def __init__(self, gui):
        self.gui = gui

    def getImage(self, imageId, requestedSize):
        pass


class IconImageProvider(ImageProvider):
    """the IconImageProvider class provides icon images to the QML layer as
    QML does not seem to handle .. in the url very well"""

    def __init__(self, gui):
        ImageProvider.__init__(self, gui)

    def getImage(self, imageId, requestedSize):
        #log.debug("ICON!")
        #log.debug(imageId)
        try:
            #TODO: theme name caching ?
            themeFolder = self.gui.modrana.paths.getThemesFolderPath()
            # fullIconPath = os.path.join(themeFolder, imageId)
            # the path is constructed like this in QML
            # so we can safely just split it like this
            splitPath = imageId.split("/")
            # remove any Ambiance specific garbage appended by Silica
            splitPath[-1] = splitPath[-1].rsplit("?")[0]
            fullIconPath = os.path.join(themeFolder, *splitPath)

            if not utils.internal_isfile(fullIconPath):
                if splitPath[0] == constants.DEFAULT_THEME_ID:
                    # already on default theme and icon path does not exist
                    log.error("Icon not found in default theme:")
                    log.error(fullIconPath)
                    return None
                else:  # try to get the icon from default theme
                    splitPath[0] = constants.DEFAULT_THEME_ID
                    fullIconPath = os.path.join(themeFolder, *splitPath)
                    if not utils.internal_isfile(fullIconPath):
                        # icon not found even in the default theme
                        log.error("Icon not found even in default theme:")
                        log.error(fullIconPath)
                        return None
            return utils.internal_get_file_contents(fullIconPath), (-1,-1), pyotherside.format_data
        except Exception:
            log.exception("icon image provider: loading icon failed, id:\n%s" % imageId)

class TileImageProvider(ImageProvider):
    """
    the TileImageProvider class provides images images to the QML map element
    """

    def __init__(self, gui):
        ImageProvider.__init__(self, gui)
        self.gui = gui

        self.gui.firstTimeSignal.connect(self._firstTimeCB)
        self._tileNotFoundImage = bytearray([0, 255, 255, 255])

    def _firstTimeCB(self):
        # connect to the tile downloaded callback so that we can notify
        # the QML context that a tile has ben downloaded and should be
        # shown on the screen
        # NOTE: we need to wait for the firstTime signal as at GUI module init
        # the other modules (other than the device module) are not yet initialized
        self.gui.modules.mapTiles.tileDownloaded.connect(self._tileDownloadedCB)

    def _tileDownloadedCB(self, error, lzxy, tag):
        """Notify the QML context that a tile has been downloaded"""
        pinchMapId = tag.split("/")[0]
        #log.debug("SENDING: %s %s" % ("tileDownloaded:%s" % pinchMapId, tag))
        resoundingSuccess = error == constants.TILE_DOWNLOAD_SUCCESS
        fatalError = error == constants.TILE_DOWNLOAD_ERROR
        pyotherside.send("tileDownloaded:%s" % pinchMapId, tag, resoundingSuccess, fatalError)

    def getImage(self, imageId, requestedSize):
        """
        the tile info should look like this:
        layerID/zl/x/y
        """
        #log.debug("TILE REQUESTED %s" % imageId)
        #log.debug(requestedSize)
        try:
            # split the string provided by QML
            split = imageId.split("/")
            pinchMapId = split[0]
            layerId = split[1]
            z = int(split[2])
            x = int(split[3])
            y = int(split[4])

            # TODO: local id:layer cache ?
            layer = self.gui.modules.mapLayers.getLayerById(layerId)

            # construct the tag
            #tag = (pinchMapId, layerId, z, x, y)
            #tag = (pinchMapId, layerId, z, x, y)

            # get the tile from the tile module
            tileData = self.gui.modules.mapTiles.getTile((layer, z, x, y),
                                                         async=True, tag=imageId,
                                                         download=False)
            imageSize = (256,256)
            if tileData is None:
                # The tile was not found locally
                # * in persistent storage (files/sqlite db)
                # * in the tile cache in memory
                # An asynchronous tile download request has been added
                # automatically, so we just now need to notify the
                # QtQuick GUI that it should wait fo the download
                # completed signal.
                #
                # We notify the GUI by returning a 1x1 image.
                return self._tileNotFoundImage, (1,1), pyotherside.format_argb32
                #log.debug("%s NOT FOUND" % imageId)
            #log.debug("RETURNING STUFF %d %s" % (imageSize[0], imageId))
            return bytearray(tileData), imageSize, pyotherside.format_data
        except Exception:
            log.error("tile image provider: loading tile failed")
            log.error(imageId)
            log.error(requestedSize)
            log.exception()

class MapTiles(object):
    def __init__(self, gui):
        self.gui = gui

    @property
    def tileserverPort(self):
        port = self.gui._getTileserverPort()
        if port:
            return port
        else: # None,0 == 0 in QML
            return 0

    def loadTile(self, layerId, z, x, y):
        """
        load a given tile from storage and/or from the network
        True - tile already in storage or in memory
        False - tile download in progress, retry in a while
        """
        #    log.debug(layerId, z, x, y)
        if self.gui.mapTiles.tileInMemory(layerId, z, x, y):
        #      log.debug("available in memory")
            return True
        elif self.gui.mapTiles.tileInStorage(layerId, z, x, y):
        #      log.debug("available in storage")
            return True
        else: # not in memory or storage
            # add a tile download request
            self.gui.mapTiles.addTileDownloadRequest(layerId, z, x, y)
            #      log.debug("downloading, try later")
            return False

class _Search(object):
    _addressSignal = signal.Signal()

    changed = signal.Signal()

    test = signal.Signal()

    def __init__(self, gui):
        self.gui = gui
        self._addressSearchResults = None
        self._addressSearchStatus = "Searching..."
        self._addressSearchInProgress = False
        self._addressSearchThreadName = None
        self._localSearchResults = None
        self._wikipediaSearchResults = None
        self._routeSearchResults = None
        self._POIDBSearchResults = None
        # why are wee keeping our own dictionary of wrapped
        # objects and not just returning a newly wrapped object on demand ?
        # -> because PySide (1.1.1) segfaults if we don't hold any reference
        # on the object returned :)

        # register the thread status changed callback
        threadMgr.threadStatusChanged.connect(self._threadStatusCB)

    def _threadStatusCB(self, threadName, threadStatus):
        if threadName == self._addressSearchThreadName:
            self._addressSearchStatus = threadStatus
            self._addressSignal()

    def address(self, address):
        """Trigger an asynchronous address search for the given term

        :param address: address search query
        :type address: str
        """
        online = self.gui.m.get("onlineServices", None)
        if online:
            self._addressSearchThreadName = online.geocodeAsync(
                address, self._addressSearchCB
            )
        self._addressSearchInProgress = True
        self._addressSignal()

    def addressCancel(self):
        """Cancel the asynchronous address search"""
        threadMgr.cancel_thread(self._addressSearchThreadName)
        self._addressSearchInProgress = False
        self._addressSearchStatus = "Searching..."
        self._addressSignal()



    def _addressSearchCB(self, results):
        """Replace old address search results (if any) with
        new (wrapped) results

        :param results: address search results
        :type results: list
        """
        #self.gui._addressSearchListModel.set_objects(
        #    wrapList(results, wrappers.PointWrapper)
        #)

        self._addressSearchInProgress = False
        self._addressSignal.emit()

    #addressStatus = QtCore.Property(six.text_type,
    #    lambda x: x._addressSearchStatus, notify=_addressSignal)
    #
    #addressInProgress = QtCore.Property(bool,
    #    lambda x: x._addressSearchInProgress, notify=_addressSignal)

class ModRana(object):
    """
    core modRana functionality
    """

    def __init__(self, modrana, gui):
        self.modrana = modrana
        self.gui = gui
        self.modrana.watch("mode", self._modeChangedCB)
        self.modrana.watch("theme", self._themeChangedCB)
        self._theme = Theme(gui)
    # mode

    def _getMode(self):
        return self.modrana.get('mode', "car")

    def _setMode(self, mode):
        self.modrana.set('mode', mode)

    modeChanged = signal.Signal()

    def _modeChangedCB(self, *args):
        """notify when the mode key changes in options"""
        self.modeChanged()

class Theme(object):
    """modRana theme handling"""
    def __init__(self, gui):
        self.gui = gui
        # connect to the first time signal
        self.gui.firstTimeSignal.connect(self._firstTimeCB)
        self.themeModule = None
        self._themeDict = {}
        self.colors = None
        self.modrana = self.gui.modrana
        self.themeChanged.connect(self._notifyQMLCB)

    themeChanged = signal.Signal()

    def _firstTimeCB(self):
        # we need the theme module
        self.themeModule = self.gui.m.get('theme')
        theme = self.themeModule.theme
        # reload the theme dict so that
        # the dict is up to date and
        # then trigger the changed signal
        # and give it the current theme dict
        self.themeChanged(self._reloadTheme(theme))
        # connect to the core theme-modules theme-changed signal
        self.themeModule.themeChanged.connect(self._themeChangedCB)

    def _themeChangedCB(self, newTheme):
        """ Callback from the core theme module
        - reload theme and trigger our own themeChanged signal

        :param newTheme: new theme from the core theme module
        :type newTheme: Theme
        """
        self.themeChanged(self._reloadTheme(newTheme))

    def _notifyQMLCB(self, newTheme):
        """ Notify the QML context that the modRana theme changed

        :param newTheme: the new theme
        :type newTheme: dict
        """
        pyotherside.send("themeChanged", newTheme)

    @property
    def themeId(self):
        return self._themeDict.get("id")

    @themeId.setter
    def themeId(self, themeId):
        self.modrana.set('theme', themeId)

    @property
    def theme(self):
        return self._themeDict

    def _reloadTheme(self, theme):
        """Recreate the theme dict from the new theme object

        :param theme: new modRana Theme object instance
        :type theme: Theme
        """
        themeDict = {
            "id" : theme.id,
            "name" : theme.name,
            "color" : {
                "main_fill" : theme.getColor("main_fill", "#92aaf3"),
                "icon_grid_toggled" : theme.getColor("icon_grid_toggled", "#c6d1f3"),
                "icon_button_normal" : theme.getColor("icon_button_normal", "#c6d1f3"),
                "icon_button_toggled" : theme.getColor("icon_button_toggled", "#3c60fa"),
                "icon_button_text" : theme.getColor("icon_button_text", "black"),
                "page_background" : theme.getColor("page_background", "black"),
                "page_header_text" : theme.getColor("page_header_text", "black"),
            }
        }
        self._themeDict = themeDict
        return themeDict

class Tracklogs(object):
    """Some tracklog specific functionality"""

    SAILFISH_TRACKLOGS_SYMLINK_NAME = "modrana_tracklogs"
    SAILFISH_SYMLINK_PATH = os.path.join(paths.getHOMEPath(), "Documents", SAILFISH_TRACKLOGS_SYMLINK_NAME)

    def __init__(self, gui):
        self.gui = gui
        self.gui.firstTimeSignal.connect(self._firstTimeCB)
        self._sendUpdates = True

    def _firstTimeCB(self):
        # connect to the tracklog update signal, so that we can send
        # track logging state updates to the GUI
        self.gui.modules.tracklog.tracklogUpdated.connect(self._sendUpdateCB)

    def _sendUpdateCB(self):
        """Tracklog has been updated, send the updated info dict to GUI"""
        if self._sendUpdates:
            pyotherside.send("tracklogUpdated", self.gui.modules.tracklog.getStatusDict())

    def setSendUpdates(self, value):
        """Set if tracklog updates should be sent to the GUI layer or not.
        This is used to disable updates when the track recording page is not visible.
        """
        self._sendUpdates = value
        if value:
            self.gui.log.debug("tracklog: enabling logging status updates")
        else:
            self.gui.log.debug("tracklog: disabling logging status updates")

    def sailfishSymlinkExists(self):
        """Report if the easy access symlink on Sailfish OS for tracklogs exists

        :returns: True if the symlink exists, False if not
        :rtype: bool
        """
        return os.path.islink(self.SAILFISH_SYMLINK_PATH)

    def createSailfishSymlink(self):
        """Create symlink from the actual tracklogs folder in the XDG path
        to ~/Documents for easier access to the tracklogs by the users
        """
        self.gui.log.info("tracklogs: creating sailfish tracklogs symlink")
        if self.sailfishSymlinkExists():
            self.gui.log.warning("tracklogs: the Sailfish tracklogs symlink already exists")
        else:
            try:
                os.symlink(self.gui.modrana.paths.getTracklogsFolderPath(), self.SAILFISH_SYMLINK_PATH)
                self.gui.log.info("tracklogs: sailfish tracklogs symlink created")
            except Exception:
                self.gui.log.exception("tracklogs: sailfish tracklogs symlink creation failed")

    def removeSailfishSymlink(self):
        """Remove the easy-access Sailfish OS symlink"""
        self.gui.log.info("tracklogs: removing sailfish tracklogs symlink")
        if not self.sailfishSymlinkExists():
            self.gui.log.warning("tracklogs: the Sailfish tracklogs symlink does not exist")
        else:
            try:
                os.remove(self.SAILFISH_SYMLINK_PATH)
                self.gui.log.info("tracklogs: sailfish tracklogs symlink removed")
            except Exception:
                self.gui.log.exception("tracklogs: sailfish tracklogs symlink removed")

class Routing(object):
    """Qt 5 GUI specific stuff for routing support"""

    def __init__(self, gui):
        self.gui = gui
        self.gui.firstTimeSignal.connect(self._first_time_cb)
        self._sendUpdates = True

    def _first_time_cb(self):
        self.gui.modules.route.routing_done.connect(self._routing_done_cb)

    def _routing_done_cb(self, result):
        if result and result.returnCode == constants.ROUTING_SUCCESS:
            routePoints = result.route.points_lle
            messagePoints = result.route.message_points
            messagePointsLLEM = []
            for mp in messagePoints:
                messagePointsLLEM.append(mp.getLLEM())
            # also add a point for the route end
            if routePoints:
                lastPoint = routePoints[-1]
                lastPointMessage = "You <b>should</b> be near the destination."
                messagePointsLLEM.append((lastPoint[0], lastPoint[1],
                                          lastPoint[2], lastPointMessage))
            self.gui.log.debug("routing successful")
            pyotherside.send("routeReceived", routePoints, messagePointsLLEM)
        else:
            error_message = constants.ROUTING_FAILURE_MESSAGES.get(result.returnCode, "Routing failed.")
            self.gui.log.debug(error_message)
