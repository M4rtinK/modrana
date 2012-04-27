#!/usr/bin/python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# modRana main GUI.  Displays maps & much more, for use on a mobile device.
#
# Controls:
# Start by clicking on the main menu icon.
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

# module folder name
import subprocess

modulesFolder = 'modules'
import sys
# add module folder to path
sys.path.append(modulesFolder)
import time
startTimestamp = time.time()
import math
# set current directory to the directory
# of this file
# like this, modRana can be run from an absolute path
# eq.: ./opt/modrana/modrana.py -u QML -d n9
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import marshal
import traceback
from math import radians
# import core modules/classes
from core import startup
from core import paths
from core import configs
from core import gs

# record that imports-done timestamp
importsDoneTimestamp = time.time()

def createFolderPath(newPath):
  """
  Create a path for a directory and all needed parent forlders
  -> parent directories will be created
  -> if directory already exists, then do nothing
  -> if there is another filesystem object (like a file) with the same name, raise an exception
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

def simplePythagoreanDistance(x1, y1, x2, y2):
  """convenience PyThagorean distance :)"""
  dx = x2 - x1
  dy = y2 - y1
  return math.sqrt(dx**2 + dy**2)

class ModRana:
  """
  This is THE main modRana class.
  """
  def __init__(self):
    self.timing = []
    self.addCustomTime("modRana start",startTimestamp)
    self.addCustomTime("imports done", importsDoneTimestamp)

    # constants & variable initialization
    self.dmod = None # device specific module
    self.gui = None

    self.d = {} # persistent dictionary of data
    self.m = {} # dictionary of loaded modules
    self.watches = {} # List of data change watches
    self.maxWatchId = 0

    self.mapRotationAngle = 0 # in radians
    self.notMovingSpeed = 1 # in m/s
    
    # map center shifting variables
    self.centerShift = (0,0)

    # map layers
    self.mapLayers = {}

    # per mode options
    # NOTE: this variable is automatically saved by the
    # options module
    self.keyModifiers = {}

    # start timing modRana launch
    self.addTime("GUI creation")

    # add the startup handling core module
    start = startup.Startup(self)
    self.args = start.getArgs()

    # add the paths handling core module
    self.paths = paths.Paths(self)
    # add the configs handling core module
    self.configs = configs.Configs(self)

    # load persistent options
    self.optLoadingOK= self._loadOptions()

    # check if upgrade took place

    if self.optLoadingOK:
      savedVersionString = self.get('modRanaVersionString', "")
      versionStringFromFile = self.paths.getVersionString()
      if savedVersionString != versionStringFromFile:
        print "modRana: possible upgrade detected"
        self._postUpgradeCheck()

    # save current version string
    self.set('modRanaVersionString', self.paths.getVersionString())

    # load all configuration files
    self.configs.loadAll()

    # start loading modules
    self.loadModules()
    # startup done, print some statistics
    self._startupDone()

  def _postUpgradeCheck(self):
    """
    perform post upgrade checks
    """
    self.configs.upgradeConfigFiles()

  ##  MODULE HANDLING ##

  def loadModules(self):
    """Load all modules from the specified directory"""

    # get the device module string
    # (a unique device module string identificator)
    # make sure there is some argument provided
    if self.args:
      device = self.args.d[0]
    else:
      # use the Neo device module as fallback
      device = "neo"

    device = device.lower() # convert to lowercase
    print "importing modules:"
    start = time.clock()
    self.initInfo={
              'modrana': self,
              'device': device, # TODO: do this directly
              'name': ""
             }

    # make shortcut for the loadModule function
    loadModule = self._loadModule

    # make sure there are some arguments
    if self.args.u:
      GUIString = self.args.u[0]
    else:
      # GTK GUI fallback
      GUIString = "GTK"
    gs.GUIString = GUIString

    ## load the device specific module

    # NOTE: other modules need the device and GUI modules
    # during init
    deviceModulesPath = os.path.join(modulesFolder, "device_modules")
    sys.path.append(deviceModulesPath)
    dmod = loadModule("device_%s" % device, "device")
    if dmod == None:
      print("modRana: no device module name provided"
            "loading the Neo device module as failsafe")
      device = "neo"
      dmod = loadModule("device_%s" % device, "device")
    self.dmod = dmod

    ## load the GUI module

    # add the GUI module folder to path
    GUIModulesPath = os.path.join(modulesFolder, "gui_modules")
    sys.path.append(GUIModulesPath)
    if GUIString == "GTK":
      gui = loadModule("gui_gtk", "gui")
    elif GUIString == "QML":
      gui = loadModule("gui_qml", "gui")
      # make device module available to the GUI module
    if gui:
      gui.dmod = dmod
    self.gui = gui


    # get possible module names
    moduleNames = self._getModuleNamesFromFolder(modulesFolder)
    # load if possible
    for moduleName in moduleNames:
        # filter out .py
        moduleName = moduleName.split('.')[0]
        loadModule(moduleName, moduleName[4:])

    print "Loaded all modules in %1.2f ms, initialising" % (1000 * (time.clock() - start))
    self.addTime("all modules loaded")

    # make sure all modules have the device module and other variables before first time
    for m in self.m.values():
      m.modrana = self # make this class accessible from modules
      m.dmod = self.dmod

      # run what needs to be done before firstTime is called
#    self._modulesLoadedPreFirstTime()

    start = time.clock()
    for m in self.m.values():
      m.firstTime()

      # run what needs to be done after firstTime is called
    self._modulesLoadedPostFirstTime()

    print( "Initialization complete in %1.2f ms" % (1000 * (time.clock() - start)) )

    # add last timing checkpoint
    self.addTime("all modules initialized")

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
      print( " * %s: %s (%1.2f ms)" % (name, self.m[name].__doc__, (1000 * (time.clock() - startM))) )
      return module
    except Exception, e:
      print( "modRana: module: %s/%s failed to load" % (importName, modRanaName) )
      traceback.print_exc(file=sys.stdout) # find what went wrong
      return None

  def _modulesLoadedPreFirstTime(self):
    """this is run after all the modules have been loaded,
    but before their first time is called"""
    self._updateCenteringShiftCB()

    """to only update values needed for map drawing when something changes
       * window is resized
       * user switches something related in options
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
    # check if own Quit button is needed
    if self.dmod.needsQuitButton():
      menus = self.m.get('menu', None)
      if menus:
        menus.addItem('main', 'Quit', 'quit', 'menu:askQuit')

  def _modulesLoadedPostFirstTime(self):
    """this is run after all the modules have been loaded,
    after before their first time is called"""
    
    # check if redrawing time should be printed to terminal
    if 'showRedrawTime' in self.d and self.d['showRedrawTime'] == True:
      self.showRedrawTime = True

  def getModule(self, name, default=None):
    """
    return a given module instance, return default if no instance
    with given name is found
    """
    return self.m.get(name, default)

  def getModules(self):
    """
    return the dictionary of all loaded modules
    """
    return self.m

  def update(self):
    """perform module state update"""
    # TODO: depreciate this
    # in favor of event based and explicit update timers
    for m in self.m.values():
      m.update()

  ## STARTUP AND SHUTDOWN ##

  def _startupDone(self):
    """called when startup has been finished"""

    # report startup time
    self.reportStartupTime()

    # check if loading options failed
    if self.optLoadingOK:
      self.gui.notify("Loading saved options failed", 7000)

    # start the mainloop or equivalent
    self.gui.startMainLoop()

  def shutdown(self):
    """
    start shutdown cleanup and stop GUI main loop
    when finished
    """
    print("Shutting-down modules")
    for m in self.m.values():
      m.shutdown()
    self._saveOptions()
    time.sleep(2) # leave some times for threads to shut down
    print("Shutdown complete")
    
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
        # return the value for current mode
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
      else: # just save to the key as usual
        self.d[name] = value
    else: # just save to the key as usual
      self.d[name] = value

    self._notifyWatcher(name, oldValue)
    """options are normally saved on shutdown,
    but for some data we want to make sure they are stored and not
    los for example because of power outage/empty battery, etc."""
    if save:
      options = self.m.get('options')
      if options:
        options.save()

  def optionsKeyExists(self, key):
    """Report if a given key exists"""
    return key in self.d.keys()

  def purgeKey(self, key):
    """remove a key from the persistent dictionary,
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
      print("modrana: can't purge a not-present key: %s" % key)

  def watch(self, key, callback, *args):
    """add a callback on an options key
    callback will get:
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
    * the watcher is notified before the key is written to the persistent
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
          print("invalid watcher callback :", callback)

  def addKeyModifier(self, key, modifier=None, mode=None, copyInitialValue=True):
    """add a key modifier
    NOTE: currently only used to make value of some keys
    dependent on the current mode"""
    options = self.m.get('options', None)
    # remember the old value, if not se use default from options
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
        # remember the old value, if not se use default from options
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

  def _updateCenteringShiftCB(self, key=None, oldValue=None, newValue=None):
    """update shifted centering amount

    this method is called if posShiftAmount or posShiftDirection
    are set and also once at startup"""
    # get the needed values
    # NOTE: some of them might have been updated just now
    (sx,sy,sw,sh) = self.get('viewport')
    shiftAmount = self.d.get('posShiftAmount', 0.75)
    shiftDirection = self.d.get('posShiftDirection', "down")
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
      """ we don't need to do anything if direction is set to don't shift (False)
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
    centerLLDistance = simplePythagoreanDistance(centerX, centerY, sw, sh)
    diagonal = max(ulCenterDistance, centerLLDistance)
    add = int(math.ceil(float(diagonal)/tileSide))
    self.expandViewportTiles = add

  def _modeChangedCB(self, key=None, oldMode=None, newMode=None):
    """handle mode change in regards to key modifiers and option key watchers"""
    # get keys that have both a key modifier and a watcher
    keys = filter(lambda x: x in self.keyModifiers.keys(), self.watches.keys())
    """ filter out only those keys that have a modifier for the new mode or
    had a modifier in the previous mode
    otherwise their value would not change and thus triggering a watch is not necessary """
    keys = filter(
                  lambda x: newMode in self.keyModifiers[x]['modes'].keys() or oldMode in self.keyModifiers[x]['modes'].keys(),
                  keys )
    for key in keys:
      # try to get some value if the old value is not available
      options = self.m.get('options', None)
      # remember the old value, if not se use default from options
      # if available
      if options:
        defaultValue = options.getKeyDefault(key, None)
      else:
        defaultValue = None
      oldValue = self.get(key, defaultValue)
      # notify watchers
      self._notifyWatcher(key, oldValue)


  def _removeNonPersistentOptions(self, inputDict):
    """keys that begin with # are not saved
    (as they mostly contain data that is either time sensitive or is
    reloaded on startup)
    ASSUMPTION: keys are strings of length>=1"""
    try:
      return dict((k, v) for k, v in inputDict.iteritems() if k[0] != '#')
    except Exception, e:
      print('options: error while filtering options\nsome nonpersistent keys might have been left in\nNOTE: keys should be strings of length>=1\n', e)
      return self.d

  def _saveOptions(self):
    print("modRana: saving options")
    try:
      f = open(self.paths.getOptionsFilePath(), "w")
      # remove keys marked as nonpersistent
      self.d['keyModifiers'] = self.keyModifiers
      d = self._removeNonPersistentOptions(self.d)
      marshal.dump(d, f)
      f.close()
      print("modRana: options successfully saved")
    except IOError:
      print("modRana: Can't save options")
    except Exception, e:
      print("modRana: saving options failed:", e)

  def _loadOptions(self):
    print("modRana: loading options")
    success = False
    try:
      f = open(self.paths.getOptionsFilePath(), "r")
      newData = marshal.load(f)
      f.close()
      # TODO: check out if this is needed anymore
      if 'tileFolder' in newData: #TODO: do this more elegantly
        del newData['tileFolder']
      if 'tracklogFolder' in newData: #TODO: do this more elegantly
        del newData['tracklogFolder']
      for k,v in newData.items():
        self.set(k,v)
      success = True
    except Exception, e:
      print("modRana: exception while loading saved options:\n%s" % e)
      #TODO: a yes/no dialog for clearing (renaming with timestamp :) the corrupted options file (options.bin)
      success = False

    self.overrideOptions()
    return success

  def overrideOptions(self):
    """
    without this, there would not be any projection values at start,
    because modRana does not know, what part of the map to show
    """
    self.set('centred', True) # set centering to True at start to get setView to run
    self.set('editBatchMenuActive', False)

  ## PROFILE PATH ##

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

  ## MAP LAYERS ##
  """map layer information is important and needed by many modules during their initialization,
  so it is handled here"""
  def getMapLayers(self):
    return self.configs.getMapLayers()

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
      print("** modRana startup timing **")

      # print device identificator and name
      if self.dmod:
        deviceName = self.dmod.getDeviceName()
        deviceString = self.dmod.getDeviceIDString()
        print("# device: %s (%s)" % (deviceName, deviceString))

      tl = self.timing
      startupTime = tl[0][1] * 1000
      lastTime = startupTime
      totalTime = (tl[-1][1] * 1000) - startupTime
      for i in tl:
        (message, t) = i
        t = 1000 * t # convert to ms
        timeSpent = t - lastTime
        timeSinceStart = t - startupTime
        print( "* %s (%1.0f ms), %1.0f/%1.0f ms" % (message, timeSpent, timeSinceStart, totalTime))
        lastTime = t
      print("** whole startup: %1.0f ms **" % totalTime)
    else:
      print("* timing list empty *")

if __name__ == "__main__":

  # check if reload has been requested

  reloadArg = "--reload"
  if len(sys.argv)>=3 and sys.argv[1] == reloadArg:
    # following argument is path to the modRana main class we want to reload to,
    # optionally followed by any argument for the main class
    print(" == modRana Reloading == ")
    reloadPath = sys.argv[2]
    callArgs = [reloadPath]
    callArgs.extend(sys.argv[3:])
    subprocess.call(callArgs)

  else:
    print(" == modRana Starting == ")

    program = ModRana()


