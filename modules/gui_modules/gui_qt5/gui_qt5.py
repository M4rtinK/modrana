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
from core import point

import logging
no_prefix_log = logging.getLogger()
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
        "highlight" : False,
        "mDistance" : 0,  # will be filled in on QML side
        "db_id" : getattr(point, "db_index", None),
        "category_id" : getattr(point, "db_category_index", None)
    }

class QMLGUI(GUIModule):
    """A Qt 5 + QtQuick 2 GUI module"""

    def __init__(self, *args, **kwargs):
        GUIModule.__init__(self, *args, **kwargs)

        # some constants
        self.msLongPress = 400
        self.centeringDisableThreshold = 2048
        self.firstTimeSignal = signal.Signal()
        size = (800, 480) # initial window size
        self._screen_size = None

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

        # log what version of PyOtherSide we are using
        # - we log this without prefix as this shows up early
        #   during startup, so it looks nicer that way :-)
        no_prefix_log.info("using PyOtherSide %s", pyotherside.version)

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

        # POI handling for the QML context
        self.POI = POI(self)

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

        # turn by turn navigation
        self.navigation = Navigation(self)

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
        return self._screen_size

    def getModRanaVersion(self):
        """
        report current modRana version or None if version info is not available
        """
        version = self.modrana.paths.version_string
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
            (lat, lon) = None, None

        # magnetic variation might sometimes not be set
        magnetic_variation = 0.0
        magnetic_variation_valid = False
        if fix.magnetic_variation is not None:
            magnetic_variation = fix.magnetic_variation
            magnetic_variation_valid = True
        pyotherside.send("pythonPositionUpdate", {
            "latitude" : lat,
            "longitude" : lon,
            "altitude" : fix.altitude,
            "speed" : fix.speed,
            "verticalSpeed" : fix.climb,
            "horizontalAccuracy" : fix.horizontal_accuracy,
            "verticalAccuracy" : fix.vertical_accuracy,
            "direction" : fix.bearing,
            "magneticVariation" : magnetic_variation,
            "magneticVariationValid" : magnetic_variation_valid,
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
            "show_quit_button": self.showQuitButton(),
            "fullscreen_only": self.modrana.dmod.fullscreen_only,
            "should_start_in_fullscreen": self.shouldStartInFullscreen(),
            "needs_back_button": self.modrana.dmod.needs_back_button,
            "needs_page_background": self.modrana.dmod.needs_page_background,
            "lastKnownPos" : self.get("pos", None),
            "gpsEnabled" : self.get("GPSEnabled", True),
            "posFromFile" : self.get("posFromFile", None),
            "nmeaFilePath" : self.get("NMEAFilePath", None),
            "layerTree" : self.modules.mapLayers.getLayerTree(),
            "dictOfLayerDicts" : self.modules.mapLayers.getDictOfLayerDicts(),
            "themesFolderPath" : os.path.abspath(self.modrana.paths.themes_folder_path),
            "sailfish" : self.dmod.device_id == "jolla",
    	    "device_type" : self.modrana.dmod.device_type,
            "highDPI" : self.highDPI,
            "defaultTileStorageType" : self.modrana.dmod.defaultTileStorageType,
            "aboutModrana" : self._get_about_info()

        }
        return values

    def _set_screen_size(self, screen_size):
        """A method called by QML to report current screen size in pixels.

        :param screen_size: screen width and height in pixels
        :type screen_size: a tuple of integers
        """
        self._screen_size = screen_size

    def _get_about_info(self):
        info = self.modules.info
        return {
            "email_address" : info.email_address,
            "website_url" : info.website_url,
            "source_repository_url" : info.source_repository_url,
            "discussion_url" : info.main_discussion[0],
            "translation_url" : info.translation_url,
            "pay_pal_url" : info.pay_pal_url,
            "flattr_url" : info.flattr_url,
            "gratipay_url" : info.gratipay_url,
            "bitcoin_address" : info.bitcoin_address
        }


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

class POI(object):
    """An easy to use POI interface for the QML context"""
    def __init__(self, gui):
        self.gui = gui

    def list_used_categories(self):
        db = self.gui.modules.storePOI.db
        cat_list = []
        for category in db.list_used_categories():
            category_id = category[2]
            poi_count = len(db.get_all_poi_from_category(category_id))  # do this more efficiently
            cat_list.append({
                "name" : category[0],
                "description" : category[1],
                "poi_count" : poi_count,
                "category_id" : category_id
            })
        return cat_list

    def _db_changed(self):
        """Notify QML that the POI database has been changed.

        This can be used to reload various caches and views.
        """
        pyotherside.send("poiDatabaseChanged")

    def _new_poi_added(self, new_poi_dict):
        """Notify QML that a new POI has been added"""
        pyotherside.send("newPoiAddedToDatabase", new_poi_dict)

    def store_poi(self, point_dict):
        success = False
        db = self.gui.modules.storePOI.db
        name = point_dict.get("name")
        description = point_dict.get("description", "")
        lat = point_dict.get("lat")
        lon = point_dict.get("lon")
        category_id = point_dict.get("category_id")
        # make sure lat & lon is a floating point number
        try:
            lat = float(lat)
            lon = float(lon)
        except Exception:
            self.gui.log.exception("can't save POI: lat or lon not float")
        # default to "Other" if no category is provided
        if category_id is None:
            category_id = 11  # TODO: this should ge dynamically queried from the database
        # sanity check
        if name and lon is not None and lat is not None:
            poi = point.POI(name=name,
                            description=description,
                            lat=lat,
                            lon=lon,
                            db_cat_id=category_id)
            self.gui.log.info("saving POI: %s", poi)
            poi_db_index = db.store_poi(poi)
            self.gui.log.info("POI saved")
            success = True
            # notify QML a new POI was added
            new_poi_dict = point2dict(point.POI(name,
                                                description,
                                                lat,
                                                lon,
                                                category_id, poi_db_index))
            self._new_poi_added(new_poi_dict)
        else:
            self.gui.log.error("cant's save poi, missing name or coordinates: %s", point_dict)
        if success:
            self._db_changed()
        return success

    def get_all_poi_from_category(self, category_id):
        db = self.gui.modules.storePOI.db
        poi_list = []
        for poi_tuple in db.get_all_poi_from_category(category_id):
            # TODO: to this already in poi_db
            (name, desc, lat, lon, poi_id) = poi_tuple
            poi_dict = point2dict(point.POI(name, desc, lat, lon, category_id, poi_id))
            poi_list.append(poi_dict)
        return poi_list

    def delete_poi(self, poi_db_index):
        log.debug("deleting POI with db index %s", poi_db_index)
        db = self.gui.modules.storePOI.db
        db.delete_poi(poi_db_index)
        self._db_changed()

class Search(object):
    """An easy to use search interface for the QML context"""

    def __init__(self, gui):
        self.gui = gui
        self._threadsInProgress = {}
        # register the thread status changed callback
        threadMgr.threadStatusChanged.connect(self._threadStatusCB)

    def search(self, searchId, query, searchPoint=None):
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
            if searchId == "local" and searchPoint:
                pointInstance = point.Point(searchPoint.latitude, searchPoint.longitude)
                threadId = searchFunction(query, callback, around=pointInstance)
            else:
                threadId = searchFunction(query, callback)
            self._threadsInProgress[threadId] = searchId
            return threadId

    def _searchCB(self, searchId, results):
        """Handle address search results

        :param list results: address search results
        """
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
            themeFolder = self.gui.modrana.paths.themes_folder_path
            # fullIconPath = os.path.join(themeFolder, imageId)
            # the path is constructed like this in QML
            # so we can safely just split it like this
            splitPath = imageId.split("/")
            # remove any Ambiance specific garbage appended by Silica
            splitPath[-1] = splitPath[-1].rsplit("?")[0]
            fullIconPath = os.path.join(themeFolder, *splitPath)
            extension = os.path.splitext(fullIconPath)[1]
            # set correct data format based on the extension
            if extension.lower() == ".svg":
                data_format = pyotherside.format_svg_data
            else:
                data_format = pyotherside.format_data

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
            # We only set height or else SVG icons would be squished if a square icon
            # has been requested but the SVG icon is not square. If just height is
            # we the clever SVG handling code (which I wrote ;-) ) will handle this correctly. :)
            return utils.internal_get_file_contents(fullIconPath), (-1, requestedSize[1]), data_format
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
                                                         asynchronous=True, tag=imageId,
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
            log.exception("tile image provider exception")

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
                "main_highlight_fill" : theme.getColor("main_highlight_fill", "#f5f5f5"),
                "icon_grid_toggled" : theme.getColor("icon_grid_toggled", "#c6d1f3"),
                "icon_button_normal" : theme.getColor("icon_button_normal", "#c6d1f3"),
                "icon_button_toggled" : theme.getColor("icon_button_toggled", "#3c60fa"),
                "icon_button_text" : theme.getColor("icon_button_text", "black"),
                "page_background" : theme.getColor("page_background", "black"),
                "list_view_background" : theme.getColor("list_view_background", "#d2d2d2d"),
                "page_header_text" : theme.getColor("page_header_text", "black"),
            }
        }
        self._themeDict = themeDict
        return themeDict

class Tracklogs(object):
    """Some tracklog specific functionality"""

    SAILFISH_TRACKLOGS_SYMLINK_NAME = "modrana_tracklogs"
    SAILFISH_SYMLINK_PATH = os.path.join(paths.get_home_path(), "Documents", SAILFISH_TRACKLOGS_SYMLINK_NAME)

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
                os.symlink(self.gui.modrana.paths.tracklog_folder_path, self.SAILFISH_SYMLINK_PATH)
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

    def request_route(self, route_request):
        waypoints = []
        self.gui.log.debug("REQUEST:")
        self.gui.log.debug(route_request)
        for waypoint_dict in route_request["waypoints"]:
            waypoint = point.Waypoint(lat=waypoint_dict["latitude"],
                                      lon=waypoint_dict["longitude"],
                                      heading=waypoint_dict["heading"])
            waypoints.append(waypoint)
            self.gui.modules.route.waypoints_route(waypoints)

    def _first_time_cb(self):
        self.gui.modules.route.routing_done.connect(self._routing_done_cb)

    def _routing_done_cb(self, result):
        if result and result.returnCode == constants.ROUTING_SUCCESS:
            route_points = result.route.points_lle
            message_points = result.route.message_points
            message_points_llemi = []
            for mp in message_points:
                message_points_llemi.append(mp.llemi)
            # also add a point for the route end
            if route_points:
                lastPoint = route_points[-1]
                lastPointMessage = "You <b>should</b> be near the destination."
                message_points_llemi.append((lastPoint[0], lastPoint[1],
                                            lastPoint[2], lastPointMessage))

            # TODO: this should really be done in the route module itself somehow
            self.gui.modules.route.process_and_save_directions(result.route)

            self.gui.log.debug("routing successful")
            pyotherside.send("routeReceived",
                             {"points" : route_points,
                              "messagePoints" : message_points_llemi}
                             )
        else:
            error_message = constants.ROUTING_FAILURE_MESSAGES.get(result.returnCode, "Routing failed.")
            self.gui.log.debug(error_message)


class Navigation(object):
    """Qt 5 GUI specific stuff for turn by turn navigation support"""

    def __init__(self, gui):
        self.gui = gui
        self.gui.firstTimeSignal.connect(self._firstTimeCB)
        self.tbt = None

    def _firstTimeCB(self):
        # the module machinery is not yet really setup at init time,
        # so we need to do stuff involving modRana modules only
        # at the first time signal
        self.tbt = self.gui.modules.turnByTurn
        # connect to signals
        self.tbt.navigation_started.connect(self._navigation_started_cb)
        self.tbt.navigation_stopped.connect(self._navigation_stopped_cb)
        self.tbt.destination_reached.connect(self._destination_reached_cb)
        self.tbt.rerouting_triggered.connect(self._rerouting_triggered_cb)
        self.tbt.current_step_changed.connect(self._current_step_changed_cb)

    def _navigation_started_cb(self):
        pyotherside.send("navigationStarted")

    def _navigation_stopped_cb(self):
        pyotherside.send("navigationStopped")

    def _destination_reached_cb(self):
        pyotherside.send("navigationDestionationReached")

    def _rerouting_triggered_cb(self):
        pyotherside.send("navigationReroutingTriggered")

    def _current_step_changed_cb(self, step_point):
        step_dict = {
            "message" : step_point.description,
            "latitude" : step_point.lat,
            "longitude" : step_point.lon,
            "icon" : step_point.icon,
        }
        pyotherside.send("navigationCurrentStepChanged", step_dict)

    def start(self):
        self.tbt.start_tbt()

    def stop(self):
        self.tbt.stop_tbt()
