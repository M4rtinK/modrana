#!/usr/bin/python
#----------------------------------------------------------------------------
# Rana main GUI.  Displays maps, for use on a mobile device
#
# Controls:
#   * click on the overlay text to change fields displayed
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
#----------------------------------------------------------------------------
modulesFolder = 'modules'
import sys
sys.path.append(modulesFolder)
import time
startTimestamp = time.time()
import pygtk
pygtk.require('2.0')
import gobject
import gtk
import math
import traceback
import os
from gtk import gdk
from math import radians
from configobj import ConfigObj
importsDoneTimestamp = time.time()


def createFolderPath(newPath):
  """
  Creat a path for a directory and all needed parent forlders
  -> parent directoryies will be created
  -> if directory already exists, then do nothing
  -> if there is another filsystem object (like a file) with the same name, raise an exception
  """
  if not newPath:
    print("cannot create folder, wrong path: ", newPath)
    return False
  if os.path.isdir(newPath):
    return True
  elif os.path.isfile(newPath):
    print("cannot create directory, file already exists: '%s'" % newPath)
    return False
  else:
    print("creating path: %s" % newPath)
    head, tail = os.path.split(newPath)
    if head and not os.path.isdir(head):
        mkdirs(head)
    if tail:
        os.mkdir(newPath)
    return True

def update1(mapWidget):
  mapWidget.update()
  return(True)

def update2(mapWidget):
  mapWidget.checkForRedraw()
  return(True)

def simplePythagoreanDistance(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx**2 + dy**2)

class MapWidget(gtk.Widget):
  __gsignals__ = { \
    'realize': 'override',
    'expose-event' : 'override',
    'size-allocate': 'override',
    'size-request': 'override',
    }
  def __init__(self,device):
    gtk.Widget.__init__(self)
    self.draw_gc = None
    self.device = device
    self.dmod = None # device specific module
    self.currentDrawMethod = self.fullDrawMethod

    self.centeringDisableTreshold = 2048

    self.msLongPress = 400


    """ setting this both to 100 and 1 in mapView and gpsd fixes the arow orientation bug """
    self.timer1 = gobject.timeout_add(100, update1, self) #default 100
    self.timer3 = None # will be used for timing long press events
    self.d = {} # persistant dictionary of data
    self.m = {} # dictionary of loaded modules
    self.watches = {} # List of data change watches
    self.maxWatchId = 0
    self.watch('needRedraw', self._checkForRedrawCB) # react on redraw requests
    # TODO: add a function for directly requesting redraw

    self.mapRotationAngle = 0 # in radians
    self.notMovingSpeed = 1 # in m/s

    self.topWindow = None

    self.redraw = True

    self.showRedrawTime = False
    
    # map center shifting variables
    self.centerShift = (0,0)

    # alternative map drag variables
    self.altMapDragEnabled = False
    self.altMapDragInProgress = False
    self.shift = (0,0,0,0)

    self.defaulMethodBindings() # use default map dragging method binding

    self.lastFullRedraw = time.time()
    self.lastFullRedrawRequest = time.time()

    # map layers
    self.mapLayers = {}
    self.notificationModule = None

    # per mode options
    # NOTE: this variable is automatically saved by the
    # options module
    self.keyModifiers = {}

  def loadModules(self):
    """Load all modules from the specified directory"""

    device = self.device
    print "importing modules:"
    start = time.clock()
    self.initInfo={
              'modrana': self,
              'device': device, # TODO: do this directly
              'name': ""
             }

    # get possible module names
    moduleNames = self._getModuleNamesFromFolder(modulesFolder)
    loadModule = self._loadModule
    # load if possible
    for moduleName in moduleNames:
        # filter out .py
        moduleName = moduleName.split('.')[0]
        loadModule(moduleName, moduleName[4:])

    # load the device specific module
    deviceModulesPath = os.path.join(modulesFolder, "device_modules")
    sys.path.append(deviceModulesPath)
    dmod = loadModule("device_%s" % device, "device")
    if dmod == None:
      print("modRana: loading Neo device module as failsafe")
      device = "neo"
      dmod = loadModule("device_%s" % device, "device")
    self.dmod = dmod

    print "Loaded all modules in %1.2f ms, initialising" % (1000 * (time.clock() - start))

    # make sure all modules have the device module and other variables before first time
    for m in self.m.values():
      m.modrana = self # make this class accessible from modules
      m.dmod = self.dmod

    # as the options module should be already loaded, we can update the viewport
    self._updateViewport()

    # run what needs to be done before firstTime is called
    self._modulesLoadedPreFirstTime()

    start = time.clock()
    for m in self.m.values():
      m.firstTime()

    # run what needs to be done after firstTime is called
    self._modulesLoadedPostFirstTime()

    # get the notication module
    self.notificationModule = self.m.get('notification', None)

    print "Initialization complete in %1.2f ms" % (1000 * (time.clock() - start))

  def _getModuleNamesFromFolder(self,folder):
    """list a given folder and find all possible module names"""

    return filter(lambda x: x[0:4]=="mod_" and x[-4:]!=".pyc",os.listdir(folder))

  def _loadModule(self, importName, modRanaName):
    """load a single module by name from path"""
    startM = time.clock()
    try:
      a = __import__(importName)
      initInfo = self.initInfo
      name = modRanaName
      initInfo['name'] = name
      module = a.getModule(self.m, self.d, initInfo)
      self.m[name] = module
      print " * %s: %s (%1.2f ms)" % (name, self.m[name].__doc__, (1000 * (time.clock() - startM)))
      return module
    except Exception, e:
      print "modRana: module: %s/%s failed to load" % (importName, modRanaName)
      traceback.print_exc(file=sys.stdout) # find what went wrong
      return None

  def _modulesLoadedPreFirstTime(self):
    """this is run after all the modules have been loaded,
    but before their first time is called"""
    self._updateCenteringShiftCB()

    """to nly update values needed for map drawing when something changes
       * window is resized
       * user switches something rleated in options
       * etc.
       we use the key watching mechanism
       once a related key is changed, we update all the values
       """
    # watch both centering shift related variables
    self.watch('posShiftAmount', self._updateCenteringShiftCB)
    self.watch('posShiftDirection', self._updateCenteringShiftCB)
    # also watch the viewport
    self.watch('viewport', self._updateCenteringShiftCB)
    # and map scaling
    self.watch('mapScale', self._updateCenteringShiftCB)
    # and mode change
    self.watch('mode', self._modeChangedCB)
    # cache key modifiers
    self.keyModifiers = self.d.get('keyModifiers', {})

  def _modulesLoadedPostFirstTime(self):
    """this is run after all the modules have been loaded,
    after before their first time is called"""
    
    # check if redrawing time should be printed to terminal
    if 'showRedrawTime' in self.d and self.d['showRedrawTime'] == True:
      self.showRedrawTime = True

  def beforeDie(self):
    print "Shutting-down modules"
    for m in self.m.values():
      m.shutdown()
    time.sleep(2) # leave some times for threads to shut down
    print "Shuttdown complete"
    
  ## OPTIONS SETTING AND WATCHING ##

  def get(self, name, default=None, mode=None):
    """Get an item of data"""

    # check if the value depends on current mode
    if name in self.keyModifiers.keys():
      # get the current mode
      if mode == None:
        mode = self.d.get('mode', 'car')
      if mode in self.keyModifiers[name]['modes'].keys():
        # get the dictionary with per mode values
        multiDict = self.d.get('%s#multi' % name , {})
        # retrun the value for current mode
        return multiDict.get(mode,default)
      else:
        return(self.d.get(name, default))

    else: # just return the normal value
      return(self.d.get(name, default))

  def set(self, name, value, save=False, mode=None):
    """Set an item of data,
    if there is a watch set for this key,
    notify the watcher that its value has changed"""

    oldValue = self.get(name, value)

    if name in self.keyModifiers.keys():
      # get the current mode
      if mode == None:
        mode = self.d.get('mode', 'car')
      # check if there is a modifier for the current mode
      if mode in self.keyModifiers[name]['modes'].keys():
        # save it to the name + #multi key under the mode key
        try:
          self.d['%s#multi' % name][mode] = value
        except KeyError: # key not yet created
          self.d['%s#multi' % name] = {mode : value}
      else: # just save to the key as usuall
        self.d[name] = value
    else: # just save to the key as usuall
      self.d[name] = value

    self._notifyWatcher(name, oldValue)
    """options are normally saved on shutdown,
    but for some data we want to make sure they are stored and not
    los for example becuase of power outage/empty battery, etc."""
    if save:
      options = self.m.get('options')
      if options:
        options.save()

  def optionsKeyExists(self, key):
    """Report if a given key exists"""
    return key in self.d.keys()

  def purgeKey(self, key):
    """remove a key from the presistant dictionary,
    including possible key modifiers and alternate values"""
    if key in self.d:
      oldValue = self.get(key, None)
      del self.d[key]
      # purge any key modifiers
      if key in self.keyModifiers.keys():
        del self.keyModifiers[key]
        """also remove the possibly present
        alternative states for different modes"""
        multiKey = "%s#multi" % key
        if multiKey in self.d:
          del self.d[multiKey]
      self._notifyWatcher(key, oldValue)
      return True
    else:
      print("modrana: can't purge a not present key: %s" % key)

  def watch(self, key, callback, *args):
    """add a callback on an options key
    callbakc will get:
    key, newValue, oldValue, *args

    NOTE: watch ids should be >0, so that they evaluate as True
    """
    nrId = self.maxWatchId + 1
    id = "%d_%s" % (nrId,key)
    self.maxWatchId = nrId # TODO: recycle ids ? (alla PID)
    if key not in self.watches:
      self.watches[key] = [] # create the initial list
    self.watches[key].append((id,callback,args))
    return id

  def removeWatch(self, id):
    """remove watch specified by the given watch id"""
    (nrId, key) = id.split('_')

    if key in self.watches:
      remove = lambda x:x[0]==id
      self.watches[key][:] = [x for x in self.watches[key] if not remove(x)]
    else:
      print("modRana: can't remove watch - key does not exist, watchId:", id)

  def _notifyWatcher(self, key, oldValue):
    """run callbacks registered on an options key
    HOW IT WORKS
    * the watcher is notified before the key is written to the persistant
    dictionary, so that it can react before the change is visible
    * the watcher gets the key and both the new and old values
    """
    callbacks = self.watches.get(key, None)
    if callbacks:
      for item in callbacks:
        (id,callback,args) = item
        # rather supply the old value than None
        newValue = self.get(key, oldValue)
        if callback:
          if callback(key,oldValue, newValue, *args) == False:
            # remove watches that return False
            self.removeWatch(id)
        else:
          print "invalid watcher callback :", callback

  def addKeyModifier(self, key, modifier=None, mode=None, copyInitialValue=True):
    """add a key modifier
    NOTE: currently only used to make value of some keys
    dependent on the current mode"""
    options = self.m.get('options', None)
    # remeber the old value, if not se use default from options
    # if available
    if options:
      defaultValue = options.getKeyDefault(key, None)
    else:
      defaultValue = None
    oldValue = self.get(key,defaultValue)
    if mode == None:
      mode = self.d.get('mode', 'car')
    if key not in self.keyModifiers.keys(): # initialize
      self.keyModifiers[key] = {'modes':{mode:modifier}}
    else:
      self.keyModifiers[key]['modes'][mode] = modifier

    # make sure the multi mode dictionary exists
    multiKey = '%s#multi' % key
    multiDict = self.d.get(multiKey , {})
    self.d[multiKey] = multiDict

    """if the modifier is set for the first time,
    do we copy the value from the normal key or not ?"""
    if copyInitialValue:
      # check if the key is unset for this mode
      if mode not in multiDict:
        # set for first time, copy value        
        self.set(key, self.d.get(key, defaultValue), mode=mode)

    # notify watchers
    self._notifyWatcher(key, oldValue)

  def removeKeyModifier(self, key, mode=None):
    """remove key modifier
    NOTE: currently this just makes the key independent
    on the current mode"""


    # if no mode is provided, use the current one
    if mode == None:
        mode = self.d.get('mode', 'car')
    if key in self.keyModifiers.keys():
      
      # just remove the key modifier preserving the alternative values
      if mode in self.keyModifiers[key]['modes'].keys():
        # get the previous value
        options = self.m.get('options', None)
        # remeber the old value, if not se use default from options
        # if available
        if options:
          defaultValue = options.getKeyDefault(key, None)
        else:
          defaultValue = None
        oldValue = self.get(key,defaultValue)
        del self.keyModifiers[key]['modes'][mode]
        # was this the last key ?
        if len(self.keyModifiers[key]['modes']) == 0:
          # no modes registered - unregister from modifiers
          # TODO: handle non-mode modifiers in the future
          del self.keyModifiers[key]
        # notify watchers
        self._notifyWatcher(key, oldValue)
        # done
        return True
      else:
        print("modrana: can't remove modifier that is not present")
        print("key: %s, mode: %s" % (key, mode))
        return False
    else:
      print("modRana: key %s has no modifier and thus cannot be removed" % key)
      return False

  def hasKeyModifier(self, key):
    """return if a key has a key modifier"""
    return key in self.keyModifiers.keys()

  def hasKeyModifierInMode(self, key, mode=None):
    """return if a key has a key modifier"""
    if mode == None:
      mode = self.d.get('mode', 'car')
    if key in self.keyModifiers.keys():
      return mode in self.keyModifiers[key]['modes'].keys()
    else:
      return False

  def getModes(self):
    modes = {
      'cycle':'Cycle',
      'walk':'Foot',
      'car':'Car',
      'train':'Train',
      'bus':'Bus',
    }
    return modes

  def getModeLabel(self, modeName):
    "get a label for a given mode"
    try:
      return self.getModes()[modeName]
    except KeyError:
      print('modrana: mode %s does not exist and thus has no label' % modeName)
      return None

  def update(self):
    for m in self.m.values():
      m.update()

  def _checkForRedrawCB(self, key, oldValue, newValue):
    """react to redraw requests"""
    if newValue == True:
      self.forceRedraw()
      
  def forceRedraw(self):
    """Make the window trigger a draw event.
    TODO: consider replacing this if porting pyroute to another platform"""
    self.d['needRedraw'] = False
    """ alter directly, no need to notificate
    about returning the key to default state"""

    # record timestamp
    self.lastFullRedrawRequest = time.time()

    if self.redraw:
      try:
        self.window.invalidate_rect((0,0,self.rect.width,self.rect.height),False)
      except Exception, e:
        print "error in screen invalidating function"
        print "exception: %s" % e

  def mousedown(self,x,y):
    """this signalizes start of a drag or a just a click"""
    pass
    
  def click(self, x, y, msDuration):
    """this fires after a drag is finished or mouse button released"""
    m = self.m.get("clickHandler",None)
    if m:
      m.handleClick(x,y,msDuration)
      self.update()
      
  def released(self,event):
    """mouse button has been released or
    the tapping object has been lifted up from the touchscreen"""

    #always unlock drag on release
    self.unlockDrag()

    if self.altDragEnd:
      self.altDragEnd(event)
      
  def handleDrag(self,x,y,dx,dy,startX,startY,msDuration):
    # check if centering is on
    if self.get("centred",True):
      fullDx = x - startX
      fullDy = y - startY
      distSq = fullDx * fullDx + fullDy * fullDy
      """ check if the drag is strong enought to disable centering
      -> like this, centering is not dsabled by pressing buttons"""
      if self.centeringDisableTreshold:
        if distSq > self.centeringDisableTreshold:
          self.set("centred", False) # turn off centering after dragging the map (like in TangoGPS)
          self.d["needRedraw"] = True
    else:
      if self.altMapDragEnabled:
        # start simple map drag if its not already in progress
        menuName = self.d.get('menu', None)
        if menuName == None and not self.altMapDragInProgress:
          self.altDragStart(x-startX,y-startY,dx,dy)
        elif self.altMapDragInProgress:
          self.altDragHandler(x-startX,y-startY,dx,dy)
      else:
        m = self.m.get("clickHandler",None)
        if m:
          m.handleDrag(startX,startY,dx,dy,x,y,msDuration)

  def handleLongPress(self, pressStartEpoch, msCurrentDuration, startX, startY, x, y):
    """handle long press"""
    m = self.m.get("clickHandler",None)
    if m:
      m.handleLongPress(pressStartEpoch, msCurrentDuration, startX, startY, x, y)
        
  def lockDrag(self):
    """start ignoring drag events"""
    self.dragLocked = True
    
  def unlockDrag(self):
    """stop ignoring drag events"""
    self.dragLocked = False

  def setCDDragTreshold(self, treshold):
    """set the treshold which needs to be reached to disable centering while dragging
    basically, larger treshold = longer drag is needed to disable centering
    default value = 2048
    """
    self.centeringDisableTreshold = treshold
    
  def _updateCenteringShiftCB(self, key=None, oldValue=None, newValue=None):
    """update shifted centering amount

    this method is called if posShiftAmount or posShiftDirection
    are set and also once at startup"""
    # get the needed values
    # NOTE: some of them might have been updated just now
    if key == 'viewport':
      (sx,sy,sw,sh) = newValue
    else:
      (sx,sy,sw,sh) = self.get('viewport')

    if key == 'posShiftAmount':
      shiftAmount = newValue
    else:
      shiftAmount = self.d.get('posShiftAmount', 0.75)

    if key == 'posShiftDirection':
      shiftDirection = newValue
    else:
      shiftDirection = self.d.get('posShiftDirection', "down")

    if key == 'mapScale':
      scale = int(newValue)
    else:
      scale = int(self.get('mapScale', 1))

    x=0
    y=0
    floatShiftAmount = float(shiftAmount)
    """this value might show up as string, so we convert it to float, just to be sure"""

    if shiftDirection:
      if shiftDirection == "down":
        y =  sh * 0.5 * floatShiftAmount
      elif shiftDirection == "up":
        y =  - sh * 0.5 * floatShiftAmount
      elif shiftDirection == "left":
        x =  - sw * 0.5 * floatShiftAmount
      elif shiftDirection == "right":
        x =  + sw * 0.5 * floatShiftAmount
      """ we dont need to do anything if direction is set to don't shift (False)
      - 0,0 will be used """
    self.centerShift = (x,y)
    
    # update the viewport expansion variable    
    tileSide = 256
    mapTiles = self.m.get('mapTiles')
    if mapTiles: # check the mapTiles for tile side length in pixels, if available
      tileSide = mapTiles.tileSide
    tileSide = tileSide * scale # apply any possible scaling
    (centerX,centerY) = ((sw/2.0),(sh/2.0))
    ulCenterDistance = simplePythagoreanDistance(0, 0, centerX, centerY)
    centerLLdistance = simplePythagoreanDistance(centerX, centerY, sw, sh)
    diagonal = max(ulCenterDistance, centerLLdistance)
    add = int(math.ceil(float(diagonal)/tileSide))
    self.expandViewportTiles = add

  def _modeChangedCB(self, key=None, oldMode=None, newMode=None):
    """handle mode change in regards to key modifiers and option key watchers"""
    print "mode changed"

    print oldMode, newMode
    # get keys that have both a key modifier and a watcher
    keys = filter(lambda x: x in self.keyModifiers.keys(), self.watches.keys())

  def draw(self, cr, event):
    """ re/Draw the modrana GUI """
    start = time.clock()
    # run the currently used draw method
    self.currentDrawMethod(cr,event)
    # enable redraw speed debugging
    if self.showRedrawTime:
      print "Redraw took %1.2f ms" % (1000 * (time.clock() - start))
    self.lastFullRedraw = time.time()

  def getLastFullRedraw(self):
    return self.lastFullRedraw

  def getLastFullRedrawRequest(self):
    return self.lastFullRedrawRequest

  def fullDrawMethod(self, cr, event):
    """ this is the default drawing method
    draws all layers and should be used together with full screen redraw """

    for m in self.m.values():
      m.beforeDraw()

    menuName = self.d.get('menu', None)
    if menuName: # draw the menu
      menus = self.m.get('menu', None)
      if menus:
        menus.mainDrawMenu(cr, menuName)
      else:
        print("modrana: error, menu module missing")
    else: # draw the map
      cr.set_source_rgb(0.2,0.2,0.2) # map background
      cr.rectangle(0,0,self.rect.width,self.rect.height)
      cr.fill()
      if (self.d.get("centred", False) and self.d.get("rotateMap", False)):
        proj = self.m['projection']
        (lat, lon) = (proj.lat,proj.lon)
        (x1,y1) = proj.ll2xy(lat, lon)

        (x,y) = self.centerShift
        cr.translate(x,y)
        cr.save()
        # get the speed and angle
        speed = self.d.get('speed', 0)
        angle = self.d.get('bearing', 0)
        
        """
        only if current direction angle and speed are known,
        submit a new angle
        like this, the map does not revert back to default orientation
        on short GPS errors
        """
        if angle and speed:
          if speed > self.notMovingSpeed: # do we look like we are moving ?
            self.mapRotationAngle = angle
        cr.translate(x1,y1) # translate to the rotation center
        cr.rotate(radians(360 - self.mapRotationAngle)) # do the rotation
        cr.translate(-x1,-y1) # translate back

        # Draw the base map, the map overlays, and the screen overlays
        try:
          for m in self.m.values():
            m.drawMap(cr)
          for m in self.m.values():
            m.drawMapOverlay(cr)
        except Exception, e:
          print "modRana main loop: an exception occured:\n"
          traceback.print_exc(file=sys.stdout) # find what went wrong
        cr.restore()
        cr.translate(-x,-y)
        for m in self.m.values():
          m.drawScreenOverlay(cr)
      else: # centering is disabled, just draw the map
        try:
          for m in self.m.values():
            m.drawMap(cr)
          for m in self.m.values():
            m.drawMapOverlay(cr)
        except Exception, e:
          print "modRana main loop: an exception occured:\n"
          traceback.print_exc(file=sys.stdout) # find what went wrong
        for m in self.m.values():
          m.drawScreenOverlay(cr)

    # do the master overlay over everything
    self.drawMasterOverlay(cr)

#    if 'showRedrawTime' in self.d and self.d['showRedrawTime'] == True:

#  def draw2(self, cr1):
#    start = time.clock()
#
#
##      cr.paint()
##      print cr.get_target()
##      print cr.get_target().get_width()
##      print cr.get_target().get_height()
#
#    mapAndMapOverlayBuffer = self.getMapAndMapOverlayBuffer()
#    if mapAndMapOverlayBuffer:
#      cr1.set_source_surface(mapAndMapOverlayBuffer, float(self.centerX), float(self.centerY))
#      cr1.paint()
#    start1 = time.clock()
#    for m in self.m.values():
#      m.drawScreenOverlay(cr1)
#
#    # enable redraw speed debugging
#    if 'showRedrawTime' in self.d and self.d['showRedrawTime'] == True:
#      print "Redraw1 took %1.2f ms" % (1000 * (time.clock() - start))
#      print "Redraw2 took %1.2f ms" % (1000 * (time.clock() - start1))
#
#  def getMapAndMapOverlayBuffer(self):
#    if self.mapBuffer == None:
#      self.mapBuffer = self.drawMapAndMapOverlay()
#    return self.mapBuffer
#
#  def drawMapAndMapOverlay(self):
#    mapAndMapOverlayBuffer = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.rect.width, self.rect.height)
#    ct = cairo.Context(mapAndMapOverlayBuffer)
#    cr = gtk.gdk.CairoContext(ct)
#
#    for m in self.m.values():
#      m.beforeDraw()
#
#    menuName = self.d.get('menu', None)
#    if(menuName != None):
#      for m in self.m.values():
#        m.drawMenu(cr1, menuName)
#    else:
#      # map background
#      cr.set_source_rgb(0.2,0.2,0.2)
#      cr.rectangle(0,0,self.rect.width,self.rect.height)
#      cr.fill()
#
#      cr.save()
#      if (self.d.get("centred", False)):
#        if self.d.get("rotateMap", False):
#
#          # get the speed and angle
#          speed = self.d.get('speed', 0)
#          angle = self.d.get('bearing', 0)
#
#          proj = self.m['projection']
#          (lat, lon) = (proj.lat,proj.lon)
#          (x1,y1) = proj.ll2xy(lat, lon)
#
#          """
#          only if current direction angle and speed are known,
#          submit a new angle
#          like this, the map does not revert back to default orientation
#          on short GPS errors
#          """
#          if angle and speed:
#            if speed > self.notMovingSpeed: # do we look like we are moving ?
#              angle = 360 - angle
#              self.mapRotationAngle = radians(angle)
#          cr.translate(x1,y1) # translate to the rotation center
#          cr.rotate(self.mapRotationAngle) # do the rotation
#          cr.translate(-x1,-y1) # translate back
#
#      # Draw the base map, the map overlays, and the screen overlays
#      for m in self.m.values():
#        m.drawMap(cr)
#      cr.restore()
#      for m in self.m.values():
#        m.drawMapOverlay(cr)
#
#      return mapAndMapOverlayBuffer

## clean map + overlay generation reference
#    staticMap = cairo.ImageSurface(cairo.FORMAT_ARGB32,w,h)
#    cr1 = cairo.Context(staticMap)
#    for m in self.m.values():
#      m.beforeDraw()
#    try:
#      for m in self.m.values():
#        m.drawMap(cr1)
#      for m in self.m.values():
#        m.drawMapOverlay(cr1)
#    except Exception, e:
#      print "modRana simple map: an exception occured:\n"
#      traceback.print_exc(file=sys.stdout) # find what went wrong
#      self.stopSimpleMapDrag()
#      return
#    self.simpleStaticMap = staticMap

## damage area computation reference
#    damage = gtk.gdk.region_rectangle((x,y,w,h))
#    keep = gtk.gdk.region_rectangle((dx,dy,w,h))
#    damage.subtract(keep)


## FASTER MAP DRAGGING ##

  def setDefaultDrag(self):
    """try to revert to the default dragging method"""
    if self.altDragRevert:
      self.altDragRevert()
    else: # just to be sure
      self.defaulMethodBindings()
      self.altMapDragEnabled = False

  def setCurrentRedrawMethod(self, method=None):
    if method == None:
      self.currentDrawMethod = self.fullDrawMethod
    else:
      self.currentDrawMethod = method


  def defaulMethodBindings(self):
    """revert drag method bindings to default state"""
    self.altDragStart = None # alternative map drag enabler
    self.altDragHandler = None # alternative map drag handler
    self.altDragEnd = None
    self.altDragRevert = None # reverts the current alt map drag to default
    self.currentDrawMethod = self.fullDrawMethod

  def initGCandBackingPixmap(self,w,h):
    if self.window:
      self.gc = self.window.new_gc(background=(gtk.gdk.color_parse('white')))
      self.gc.set_clip_rectangle(gtk.gdk.Rectangle(0, 0, w, h))
      self.backingPixmap = gtk.gdk.Pixmap(self.window, int(w), int(h), depth=-1)

# static map image dragging #
  def staticMapDragEnable(self):
    """enable static map dragging method"""
    # first do a cleanup
    self.setDefaultDrag()

    self.d['needRedraw'] = True

    # then bind all relevant methods to variables
    self.altDragStart = self.staticMapDragStart
    self.altDragEnd = self.staticMapDragEnd
    self.altDragHandler = self.staticMapDrag
    self.altDragRevert = self.staticMapRevert
    # enable alternative map drag
    self.altMapDragEnabled = True

  def staticMapDragStart(self,shiftX,shiftY,dx,dy):
    """start the simple map dragging procedure"""
    self.altMapDragInProgress = True
    self.setCurrentRedrawMethod(self.staticMapPixmapDrag)
    # get the map and overlay
    (sx,sy,w,h) = self.d.get('viewport')

    # store current screen content in backing pixmap
    self.backingPixmap.draw_drawable(self.gc, self.window, 0, 0, 0,0,-1,-1)
    # initiate first drag
    self.staticMapDrag(shiftX, shiftY,dx,dy)
    self.set('needRedraw',True)

  def staticMapDragEnd(self, event):
    """revert the changes neede for the drag"""
    proj = self.m['projection']
    (shiftX,shiftY,dx,dy) = self.shift
    proj.nudge(shiftX, shiftY)
    self.shift = (0,0,0,0)

    # disable alternative map drag
    self.altMapDragInProgress = False

    # return the defaultRedrawMethod
    self.setCurrentRedrawMethod()

    # redraw the whole screen
    self.set('needRedraw',True)

  def staticMapDrag(self,shiftX,shiftY,dx,dy):
    """drag the map"""
    self.shift = (shiftX,shiftY,dx,dy)
    (x,y,w,h) = (self.rect.x, self.rect.y, self.rect.width, self.rect.height)
    self.set('needRedraw',True)

  def staticMapPixmapDrag(self, cr, event):
    (x,y,w,h) = (self.rect.x, self.rect.y, self.rect.width, self.rect.height)
    (shiftX,shiftY,dx,dy) = self.shift
    self.window.draw_drawable(self.gc, self.backingPixmap, 0,0,int(shiftX),int(shiftY),-1,-1)

  def staticMapRevert(self):
    self.defaulMethodBindings()
    self.altMapDragEnabled = False

  def do_realize(self):
    self.set_flags(self.flags() | gtk.REALIZED)
    self.window = gdk.Window( \
      self.get_parent_window(),
      width = self.allocation.width,
      height = self.allocation.height,
      window_type = gdk.WINDOW_CHILD,
      wclass = gdk.INPUT_OUTPUT,
      event_mask = self.get_events() | gdk.EXPOSURE_MASK)
    self.window.set_user_data(self)
    self.style.attach(self.window)
    self.style.set_background(self.window, gtk.STATE_NORMAL)
    self.window.move_resize(*self.allocation)

    # initialize resources needed for fast map dragging support
    self.initGCandBackingPixmap(self.allocation.width, self.allocation.height)

    # alow the modules to manipulate the window TODO: do this more elegantly (using signals ?)
    for name in self.m:
      self.m[name].mainWindow = self.window
      self.m[name].topWindow = self.topWindow

  def do_size_request(self, allocation):
    pass
  def do_size_allocate(self, allocation):
    self.allocation = allocation
    self.rect = self.allocation
    self._updateViewport()
    
    if self.flags() & gtk.REALIZED:
      self.window.move_resize(*allocation)
    newW = allocation[2]
    newH = allocation[3]

    print "size allocate", allocation
    # resize the backing pixmap
    self.initGCandBackingPixmap(self.allocation.width, self.allocation.height)

    # notify all modules
    for m in self.m.values(): # enable resize handling by modules
        m.handleResize(newW, newH)
    self.forceRedraw() # redraw window contents after resize

  def _updateViewport(self):
    """update the current viewport in the global perzistent dictionary"""
    self.set('viewport', (self.rect.x, self.rect.y, self.rect.width, self.rect.height))

  def _expose_cairo(self, event, cr):    
    # set clipping in cairo
    cr.rectangle(
      self.rect.x,
      self.rect.y,
      self.rect.width,
      self.rect.height)
    cr.clip()
    
    self.draw(cr,event)
  def do_expose_event(self, event):
    self.chain(event)
    cr = self.window.cairo_create()
    return self._expose_cairo(event, cr)

  # * MASTER OVERLAY *
  def drawMasterOverlay(self, cr):
    if self.notificationModule:
      self.notificationModule.drawMasterOverlay(cr)

  # * PROFILE PATH *
  def getProfilePath(self):
    """return the profile folder (create it if it does not exist)
    NOTE: this function is provided here in the main class as some
    ordinary modRana modules need to know the profile folder path before the
    option module that normally handles it is fully initialized
    (for example the config module might need to copy default
    configuration files to the profile folder in its init)
    """
    # get the path
    modRanaProfileFolderName = '.modrana'
    userHomePath = os.getenv("HOME")
    profileFolderPath = os.path.join(userHomePath, modRanaProfileFolderName)
    # make sure it exists
    createFolderPath(profileFolderPath)
    # return it
    return profileFolderPath

  # * MAP LAYERS *
  """map lyer information is important and needed by many modules during their initialization,
  so it is handled here"""
  def getMapLayers(self):
    return self.mapLayers

  def loadMapLayerInfo(self):
    mapLayers = {}
    configVariables = {
        'label':'label',
        'url':'tiles',
        'max_zoom':'maxZoom',
        'min_zoom':'minZoom',
        'type':'type',
        'folder_prefix':'folderPrefix',
        'coordinates':'coordinates',
                      }
    mapConfigPath = os.path.join(self.getProfilePath(),'map_config.conf')
    # check if the configuration files are there already
    if not os.path.exists(mapConfigPath):
      # nthing in prfile folder -> try to use the default configs
      print("modRana: no config in profile folder, using default map layer configuration file")
      mapConfigPath = os.path.join("data/default_configuration_files",'map_config.conf')
      if not os.path.exists(mapConfigPath):
        # no map layer config available
        print("modRana: map layer configuration file not available")
        return

    def allNeededIn(needed, dict):
      for key in needed:
        if key in dict:
          continue
        else:
          return False
      return True  

    try:
      config = ConfigObj(mapConfigPath)
      for layer in config:
        if allNeededIn(configVariables.keys(), config[layer].keys()): # check if all neded keys are available
          tempDict = {}
          for var in configVariables:
            tempDict[configVariables[var]] = config[layer][var]
          tempDict['minZoom'] = int(tempDict['minZoom']) # convert strings to integers
          tempDict['maxZoom'] = int(tempDict['maxZoom'])
        else:
          print "mapTiles: layer is badly defined/formated: %s" % layer


        mapLayers[layer] = tempDict

    except Exception, e:
      print "mapTiles: loading map_config.conf failed: %s" % e

    self.mapLayers = mapLayers

class GuiBase:
  """Wrapper class for a GUI interface"""
  def __init__(self, device):
    # start timing the launch
    self.timing = []
    self.addCustomTime("modRana start",startTimestamp)
    self.addCustomTime("imports done", importsDoneTimestamp)
    self.addTime("GUI creation")

    # Create the window

    #TODO: do this more cleanly:

    """when on N900, use a hildon StackableWindow, which
    enables app menu and tohe features on Maemo 5"""
    if device == 'n900':
      try:
        import hildon
        win = hildon.StackableWindow()
      except Exception, e:
        print "creating hildon stackable window failed"
        print e
        win = gtk.Window()
    else:
      win = gtk.Window()

    win.set_title('modRana')
    win.connect('delete-event', gtk.main_quit)
    self.addTime("window created")

    # press length timing
    self.lastPressEpoch = 0
    self.pressInProgress = False
    self.pressLengthTimer = None

    if(device == 'eee'): # test for use with asus eee
      win.resize(800,600)
      win.move(gtk.gdk.screen_width() - 900, 50)
    if(device == 'netbook'): # test for use with asus eee
      win.resize(800,600)
      win.move(gtk.gdk.screen_width() - 900, 50)
    elif(device == 'n900'): # test for use with nokie N900
      win.resize(800,480)
    elif(device == 'q7'): # test for use with Smart Q7
      win.resize(800,480)
      win.move(gtk.gdk.screen_width() - 900, 50)
    elif(device == 'n95'): # test for use with nokia 95
      win.resize(480,640)
      win.move(gtk.gdk.screen_width() - 500, 50)
    elif(device == 'square'): # for testing equal side displays
      win.resize(480,480)
      win.move(gtk.gdk.screen_width() - 500, 50)
    elif(device == 'ipaq'): #  for some 240*320 displays (like most old Ipaqs/PocketPCs)
      win.resize(240,320)
      win.move(gtk.gdk.screen_width() - 500, 50)
    else: # test for use with neo freerunner
      win.resize(480,640)
      win.move(gtk.gdk.screen_width() - 500, 50)
    
    # Events
    event_box = gtk.EventBox()

    event_box.connect("button_press_event", self.pressed)
    event_box.connect("button_release_event", self.released)
    event_box.connect("motion_notify_event", self.moved)
    win.add(event_box)

    # Create the map
    self.mapWidget = MapWidget(device)
    self.mapWidget.topWindow=win # make the main widown accessible from modules
    event_box.add(self.mapWidget)
    self.addTime("map widget created")

    # Finalise the window
    win.show_all()
    self.addTime("window finalized")

    # load map layer info
    self.mapWidget.loadMapLayerInfo()

    # start loading modules
    self.mapWidget.loadModules() # name of the folder with modules

    # add last timing checkpoint
    self.addTime("all modules loaded")

    # report startup time
    self.reportStartupTime()

    # start gtk main loop
    gtk.main()
    self.mapWidget.beforeDie()

## STARTUP TIMING ##

  def addTime(self, message):
    timestamp = time.time()
    self.timing.append((message,timestamp))
    return (timestamp)

  def addCustomTime(self, message, timestamp):
    self.timing.append((message,timestamp))
    return (timestamp)

  def reportStartupTime(self):
    if self.timing:
      print "** modRana startup timing **"
      
      # print device identificator and name
      if self.mapWidget.dmod:
        deviceName = self.mapWidget.dmod.getDeviceName()
        print "# device: %s (%s)" % (deviceName, device)

      tl = self.timing
      startupTime = tl[0][1] * 1000
      lastTime = startupTime
      totalTime = (tl[-1][1] * 1000) - startupTime
      for i in tl:
        (message, t) = i
        t = 1000 * t # convert to ms
        timeSpent = t - lastTime
        timeSinceStart = t - startupTime
        print "* %s (%1.0f ms), %1.0f/%1.0f ms" % (message, timeSpent, timeSinceStart, totalTime)
        lastTime = t
      print "** whole startup: %1.0f ms **" % totalTime
    else:
      print "* timing list empty *"



  def pressed(self, w, event):
    self.lastPressEpoch=event.time
    self.pressInProgress = True

    self.dragstartx = event.x
    self.dragstarty = event.y
    #print dir(event)
    #print "Pressed button %d at %1.0f, %1.0f" % (event.button, event.x, event.y)
    
    self.dragx = event.x
    self.dragy = event.y
    self.mapWidget.mousedown(event.x,event.y)

    if not self.pressLengthTimer:
      self.pressLengthTimer = gobject.timeout_add(50, self.checkStillPressed, event.time, time.time(), event.x,event.y)
    
  def moved(self, w, event):
    """Drag-handler"""

    self.mapWidget.handleDrag( \
      event.x,
      event.y,
      event.x - self.dragx, 
      event.y - self.dragy,
      self.dragstartx,
      self.dragstarty,
      event.time - self.lastPressEpoch)

    self.dragx = event.x
    self.dragy = event.y

  def released(self, w, event):
    self.pressInProgress = False
    self.pressLengthTimer = None
    msDuration = event.time - self.lastPressEpoch

    self.mapWidget.released(event)
    dx = event.x - self.dragstartx
    dy = event.y - self.dragstarty
    distSq = dx * dx + dy * dy
    # Adjust this to the length^2 of a gerfingerpoken on your touchscreen (1024 is for Freerunner, since it's very high resolution)
    if distSq < 1024:
      self.mapWidget.click(event.x, event.y,msDuration)

  def checkStillPressed(self, pressStartEpoch, pressStartTime, startX, startY):
    """check if a press is still in progress and report:
    pressStart epoch - to differentiate presses
    duration
    start coordinates
    currentCoordinates
    if no press is in progress or another press already started, shut down the timer
    """

    """just to be sure, time out after 60 seconds
    - provided the released signal is always called, this timeout might not be necessary,
    but better be safe, than eat the whole battery if the timer is not terminated"""
    dt = (time.time() - pressStartTime)*1000
    if dt > 60000:
      print "long press timeout reached"
      return False

    if pressStartEpoch == self.lastPressEpoch and self.pressInProgress:
      self.mapWidget.handleLongPress(pressStartEpoch, dt, startX, startY, self.dragx, self.dragy)     
      return True
    else: # the press ended or a new press is in progress -> stop the timer
      return False



if __name__ == "__main__":
  """
  suported devices (for now):
  'neo' (480*640)
  'n95' (480*640)
  'eee' (800*600)
  'netbook' (800*600)
  'q7'  (800*480)
  'n900' (800*480) -> for now can also be used for the Q7 or Q5 (same resolution)
  'square' (480*480) -> this is for testing screens with equal sides
  'ipaq' (240*320) -> old Ipaqs (and and other Pocket PCs) had this resolution
  """

  print " == modRana Starting == "

  try:
    import sys
    device = sys.argv[1].lower()
    print " device string (first parameter): %s " % sys.argv[1]
  except:
    device = 'neo'
    print " no device string in first parameter, using: %s" % device

  program = GuiBase(device)