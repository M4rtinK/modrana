# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# A modRana QML GUI module
# * it inherits everything in the base GUI module
# * overrides default functions and handling
#----------------------------------------------------------------------------
# Copyright 2012, Martin Kolman
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

# PySide
from PySide import QtCore
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtDeclarative import *
from PySide.QtNetwork import *

# modRana imports
import math
from modules.gui_modules.base_gui_module import GUIModule
from datetime import datetime
import time
from modules.gui_modules.gui_qml import drawing
from modules.gui_modules.gui_qml import wrappers
from modules.gui_modules.gui_qml import list_models
from core.fix import Fix
from core import signal
from core.backports import six
from core import constants

global globe

# QML paths
BASE_QML_FOLDER = "modules/gui_modules/gui_qml"
QML_PLATFORM_INDEPENDENT = "qml"
QML_HARMATTAN = "qml_harmattan"
DEFAULT_QML_FOLDER = QML_HARMATTAN
# TODO: use the independent GUI as default
QML_MAIN_FILENAME = "main.qml"


def newlines2brs(text):
  """ QML uses <br> instead of \n for linebreak """
  return re.sub('\n', '<br>', text)


class Logger(object):
  def __init__(self, log=True):
    pass
    self.log = log

  def debug(self, message):
    if self.log:
      print(message)

logger = Logger(log=False)

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

    # Create Qt application and the QDeclarative view
    class ModifiedQDeclarativeView(QDeclarativeView):
      def __init__(self, modrana):
        QDeclarativeView.__init__(self)
        self.modrana = modrana

      def closeEvent(self, event):
        print("shutting down")
        self.modrana.shutdown()

    self.app = QApplication(sys.argv)
    startDragDistance = self.modrana.dmod.getStartDragDistance()
    if startDragDistance:
      self.app.setStartDragDistance(startDragDistance)

    # get screen resolution
    screenRectangle = self.app.desktop().screenGeometry()
    width = screenRectangle.width()
    height = screenRectangle.height()
    print(" @ screen size: %dx%d" % (width, height))
    # NOTE: what about multi-display devices ? :)

    # register custom modRana types
    # NOTE: custom types need to be registered AFTER
    # QApplication is created but BEFORE QDeclarativeView
    # is instantiated, or else horrible breakage occurs :)
    qmlRegisterType(drawing.PieChart, 'Charts', 1, 0, 'PieChart')
    qmlRegisterType(drawing.PieSlice, "Charts", 1, 0, "PieSlice")

    # m-declarative stuff implemented in Python
    qmlRegisterType(Screen, "mpBackend", 1, 0, "Screen")
    qmlRegisterType(Snapshot, "mpBackend", 1, 0, "Snapshot")

    self.view = ModifiedQDeclarativeView(self.modrana)
    self.window = QMainWindow()
    self.window.setWindowTitle("modRana")
    self.window.resize(*size)
    self.window.setCentralWidget(self.view)
    self.view.setResizeMode(QDeclarativeView.SizeRootObjectToView)
    #    self.view.setResizeMode(QDeclarativeView.SizeViewToRootObject)

    # add image providers
    self.iconProvider = IconImageProvider(self)
    self.view.engine().addImageProvider("icons", self.iconProvider)
    # add tiles provider
    self.tilesProvider = TileImageProvider(self)
    self.view.engine().addImageProvider("tiles", self.tilesProvider)

    rc = self.view.rootContext()
    # make core modRana functionality accessible from QML
    modRanaCore = ModRana(self.modrana, self)
    rc.setContextProperty("modrana", modRanaCore)
    # make options accessible from QML
    options = Options(self.modrana)
    rc.setContextProperty("options", options)
    # make GPS accessible from QML
    gps = GPSDataWrapper(self.modrana, self)
    rc.setContextProperty("gps", gps)
    # make the platform accessible from QML
    platform = Platform(self.modrana)
    rc.setContextProperty("platform", platform)
    # make the modules accessible from QML
    modules = Modules(self.modrana)
    rc.setContextProperty("modules", modules)
    # make tile loading accessible from QML
    tiles = MapTiles(self)
    rc.setContextProperty("mapTiles", tiles)
    # make map layers accessible from QML
    layers = MapLayers(self)
    rc.setContextProperty("mapLayers", layers)

    # make constants accessible
    self.constants = self.getConstants()
    rc.setContextProperty("C", self.constants)

    # #register list models
    # self._registerListModels()

    # connect to the close event
    self.window.closeEvent = self._qtWindowClosed
    #self.window.show()

    self.rootObject = None

    self._location = None # location module
    self._mapTiles = None # map tiles module
    self._mapLayers = None # map tiles module

    self._notificationQueue = []

  def firstTime(self):
    self._location = self.m.get('location', None)
    self._mapTiles = self.m.get('mapTiles', None)
    self._mapLayers = self.m.get('mapLayers', None)

    #register list models
    self._registerListModels()

    # trigger the first time signal
    self.firstTimeSignal()

  def getIDString(self):
    return "QML"

  def needsLocalhostTileserver(self):
    """
    the QML GUI needs the localhost tileserver
    for efficient and responsive tile loading
    """
    return False

  def isFullscreen(self):
    return self.window.isFullScreen()

  def toggleFullscreen(self):
    if self.window.isFullScreen():
      self.window.showNormal()
    else:
      self.window.showFullScreen()

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

  def startMainLoop(self):
    """start the main loop or its equivalent"""

    #    print("QML starting main loop")

    if self.modrana.dmod.startInFullscreen():
      self.toggleFullscreen()

    # Create an URL to the QML file
    QMLSubfolder = DEFAULT_QML_FOLDER
    if self.subtypeId  == "indep":
      QMLSubfolder = QML_PLATFORM_INDEPENDENT
    elif self.subtypeId == "harmattan":
      QMLSubfolder = QML_HARMATTAN

    print('QML GUI subtype folder: %s' % QMLSubfolder)

    url = QUrl(os.path.join(BASE_QML_FOLDER, QMLSubfolder, QML_MAIN_FILENAME))
    # Set the QML file and show
    self.view.setSource(url)
    # get the root object
    self.rootObject = self.view.rootObject()

    # start main loop
    self.window.show()

    # handle any notifications that might have come before firstTime
    # (the GUI is not available before firstTime)
    if self._notificationQueue:
      for item in self._notificationQueue:
        self.notify(*item)
      #    print("loaded modules:")
      #    print(sys.modules.keys())
    self.app.exec_()

  #    print("QML main loop started")

  def _qtWindowClosed(self, event):
    print('Qt window closing down')
    self.modrana.shutdown()

  def stopMainLoop(self):
    """stop the main loop or its equivalent"""
    # notify QML GUI first

    # NOTE: due to calling Python properties
    # from onDestruction handlers causing
    # segfault, we need this

    #self.rootObject.shutdown()

    # quit the application
    self.app.exit()
    self.modrana.shutdown()

  def hasNotificationSupport(self):
    return True

  def notify(self, text, msTimeout=5000, icon=""):
    """trigger a notification using the Qt Quick Components
    InfoBanner notification"""

#    # QML uses <br> instead of \n for linebreak
#    text = newlines2brs(text)
#    print("QML GUI notify:\n message: %s, timeout: %d" % (text, msTimeout))
#    if self.rootObject:
#      self.rootObject.notify(text, msTimeout)
#    else:
#      self._notificationQueue.append((text, msTimeout, icon))
    return

  def openUrl(self, url):
    QDesktopServices.openUrl(url)

  def _getTileserverPort(self):
    m = self.m.get("tileserver", None)
    if m:
      return m.getServerPort()
    else:
      return None


  def getConstants(self):
    C = {
      "style" : self._getStyleConstants()
    }
    return C

  def _registerListModel(self, modelName, model):
    """Register a list model to the QML context
    :param modelName: a unique name of the model for the QML context
    :param model: the list model instance
    """
    self.view.rootContext().setContextProperty(modelName, model)

  def _registerListModels(self):
    """Register all list models needed by modRana"""

    # register the layer model
    ml = self.m.get('mapLayers', None)
    if ml:
      # just to make sure that the garbage
      # collector doesn't eat the list model
      # we assign it as a class variable
      wrappedGroupList = map(
        lambda x: wrappers.MapLayerGroupWrapper(x), ml.getGroupList(sort=True)
      )
      wrappedGroupList = list(wrappedGroupList)
      self.layersListModel = list_models.BaseListModel(wrappedGroupList)
      self._registerListModel("mapLayersModel", self.layersListModel)

  def _getLayerListModel(self):
    pass

  def _getStyleConstants(self, highDPI=False):
    # as True == 1 and False == 0,
    # we use the highDPI boolean as a tuple index
    # * highDpi == False -> first value is used
    # * highDpi == True -> second value is used
    i = highDPI
    style = {
      "map": {
        "button": {
          "size": (72, 108)[i],
          "margin": (16, 24)[i],
          "spacing": (16, 24)[i],
        }
      }
    }
    return style

class Platform(QtCore.QObject):
  """make current platform available to QML and integrable as a property"""

  def __init__(self, modrana):
    QtCore.QObject.__init__(self)
    self.modrana = modrana

  @QtCore.Slot(result=bool)
  def isFullscreen(self):
    return self.modrana.gui.isFullscreen()

  @QtCore.Slot()
  def toggleFullscreen(self):
    self.modrana.gui.toggleFullscreen()

  @QtCore.Slot(bool)
  def setFullscreen(self, value):
    self.modrana.gui.setFullscreen(value)

  @QtCore.Slot(result=str)
  def modRanaVersion(self):
    """
    report current modRana version or None if version info is not available
    """
    version = self.modrana.paths.getVersionString()
    if version is None:
      return "unknown"
    else:
      return version

  #  @QtCore.Slot()
  #  def minimise(self):
  #    return self.mieru.platform.minimise()

  #  @QtCore.Slot(result=bool)
  #  def showMinimiseButton(self):
  #    """
  #    Harmattan handles this by the Swype UI and
  #    on PC this should be handled by window decorator
  #    """
  #    return self.mieru.platform.showMinimiseButton()

  @QtCore.Slot(result=bool)
  def showQuitButton(self):
    """
    Harmattan handles this by the Swype UI and
    on PC it is a custom to have the quit action in the main menu
    """
    return self.modrana.dmod.needsQuitButton()

  @QtCore.Slot(result=bool)
  def fullscreenOnly(self):
    """
    Harmattan doesn't need a minimize button
    """
    return self.modrana.dmod.fullscreenOnly()

  @QtCore.Slot(result=bool)
  def incompleteTheme(self):
    """
    The "base" theme is incomplete at the moment (March 2012),
    use fail-safe or local icons.
    Hopefully, this can be removed once the themes are in better shape.
    """
    # the Fremantle theme is incomplete
    return self.modrana.dmod.getDeviceIDString() == "n900"


class Modules(QtCore.QObject):
  """
  modRana module access from QML
  """

  def __init__(self, modrana):
    QtCore.QObject.__init__(self)
    self.modrana = modrana

  @QtCore.Slot(str, str, result=str)
  @QtCore.Slot(str, str, bool, result=str)
  def getS(self, moduleName, functionName, replaceNewlines=True):
    result = self._mCall(moduleName, functionName)
    # QML uses <br> in place of newlines
    if replaceNewlines:
      result = newlines2brs(result)
    return result

  @QtCore.Slot(str, str, result=bool)
  def getB(self, moduleName, functionName):
    return self._mCall(moduleName, functionName)

  @QtCore.Slot(str, str, result=int)
  def getI(self, moduleName, functionName):
    return self._mCall(moduleName, functionName)

  @QtCore.Slot(str, str, result=float)
  def getF(self, moduleName, functionName):
    return self._mCall(moduleName, functionName)

  def _mCall(self, moduleName, functionName):
    """
    call the getter function for a given module
    """
    m = self.modrana.getModule(moduleName, None)
    if m:
      try:
        function = getattr(m, functionName)
        result = function()
        return result
      except Exception:
        import sys
        e = sys.exc_info()[1]
        print("QML GUI: calling function %s on module %s failed" % (functionName, moduleName))
        print(e)
        return None
    else:
      print("QML GUI: module %s not loaded" % moduleName)
      return None


class IconImageProvider(QDeclarativeImageProvider):
  """the IconImageProvider class provides icon images to the QML layer as
  QML does not seem to handle .. in the url very well"""

  def __init__(self, gui):
    QDeclarativeImageProvider.__init__(self, QDeclarativeImageProvider.ImageType.Image)
    self.gui = gui

  def requestImage(self, iconPath, size, requestedSize):
    try:

      #TODO: theme name caching ?
      themeFolder = self.gui.modrana.paths.getThemesFolderPath()
      fullIconPath = os.path.join(themeFolder, iconPath)

      # the path is constructed like this in QML
      # so we can safely just split it like this
      splitPath = iconPath.split("/")
      if not os.path.exists(fullIconPath):
        if splitPath[0] == constants.DEFAULT_THEME_ID:
          # already on default theme and icon path does not exist
          return None
        else:  # try to get the icon from default theme
          splitPath[0] = constants.DEFAULT_THEME_ID
          fullIconPath = os.path.join(themeFolder, *splitPath)
          if not os.path.exists(fullIconPath):
            # icon not found even in the default theme
            return None
      f = open(fullIconPath, 'rb')
      #      print("ICON")
      #      print(iconPath)
      #      print(size)
      #      print(requestedSize)
      img = QImage()
      img.loadFromData(f.read())
      f.close()
      return img
    except Exception:
      import sys
      e = sys.exc_info()[1]
      print("QML GUI: icon image provider: loading icon failed")
      print(e)
      print(os.path.join('themes', iconPath))
      print("Traceback:")
      traceback.print_exc(file=sys.stdout) # find what went wrong

class TileImageProvider(QDeclarativeImageProvider):
  """
  the TileImageProvider class provides images images to the QML map element
  NOTE: this image provider is currently only used as fallback in case
  the localhost tileserver won't start
  """

  def __init__(self, gui):
    QDeclarativeImageProvider.__init__(self, QDeclarativeImageProvider.ImageType.Image)
    self.gui = gui
    self.loading = QImage(1, 1, QImage.Format_RGB32)
    self.ready = QImage(2, 1, QImage.Format_RGB32)
    self.error = QImage(3, 1, QImage.Format_RGB32)
    self.manager = QNetworkAccessManager()

  def requestImage(self, tileInfo, size, requestedSize):
    """
    the tile info should look like this:
    layerID/zl/x/y
    """
    #print("IMAGE REQUESTED")
    #print(tileInfo)
    try:
      # split the string provided by QML
      split = tileInfo.split("/")
      layerId = split[0]
      z = int(split[1])
      x = int(split[2])
      y = int(split[3])

      # get the tile from the tile module
      tileData = self.gui._mapTiles.getTile(layerId, z, x, y)
      if not tileData:
        # print("NO TILEDATA")
        return None

      # create a file-like object
      # f = StringIO(tileData)
      # create image object
      img = QImage()
      # lod the image from in memory buffer
      # img.loadFromData(f.read())
      img.loadFromData(tileData)
      # cleanup
      # f.close()
      #print("OK")
      return img
    except Exception:
      import sys
      e = sys.exc_info()[1]
      print("QML GUI: icon image provider: loading tile failed")
      print(e)
      print(tileInfo)
      traceback.print_exc(file=sys.stdout)


class MapTiles(QtCore.QObject):
  def __init__(self, gui):
    QtCore.QObject.__init__(self)
    self.gui = gui

  @QtCore.Slot(result=int)
  def tileserverPort(self):
    port = self.gui._getTileserverPort()
    if port:
      return port
    else: # None,0 == 0 in QML
      return 0

  @QtCore.Slot(str, int, int, int, result=bool)
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

class MapLayers(QtCore.QObject):
  def __init__(self, gui):
    QtCore.QObject.__init__(self)
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
      for layerId, layer in six.iteritems(self.gui._mapLayers.getLayerDict()):
        self.wrappedLayers[layerId] = wrappers.MapLayerWrapper(layer)
    return self._wrappedLayers

  @QtCore.Slot(str, result=QtCore.QObject)
  def getLayer(self, layerId):
    return self.wrappedLayers.get(layerId, None)

  @QtCore.Slot(str, result=str)
  def getLayerName(self, layerId):
    layer = self.wrappedLayers.get(layerId, None)
    if layer:
      return layer.wo.label
    else:
      return "label for %s unknown" % layerId


class FixWrapper(QtCore.QObject):
  def __init__(self, fix):
    QtCore.QObject.__init__(self)
    self.data = fix

  changed = QtCore.Signal()

  def update(self, fix):
    self.data = fix
    logger.debug("Fix updated with data from %r" % fix)
    self.changed.emit()

  def _mode(self):
    """GPS fix mode:
    0 - no fix
    2 - 2D fix
    3 - 3D fix
    """
    return self.data.mode

  def _lat(self):
    if self.data.position is not None:
      return self.data.position[0]
    else:
      return -1

  def _lon(self):
    if self.data.position is not None:
      return self.data.position[1]
    else:
      return -1

  def _altitude(self):
    return self.data.altitude if self.data.altitude is not None else 0

  def _bearing(self):
    return self.data.bearing if self.data.bearing is not None else 0

  def _speed(self):
    return self.data.speed if self.data.speed is not None else 0

  def _climb(self):
    return self.data.climb if self.data.climb is not None else -1

  def _magnetic_variation(self):
    return self.data.magnetic_variation if self.data.magnetic_variation is not None else -1

  def _sats(self):
    return self.data.sats if self.data.sats is not None else -1

  def _sats_in_use(self):
    return self.data.sats_in_use if self.data.sats_in_use is not None else -1

  def _error(self):
    return float(self.data.error)

  def _valid(self):
    # 0-1 = no fix, 2-3 = 2D/3D fix
    return self.data.mode > 1

  def _altitude_valid(self):
    return self.data.altitude is not None

  def _speed_valid(self):
    return self.data.speed is not None

  def _bearing_valid(self):
    return self.data.bearing is not None

  def _climb_valid(self):
    return self.data.climb is not None

  def _speed_error(self):
    return float(self.data.error)

  def _horizontal_accuracy(self):
    return self.data.horizontal_accuracy if self.data.horizontal_accuracy is not None else -1

  def _vertical_accuracy(self):
    return self.data.vertical_accuracy if self.data.vertical_accuracy is not None else -1

  def _speed_accuracy(self):
    return self.data.speed_accuracy if self.data.speed_accuracy is not None else -1

  def _climb_accuracy(self):
    climbAccuracy = self.data.climb_accuracy
    if climbAccuracy is None or math.isnan(climbAccuracy):
      return -1
    else:
      return climbAccuracy

  def _time_accuracy(self):
    return self.data.time_accuracy if self.data.time_accuracy is not None else -1

  def _gps_time(self):
    return self.data.gps_time if self.data.gps_time is not None else "not available"

  mode = QtCore.Property(int, _mode, notify=changed)
  lat = QtCore.Property(float, _lat, notify=changed)
  lon = QtCore.Property(float, _lon, notify=changed)
  altitude = QtCore.Property(float, _altitude, notify=changed)
  bearing = QtCore.Property(float, _bearing, notify=changed)
  speed = QtCore.Property(float, _speed, notify=changed)
  climb = QtCore.Property(float, _climb, notify=changed)
  magneticVariation = QtCore.Property(float, _magnetic_variation, notify=changed)
  sats = QtCore.Property(int, _sats, notify=changed)
  satsInUse = QtCore.Property(int, _sats_in_use, notify=changed)
  error = QtCore.Property(float, _error, notify=changed)
  valid = QtCore.Property(bool, _valid, notify=changed)
  speedValid = QtCore.Property(bool, _speed_valid, notify=changed)
  bearingValid = QtCore.Property(bool, _bearing_valid, notify=changed)
  altitudeValid = QtCore.Property(bool, _altitude_valid, notify=changed)
  climbValid = QtCore.Property(bool, _climb_valid, notify=changed)
  horizontalAccuracy = QtCore.Property(float, _horizontal_accuracy, notify=changed)
  verticalAccuracy = QtCore.Property(float, _vertical_accuracy, notify=changed)
  speedAccuracy = QtCore.Property(float, _speed_accuracy, notify=changed)
  climbAccuracy = QtCore.Property(float, _climb_accuracy, notify=changed)
  timeAccuracy = QtCore.Property(float, _time_accuracy, notify=changed)
  gpsTime = QtCore.Property(str, _gps_time, notify=changed)

class GPSDataWrapper(QtCore.QObject):
  changed = QtCore.Signal()
  changed_target = QtCore.Signal()
  changed_distance_bearing = QtCore.Signal()

  def __init__(self, modrana, gui):
    QtCore.QObject.__init__(self)
    self.modrana = modrana
    self.gui = gui
    #    self.modrana.connect('good-fix', self._on_good_fix)
    #    self.modrana.connect('no-fix', self._on_no_fix)
    #    self.modrana.connect('target-changed', self._on_target_changed)
    self.modrana.watch('locationUpdated', self._posChangedCB)

    pos = self.modrana.get('pos', constants.DEFAULT_COORDINATES)
    speed = self.modrana.get('speed', 0)
    bearing = self.modrana.get('bearing', 0)
    elevation = self.modrana.get('elevation', 0)
    fix = Fix(pos, elevation, bearing, speed)
    self.gps_data = FixWrapper(fix)
    self.gps_last_good_fix = FixWrapper(fix)
    self.gps_has_fix = False
    self.gps_mode = ''
    #self.astral = Astral()

#  @QtCore.Slot(bool, float, float, bool, float, bool, float, float, QtCore.QObject)
#  def positionChanged(self, valid, lat, lon, altvalid, alt, speedvalid, speed, error, timestamp):
#    if valid:
#      pos = (lat, lon)
#      self._on_good_fix(Fix(pos, alt, bearing, speed))

  def _posChangedCB(self, key, oldValue, newValue):
    """position changed callback"""

    # check validity
    fix = None
    try:
      fix = self.gui._location.getFix()
    except Exception:
      import sys
      e = sys.exc_info()[1]
      print("gui_qml: can't get fix object from location module")
      print(e)
    if fix:
      if fix.mode > 1: # 2 -> 2D fix, 3 -> 3D fix, 0 & 1 -> no fix
        self._on_good_fix(fix)
      else:
        self._on_no_fix()
    else:
      self._on_no_fix()

  def _on_good_fix(self, fix):
    logger.debug("Received good fix")
    self.gps_data.update(fix)
    self.gps_last_good_fix.update(fix)
    self.gps_has_fix = True
    self.gps_mode = fix.mode
    self.changed_distance_bearing.emit()
    self.changed.emit()

  def _on_no_fix(self):
#    self.gps_data.update(gps_data)
    self.gps_has_fix = False
    self.gps_mode = 0
    self.changed_distance_bearing.emit()
    self.changed.emit()

  def _gps_data(self):
    return self.gps_data

  def _gps_last_good_fix(self):
    return self.gps_last_good_fix

  def _gps_has_fix(self):
    return self.gps_has_fix

  def _gps_mode(self):
    return self.gps_mode

  data = QtCore.Property(QtCore.QObject, _gps_data, notify=changed)
  lastGoodFix = QtCore.Property(QtCore.QObject, _gps_last_good_fix, notify=changed)
  hasFix = QtCore.Property(bool, _gps_has_fix, notify=changed)
  mode = QtCore.Property(str, _gps_mode, notify=changed)


class ModRana(QtCore.QObject):
  """
  core modRana functionality
  """

  def __init__(self, modrana, gui):
    QtCore.QObject.__init__(self)
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

  modeChanged = Signal()

  def _modeChangedCB(self, *args):
    """notify when the mode key changes in options"""
    self.modeChanged.emit()

  # theme

  def _getThemeId(self):
    return self.modrana.get('theme', "default")

  def _setThemeId(self, newTheme):
    return self.modrana.set('theme', newTheme)

  def _getTheme(self):
    return self._theme

  themeChanged = Signal()

  def _themeChangedCB(self, *args):
    """notify when the mode key changes in options"""
    self.themeChanged.emit()

  # properties

  mode = QtCore.Property(str, _getMode, _setMode, notify=modeChanged)
  theme_id = QtCore.Property(str, _getThemeId, _setThemeId, notify=themeChanged)
  theme = QtCore.Property(QtCore.QObject, _getTheme, notify=themeChanged)

class Theme(QtCore.QObject):
  """modRana themes"""
  def __init__(self, gui):
    QtCore.QObject.__init__(self)
    self.gui = gui
    # connect to the first time signal
    self.gui.firstTimeSignal.connect(self._firstTimeCB)

  themeChanged = Signal()

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
    self.themeChanged.emit()

  def _getThemeId(self):
    return self.theme.id

  def _setThemeId(self, newTheme):
    return self.modrana.set('theme', newTheme)

  def _getThemeName(self):
    return self.theme.name

  def _getColor(self):
    return self.colors

  id = QtCore.Property(str, _getThemeId, _setThemeId, notify=themeChanged)
  name = QtCore.Property(str, _getThemeName, notify=themeChanged)
  color = QtCore.Property(QtCore.QObject, _getColor, notify=themeChanged)

class ColorsWrapper(QtCore.QObject):
  """Wrapper for modRana theme colors"""
  def __init__(self, theme):
    QtCore.QObject.__init__(self)
    self.t = theme

  colorsChanged = Signal()

  def reloadTheme(self, theme):
    """Replace the current theme with a new one
    and emit the changed signal"""
    self.t = theme
    self.colorsChanged.emit()

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

  main_fill = QtCore.Property(str, _main_fill, notify=colorsChanged)
  icon_grid_toggled = QtCore.Property(str, _icon_grid_toggled, notify=colorsChanged)
  icon_button_normal = QtCore.Property(str, _icon_button_normal, notify=colorsChanged)
  icon_button_toggled = QtCore.Property(str, _icon_button_toggled, notify=colorsChanged)
  icon_button_text = QtCore.Property(str, _icon_button_text, notify=colorsChanged)
  page_header_text = QtCore.Property(str, _page_header_text, notify=colorsChanged)
  page_background = QtCore.Property(str, _page_background, notify=colorsChanged)



class Options(QtCore.QObject):
  """make options available to QML and integrable as a property"""

  def __init__(self, modrana):
    QtCore.QObject.__init__(self)
    self.modrana = modrana

  # like this, the function can accept
  # and return different types to and from QML
  # (basically anything that matches some of the decorators)
  # as per PySide developers, there should be no performance
  # penalty for doing this and the order of the decorators
  # doesn't mater

  @QtCore.Slot(str, bool, result=bool)
  @QtCore.Slot(str, int, result=int)
  @QtCore.Slot(str, str, result=str)
  @QtCore.Slot(str, float, result=float)
  def get(self, key, default):
    """get a value from the modRanas persistent options dictionary"""
    print("GET")
    print(key, default, self.modrana.get(key, default))
    return self.modrana.get(key, default)

  @QtCore.Slot(str, bool)
  @QtCore.Slot(str, int)
  @QtCore.Slot(str, str)
  @QtCore.Slot(str, float)
  def set(self, key, value):
    """set a keys value in modRanas persistent options dictionary"""
    print("SET")
    print(key, value)
    return self.modrana.set(key, value)

  # while the overloaded set function works just fine,
  # it always stores a float, even if an integer is pasted
  # from QML
  # so if you want to make sure an int or a float is stored
  # in options, use the following two functions

  @QtCore.Slot(str, int)
  def setI(self, key, value):
    print("SET int")
    print(key, value)
    return self.modrana.set(key, int(value))

  @QtCore.Slot(str, float)
  def setF(self, key, value):
    print("SET float")
    print(key, value)
    return self.modrana.set(key, float(value))

class Item(QtCore.QObject):
  """implement m-declarative-item"""
  wChanged = QtCore.Signal()
  hChanged = QtCore.Signal()
  opacityChanged = QtCore.Signal()

  def __init__(self):
    QtCore.QObject.__init__(self)
    self.width = 854
    self.height = 480
    self.opacity = 1.0

  def _getWidth(self):
    return self.width

  def _setWidth(self, value):
    self.width = value
    self.wChanged.emit()

  def _getHeight(self):
    return self.height

  def _setHeight(self, value):
    self.height = value
    self.hChanged.emit()

  def _getOpacity(self):
    return self.opacity

  def _setOpacity(self, value):
    self.opacity = value
    self.opacityChanged.emit()

  width = QtCore.Property(int, _getWidth, _setWidth, notify=wChanged)
  height = QtCore.Property(int, _getHeight, _setHeight, notify=hChanged)
  opacity = QtCore.Property(int, _getOpacity, _setOpacity, notify=hChanged)

class Screen(QtCore.QObject):
  """implement m-declarative-screen"""

  def __init__(self):
    QtCore.QObject.__init__(self)
    self.width = 854
    self.height = 480

  def _width(self):
    return self.width

  def _height(self):
    return self.height

  wChanged= QtCore.Signal()
  hChanged= QtCore.Signal()
  displayWidth = QtCore.Property(int, _width, notify=wChanged)
  displayHeight = QtCore.Property(int, _height, notify=hChanged)

class Snapshot(QDeclarativeItem):
  """implement m-declarative-snapshot"""
  wChanged = QtCore.Signal()
  hChanged = QtCore.Signal()

  def __init__(self):
    QDeclarativeItem.__init__(self)
    self.snapshotWidth = 854
    self.snapshotHeight = 480

  def _getSnapshotWidth(self):
    return self.snapshotWidth

  def _setSnapshotWidth(self, value):
    pass

# hotfix for recursive loop
  # TODO: find what's causing it
#    self.snapshotWidth = value
#    self.wChanged.emit()

  def _getSnapshotHeight(self):
    return self.snapshotHeight

  def _setSnapshotHeight(self, value):
    pass
# hotfix for recursive loop
#    self.snapshotHeight = value
#    self.hChanged.emit()

  snapshotWidth = QtCore.Property(int, _getSnapshotWidth, _setSnapshotWidth, notify=wChanged)
  snapshotHeight = QtCore.Property(int, _getSnapshotHeight, _setSnapshotHeight, notify=hChanged)


