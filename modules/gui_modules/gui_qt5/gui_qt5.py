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
import os
import sys
import re
import traceback

try:
    from StringIO import StringIO # python 2
except ImportError:
    from io import StringIO # python 3
from pprint import pprint

# modRana imports
import math
from modules.gui_modules.base_gui_module import GUIModule
from datetime import datetime
import time

from core.fix import Fix
from core import signal
from core.backports import six
from core import constants
from core.threads import threadMgr


def newlines2brs(text):
    """ QML uses <br> instead of \n for linebreak """
    return re.sub('\n', '<br>', text)

def getModule(m, d, i):
    return QMLGUI(m, d, i)


class QMLGUI(GUIModule):
    """A Qt + QML GUI module"""

    def __init__(self, m, d, i):
        GUIModule.__init__(self, m, d, i)

        # some constants
        self.msLongPress = 400
        self.centeringDisableThreshold = 2048
        self.firstTimeSignal = signal.Signal()
        size = (800, 480) # initial window size

        # window state
        self.fullscreen = False

        # get screen resolution
        # TODO: implement this
        #screenWH = self.getScreenWH()
        #print(" @ screen size: %dx%d" % screenWH)
        #if self.highDPI:
        #    print(" @ high DPI")
        #else:
        #    print(" @ normal DPI")

        # NOTE: what about multi-display devices ? :)

        ## add image providers
        #self.iconProvider = IconImageProvider(self)
        #self.view.engine().addImageProvider("icons", self.iconProvider)
        ## add tiles provider
        #self.tilesProvider = TileImageProvider(self)
        #self.view.engine().addImageProvider("tiles", self.tilesProvider)

        ## make constants accessible
        #self.constants = self.getConstants()
        #rc.setContextProperty("C", self.constants)

        ## connect to the close event
        #self.window.closeEvent = self._qtWindowClosed
        ##self.window.show()

        self._notificationQueue = []

    def firstTime(self):
        self._location = self.m.get('location', None)
        self._mapTiles = self.m.get('mapTiles', None)
        self._mapLayers = self.m.get('mapLayers', None)

        # trigger the first time signal
        self.firstTimeSignal()

    def getIDString(self):
        return "Qt5"

    def needsLocalhostTileserver(self):
        """
        the QML GUI needs the localhost tileserver
        for efficient and responsive tile loading
        """
        return False

    def isFullscreen(self):
        return self.window.isFullScreen()

    def toggleFullscreen(self):
        # TODO: implement this
        pass

    def setFullscreen(self, value):
        if value == True:
            self.window.showFullScreen()
        else:
            self.window.showNormal()

    def setCDDragThreshold(self, threshold):
        """set the threshold which needs to be reached to disable centering while dragging
        basically, larger threshold = longer drag is needed to disable centering
        default value = 2048
        """
        self.centeringDisableThreshold = threshold

    def hasNotificationSupport(self):
        return True

    def notify(self, text, msTimeout=5000, icon=""):
        """trigger a notification using the Qt Quick Components
        InfoBanner notification"""
        # TODO: implement this

        #    # QML uses <br> instead of \n for linebreak
        #    text = newlines2brs(text)
        #    print("QML GUI notify:\n message: %s, timeout: %d" % (text, msTimeout))
        #    if self.rootObject:
        #      self.rootObject.notify(text, msTimeout)
        #    else:
        #      self._notificationQueue.append((text, msTimeout, icon))
        return

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

    def getConstants(self):
        C = {
            "style": self._getStyleConstants()
        }
        return C

    def _getStyleConstants(self):
        # as True == 1 and False == 0,
        # we use the highDPI boolean as a tuple index
        # * highDpi == False -> first value is used
        # * highDpi == True -> second value is used
        i = self.highDPI

        style = {
            "m" : (1, 2)[i], # approximate size multiplier
            "main" : {
                "multiplier" : (1, 2)[i],
                "spacing" : (8, 16)[i],
                "spacingBig" : (16, 32)[i]
            },
            "button" : {
                "selector" : {
                    "width" : (200, 400)[i],
                    "height" : (80, 160)[i],
                    },
                "icon" : {
                    "size" : (80, 160)[i]
                },
                "iconGrid" : {
                    "size" : (100, 200)[i],
                    "radius" : (10, 20)[i]
                },
                "generic" : {
                    "height" : (60, 120)[i]
                }
            },
            "dialog" : {
                "item" : {
                    "height" : (80, 160)[i]
                }
            },

            "map": {
                "button": {
                    "size": (72, 108)[i],
                    "margin": (16, 24)[i],
                    "spacing": (16, 24)[i],
                    },
                "scaleBar" : {
                    "border" : (2, 4)[i],
                    "height" : (4, 8)[i],
                    "fontSize" : (24, 48)[i],

                    },
                },
            "listView" : {
                "spacing" : (8, 16)[i],
                "cornerRadius" : (8, 16)[i],
                "itemBorder" : (20, 40)[i],
                }
        }
        return style


class Platform(object):
    """make current platform available to QML and integrable as a property"""

    def __init__(self, modrana):
        self.modrana = modrana

    @property
    def modRanaVersion(self):
        """
        report current modRana version or None if version info is not available
        """
        version = self.modrana.paths.getVersionString()
        if version is None:
            return "unknown"
        else:
            return version

    @property
    def showQuitButton(self):
        """
        Harmattan handles this by the Swype UI and
        on PC it is a custom to have the quit action in the main menu
        """
        return self.modrana.dmod.needsQuitButton()

    @property
    def fullscreenOnly(self):
        """
        Harmattan doesn't need a minimize button
        """
        return self.modrana.dmod.fullscreenOnly()


#class IconImageProvider(QDeclarativeImageProvider):
#    """the IconImageProvider class provides icon images to the QML layer as
#    QML does not seem to handle .. in the url very well"""
#
#    def __init__(self, gui):
#        QDeclarativeImageProvider.__init__(self, QDeclarativeImageProvider.ImageType.Image)
#        self.gui = gui
#
#    def requestImage(self, iconPath, size, requestedSize):
#        try:
#
#            #TODO: theme name caching ?
#            themeFolder = self.gui.modrana.paths.getThemesFolderPath()
#            fullIconPath = os.path.join(themeFolder, iconPath)
#
#            # the path is constructed like this in QML
#            # so we can safely just split it like this
#            splitPath = iconPath.split("/")
#            if not os.path.exists(fullIconPath):
#                if splitPath[0] == constants.DEFAULT_THEME_ID:
#                    # already on default theme and icon path does not exist
#                    return None
#                else:  # try to get the icon from default theme
#                    splitPath[0] = constants.DEFAULT_THEME_ID
#                    fullIconPath = os.path.join(themeFolder, *splitPath)
#                    if not os.path.exists(fullIconPath):
#                        # icon not found even in the default theme
#                        return None
#            f = open(fullIconPath, 'rb')
#            #      print("ICON")
#            #      print(iconPath)
#            #      print(size)
#            #      print(requestedSize)
#            img = QImage()
#            img.loadFromData(f.read())
#            f.close()
#            return img
#        except Exception:
#            import sys
#
#            e = sys.exc_info()[1]
#            print("QML GUI: icon image provider: loading icon failed")
#            print(e)
#            print(os.path.join('themes', iconPath))
#            print("Traceback:")
#            traceback.print_exc(file=sys.stdout) # find what went wrong
#
#
#class TileImageProvider(QDeclarativeImageProvider):
#    """
#    the TileImageProvider class provides images images to the QML map element
#    NOTE: this image provider is currently only used as fallback in case
#    the localhost tileserver won't start
#    """
#
#    def __init__(self, gui):
#        QDeclarativeImageProvider.__init__(self, QDeclarativeImageProvider.ImageType.Image)
#        self.gui = gui
#        self.loading = QImage(1, 1, QImage.Format_RGB32)
#        self.ready = QImage(2, 1, QImage.Format_RGB32)
#        self.error = QImage(3, 1, QImage.Format_RGB32)
#        self.manager = QNetworkAccessManager()
#
#    def requestImage(self, tileInfo, size, requestedSize):
#        """
#        the tile info should look like this:
#        layerID/zl/x/y
#        """
#        #print("IMAGE REQUESTED")
#        #print(tileInfo)
#        try:
#            # split the string provided by QML
#            split = tileInfo.split("/")
#            layerId = split[0]
#            z = int(split[1])
#            x = int(split[2])
#            y = int(split[3])
#
#            # get the tile from the tile module
#            tileData = self.gui._mapTiles.getTile(layerId, z, x, y)
#            if not tileData:
#                # print("NO TILEDATA")
#                return None
#
#            # create a file-like object
#            # f = StringIO(tileData)
#            # create image object
#            img = QImage()
#            # lod the image from in memory buffer
#            # img.loadFromData(f.read())
#            img.loadFromData(tileData)
#            # cleanup
#            # f.close()
#            #print("OK")
#            return img
#        except Exception:
#            import sys
#
#            e = sys.exc_info()[1]
#            print("QML GUI: icon image provider: loading tile failed")
#            print(e)
#            print(tileInfo)
#            traceback.print_exc(file=sys.stdout)


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
        #    print(layerId, z, x, y)
        if self.gui._mapTiles.tileInMemory(layerId, z, x, y):
        #      print("available in memory")
            return True
        elif self.gui._mapTiles.tileInStorage(layerId, z, x, y):
        #      print("available in storage")
            return True
        else: # not in memory or storage
            # add a tile download request
            self.gui._mapTiles.addTileDownloadRequest(layerId, z, x, y)
            #      print("downloading, try later")
            return False


class MapLayers(object):
    def __init__(self, gui):
        self.gui = gui

        self._wrappedLayers = None
        # why are wee keeping our own dictionary of wrapped
        # layers and not just returning a newly wrapped object on demand ?
        # -> because PySide (1.1.1) segfaults if we don't hold any reference
        # on the object returned :)

    @property
    def wrappedLayers(self):
        # make sure the wrapped layer dict has benn initialized
        # (we can't do that at init, as at that time the
        # map layers module is not yet loaded)
        if self._wrappedLayers is None:
            self._wrappedLayers = {}
            #for layerId, layer in six.iteritems(self.gui._mapLayers.getLayerDict()):
            #    self.wrappedLayers[layerId] = wrappers.MapLayerWrapper(layer)
        return self._wrappedLayers

    def getLayer(self, layerId):
        return self.wrappedLayers.get(layerId, None)

    def getLayerName(self, layerId):
        layer = self.wrappedLayers.get(layerId, None)
        if layer:
            return layer.wo.label
        else:
            return "label for %s unknown" % layerId

class Search(object):
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
        #if threadName == constants.THREAD_ADDRESS_SEARCH:
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

    # theme

    def _getThemeId(self):
        return self.modrana.get('theme', "default")

    def _setThemeId(self, newTheme):
        return self.modrana.set('theme', newTheme)

    def _getTheme(self):
        return self._theme

    themeChanged = signal.Signal()

    def _themeChangedCB(self, *args):
        """notify when the mode key changes in options"""
        self.themeChanged()

    # properties
    #
    #mode = QtCore.Property(str, _getMode, _setMode, notify=modeChanged)
    #theme_id = QtCore.Property(str, _getThemeId, _setThemeId, notify=themeChanged)
    #theme = QtCore.Property(QtCore.QObject, _getTheme, notify=themeChanged)


class Theme(object):
    """modRana themes"""

    def __init__(self, gui):
        self.gui = gui
        # connect to the first time signal
        self.gui.firstTimeSignal.connect(self._firstTimeCB)
        self.themeModule = None
        self.theme = None
        self.colors = None
        self.modrana = self.gui.modrana

    themeChanged = signal.Signal()

    def _firstTimeCB(self):
        # we need the them module
        self.themeModule = self.gui.m.get('theme')
        self.theme = self.themeModule.theme
        self.colors = ColorsWrapper(self.theme)
        # connect to the theme changed signal
        self.themeModule.themeChanged.connect(self._themeChangedCB)

    def _themeChangedCB(self, newTheme):
        self.theme = newTheme
        self.colors.reloadTheme(self.theme)
        self.themeChanged()

    def _getThemeId(self):
        return self.theme.id

    def _setThemeId(self, newTheme):
        return self.modrana.set('theme', newTheme)

    def _getThemeName(self):
        return self.theme.name

    def _getColor(self):
        return self.colors

    #id = QtCore.Property(str, _getThemeId, _setThemeId, notify=themeChanged)
    #name = QtCore.Property(str, _getThemeName, notify=themeChanged)
    #color = QtCore.Property(QtCore.QObject, _getColor, notify=themeChanged)


class ColorsWrapper(object):
    """Wrapper for modRana theme colors"""

    def __init__(self, theme):
        self.t = theme

    colorsChanged = signal.Signal()

    def reloadTheme(self, theme):
        """Replace the current theme with a new one
        and emit the changed signal"""
        self.t = theme
        self.colorsChanged()

    def _main_fill(self):
        return self.t.getColor("main_fill", "#92aaf3")

    def _icon_grid_toggled(self):
        return self.t.getColor("icon_grid_toggled", "#c6d1f3")

    def _icon_button_normal(self):
        return self.t.getColor("icon_button_normal", "#c6d1f3")

    def _icon_button_toggled(self):
        return self.t.getColor("icon_button_toggled", "#3c60fa")

    def _icon_button_text(self):
        return self.t.getColor("icon_button_text", "black")

    def _page_background(self):
        return self.t.getColor("page_background", "black")

    def _page_header_text(self):
        return self.t.getColor("page_header_text", "black")

    #main_fill = QtCore.Property(str, _main_fill, notify=colorsChanged)
    #icon_grid_toggled = QtCore.Property(str, _icon_grid_toggled, notify=colorsChanged)
    #icon_button_normal = QtCore.Property(str, _icon_button_normal, notify=colorsChanged)
    #icon_button_toggled = QtCore.Property(str, _icon_button_toggled, notify=colorsChanged)
    #icon_button_text = QtCore.Property(str, _icon_button_text, notify=colorsChanged)
    #page_header_text = QtCore.Property(str, _page_header_text, notify=colorsChanged)
    #page_background = QtCore.Property(str, _page_background, notify=colorsChanged)