#!/usr/bin/env python
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
import subprocess
import sys
import time

startTimestamp = time.time()
import os
import marshal
import traceback
import imp
# import core modules/classes
from core import startup
from core import utils
from core import paths
from core import configs
from core import threads
from core import gs
from core import singleton
from core.backports import six
# record that imports-done timestamp
importsDoneTimestamp = time.time()

MAIN_MODULES_FOLDER = 'modules'
DEVICE_MODULES_FOLDER = os.path.join(MAIN_MODULES_FOLDER, "device_modules")
GUI_MODULES_FOLDER = os.path.join(MAIN_MODULES_FOLDER, "gui_modules")
ALL_MODULE_FOLDERS = [
    MAIN_MODULES_FOLDER,
    DEVICE_MODULES_FOLDER,
    GUI_MODULES_FOLDER
]


class ModRana(object):
    """
    This is THE main modRana class.
    """

    def __init__(self):
        singleton.modrana = self

        self.timing = []
        self.addCustomTime("modRana start", startTimestamp)
        self.addCustomTime("imports done", importsDoneTimestamp)

        # constants & variable initialization
        self.dmod = None # device specific module
        self.gui = None
        self.GUIString = ""
        self.optLoadingOK = None

        self.d = {} # persistent dictionary of data
        self.m = {} # dictionary of loaded modules
        self.watches = {} # List of data change watches
        self.maxWatchId = 0

        self.initInfo = {
            'modrana': self,
            'device': None, # TODO: do this directly
            'name': ""
        }

        self.mapRotationAngle = 0 # in radians
        self.notMovingSpeed = 1 # in m/s

        # per mode options
        # NOTE: this variable is automatically saved by the
        # options module
        self.keyModifiers = {}

        # initialize threading
        threads.initThreading()

        # start timing modRana launch
        self.addTime("GUI creation")

        # add the startup handling core module
        self.startup = startup.Startup(self)
        self.args = self.startup.getArgs()

        # handle any early tasks specified from CLI
        self.startup.handleEarlyTasks()

        # early CLI tasks might need a "silent" modRana
        # so the startup announcement is here
        print(" == modRana Starting == ")

        # add the paths handling core module
        self.paths = paths.Paths(self)

        # print(version string)
        version = self.paths.getVersionString()
        if version is None:
            version = "unknown version"
        print("  %s" % version)

        # add the configs handling core module
        self.configs = configs.Configs(self)

        # load persistent options
        self.optLoadingOK = self._loadOptions()

        # check if upgrade took place

        if self.optLoadingOK:
            savedVersionString = self.get('modRanaVersionString', "")
            versionStringFromFile = self.paths.getVersionString()
            if savedVersionString != versionStringFromFile:
                print("modRana: possible upgrade detected")
                self._postUpgradeCheck()

        # save current version string
        self.set('modRanaVersionString', self.paths.getVersionString())

        # load all configuration files
        self.configs.loadAll()

        # start loading modules

        # device module first
        self._loadDeviceModule()

        # handle tasks that require the device
        # module but not GUI
        self.startup.handleNonGUITasks()

        # then the GUI module
        self._loadGUIModule()

        # and all other modules
        self._loadModules()

        # startup done, print some statistics
        self._startupDone()

    def _postUpgradeCheck(self):
        """
        perform post upgrade checks
        """
        self.configs.upgradeConfigFiles()

    ##  MODULE HANDLING ##

    def _loadDeviceModule(self):
        """Load the device module"""
        if self.dmod: # don't reload the module
            return

        # get the device module string
        # (a unique device module string identificator)
        if self.args.d:
            device = self.args.d
        else: # no device specified from CLI
            # try to auto-detect the current device
            from core import platform_detection

            device = platform_detection.getBestDeviceModuleId()

        device = device.lower() # convert to lowercase

        self.initInfo["device"] = device

        # get GUI ID from the CLI argument
        if self.args.u:
            try:
                self.GUIString = self.args.u.split(":")[0]
            except Exception:
                e = sys.exc_info()[1]
                print('modRana: splitting the GUI string failed')
                print(e)
        else: # no ID specified
            # the N900 device module needs the GUIString
            # at startup
            if device == "n900":
                self.GUIString = "GTK"

        # set the pre-import-visible GUIString
        # for the device module
        gs.GUIString = self.GUIString

        ## load the device specific module

        # NOTE: other modules need the device and GUI modules
        # during init
        deviceModulesPath = os.path.join(MAIN_MODULES_FOLDER, "device_modules")
        sys.path.append(deviceModulesPath)
        dmod = self._loadModule("device_%s" % device, "device")
        if dmod is None:
            print("modRana: !! device module failed to load !!\n"
                  "loading the Neo device module as fail-safe")
            device = "neo"
            dmod = self._loadModule("device_%s" % device, "device")
        self.dmod = dmod

        # if no GUIString was specified from CLI,
        # get preferred GUI module strings from the device module

        if self.GUIString == "":
            ids = self.dmod.getSupportedGUIModuleIds()
            if ids:
                self.GUIString = ids[0]
            else:
                self.GUIString = "GTK" # fallback
                # export the GUI string
                # set the pre-import visible GUI string and subtype
        splitGUIString = self.GUIString.split(":")
        gs.GUIString = splitGUIString[0]
        if len(splitGUIString) >= 2:
            gs.GUISubtypeString = splitGUIString[1]

            # TODO: if loading GUI module fails, retry other modules in
            # order of preference as provided by the  device module

    def _loadGUIModule(self):
        """load the GUI module"""

        # add the GUI module folder to path
        GUIModulesPath = os.path.join(MAIN_MODULES_FOLDER, "gui_modules")
        sys.path.append(GUIModulesPath)
        gui = None
        splitGUIString = self.GUIString.split(":")

        GUIModuleId = splitGUIString[0]
        if len(splitGUIString) > 1:
            subtypeId = splitGUIString[1]
        else:
            subtypeId = None

        if GUIModuleId == "GTK":
            gui = self._loadModule("gui_gtk", "gui")
        elif GUIModuleId == "QML":
            gui = self._loadModule("gui_qml", "gui")
            # make device module available to the GUI module
        if gui:
            gui.setSubtypeId(subtypeId)
            gui.dmod = self.dmod
        self.gui = gui

    def _loadModules(self):
        """load all "normal" (other than device & GUI) modules"""

        print("importing modules:")
        start = time.clock()

        # make shortcut for the loadModule function
        loadModule = self._loadModule

        # get possible module names
        moduleNames = self._getModuleNamesFromFolder(MAIN_MODULES_FOLDER)
        # load if possible
        for moduleName in moduleNames:
            # filter out .py
            moduleName = moduleName.split('.')[0]
            loadModule(moduleName, moduleName[4:])

        print("Loaded all modules in %1.2f ms, initialising" % (1000 * (time.clock() - start)))
        self.addTime("all modules loaded")

        # make sure all modules have the device module and other variables before first time
        for m in self.m.values():
            m.modrana = self # make this class accessible from modules
            m.dmod = self.dmod

            # run what needs to be done before firstTime is called
        self._modulesLoadedPreFirstTime()

        start = time.clock()
        for m in self.m.values():
            m.firstTime()

        # run what needs to be done after firstTime is called
        self._modulesLoadedPostFirstTime()

        print( "Initialization complete in %1.2f ms" % (1000 * (time.clock() - start)) )

        # add last timing checkpoint
        self.addTime("all modules initialized")

    def _getModuleNamesFromFolder(self, folder, prefix='mod_'):
        """list a given folder and find all possible module names
        Module names:
        Module names start with the "mod_" and don't end with .pyc or .pyo.
        Consequences:
        Valid modules need to have an existing .py file or be folder-modules
        (don't name a folder module mod_foo.pyc :) ), even if they are
        actually loaded from the .pyc or .pyo in the end.
        This is done so that dangling .pyc/.pyo file from a module
        that was removed are not loaded by mistake.
        This situation shouldn't really happen if modRana is installed from a package,
        as all .pyc files are purged during package upgrade and regenerated."""
        moduleNames = filter(
            lambda x: x[0:len(prefix)] == prefix, os.listdir(folder)
        )
        # remove the extension
        moduleNames = map(lambda x: os.path.splitext(x)[0], moduleNames)
        # return a set of unique module names
        # * like this, two module names will not be returned if there are
        # both py and pyc files
        return set(moduleNames)

    def _listAvailableDeviceModulesByID(self):
        moduleNames = self._getModuleNamesFromFolder(DEVICE_MODULES_FOLDER, prefix='device_')
        # remove the device_ prefix and return the results
        # NOTE: .py, .pyc & .pyo should be removed already in _getModuleNamesFromFolder()
        # also sort the module names alphabetically
        return sorted(map(lambda x: x[7:], moduleNames))

    def _listAvailableGUIModulesByID(self):
        return self._getModuleNamesFromFolder(GUI_MODULES_FOLDER)

    def _loadModule(self, importName, modRanaName):
        """load a single module by name from path"""
        startM = time.clock()
        fp = None
        try:
            fp, pathName, description = imp.find_module(importName, ALL_MODULE_FOLDERS)
            a = imp.load_module(importName, fp, pathName, description)
            initInfo = self.initInfo
            initInfo['name'] = modRanaName
            module = a.getModule(self.m, self.d, initInfo)
            self.m[modRanaName] = module
            print(
            " * %s: %s (%1.2f ms)" % (modRanaName, self.m[modRanaName].__doc__, (1000 * (time.clock() - startM))) )
            return module
        except Exception:
            e = sys.exc_info()[1]
            print( "modRana: module: %s/%s failed to load" % (importName, modRanaName) )
            print(e)
            print("traceback:")
            traceback.print_exc(file=sys.stdout) # find what went wrong
            return None
        finally:
            if fp:
                fp.close()

    def _modulesLoadedPreFirstTime(self):
        """this is run after all the modules have been loaded,
        but before their first time is called"""

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

        # run any tasks specified by CLI arguments
        self.startup.handlePostFirstTimeTasks()


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
            if mode is None:
                mode = self.d.get('mode', 'car')
            if mode in self.keyModifiers[name]['modes'].keys():
                # get the dictionary with per mode values
                multiDict = self.d.get('%s#multi' % name, {})
                # return the value for current mode
                return multiDict.get(mode, default)
            else:
                return self.d.get(name, default)

        else: # just return the normal value
            return self.d.get(name, default)

    def set(self, name, value, save=False, mode=None):
        """Set an item of data,
        if there is a watch set for this key,
        notify the watcher that its value has changed"""

        oldValue = self.get(name, value)

        if name in self.keyModifiers.keys():
            # get the current mode
            if mode is None:
                mode = self.d.get('mode', 'car')
                # check if there is a modifier for the current mode
            if mode in self.keyModifiers[name]['modes'].keys():
                # save it to the name + #multi key under the mode key
                try:
                    self.d['%s#multi' % name][mode] = value
                except KeyError: # key not yet created
                    self.d['%s#multi' % name] = {mode: value}
            else: # just save to the key as usual
                self.d[name] = value
        else: # just save to the key as usual
            self.d[name] = value

        self._notifyWatcher(name, oldValue)
        # options are normally saved on shutdown,
        # but for some data we want to make sure they are stored and not
        # lost for example because of power outage/empty battery, etc.
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
                # also remove the possibly present
                # alternative states for different modes"""
                multiKey = "%s#multi" % key
                if multiKey in self.d:
                    del self.d[multiKey]
            self._notifyWatcher(key, oldValue)
            return True
        else:
            print("modrana: can't purge a not-present key: %s" % key)

    def watch(self, key, callback, args=None, runNow=False):
        """add a callback on an options key
        callback will get:
        key, newValue, oldValue, *args

        NOTE: watch ids should be >0, so that they evaluate as True
        """
        if not args: args = []
        nrId = self.maxWatchId + 1
        id = "%d_%s" % (nrId, key)
        self.maxWatchId = nrId # TODO: recycle ids ? (alla PID)
        if key not in self.watches:
            self.watches[key] = [] # create the initial list
        self.watches[key].append((id, callback, args))
        # should we now run the callback one ?
        # -> this is useful for modules that configure
        # themselves according to an options value at startup
        if runNow:
            currentValue = self.get(key, None)
            callback(key, currentValue, currentValue, *args)
        return id

    def removeWatch(self, id):
        """remove watch specified by the given watch id"""
        (nrId, key) = id.split('_')
        if key in self.watches:
            remove = lambda x: x[0] == id
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
                (id, callback, args) = item
                # rather supply the old value than None
                newValue = self.get(key, oldValue)
                if callback:
                    if callback(key, oldValue, newValue, *args) == False:
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
        oldValue = self.get(key, defaultValue)
        if mode is None:
            mode = self.d.get('mode', 'car')
        if key not in self.keyModifiers.keys(): # initialize
            self.keyModifiers[key] = {'modes': {mode: modifier}}
        else:
            self.keyModifiers[key]['modes'][mode] = modifier

        # make sure the multi mode dictionary exists
        multiKey = '%s#multi' % key
        multiDict = self.d.get(multiKey, {})
        self.d[multiKey] = multiDict

        # if the modifier is set for the first time,
        # do we copy the value from the normal key or not ?
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
        if mode is None:
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
                oldValue = self.get(key, defaultValue)
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
        if mode is None:
            mode = self.d.get('mode', 'car')
        if key in self.keyModifiers.keys():
            return mode in self.keyModifiers[key]['modes'].keys()
        else:
            return False

    def notify(self, message, msTimeout=0, icon=""):
        notify = self.m.get('notification')
        if notify:
            # the notification module counts timeout in seconds
            sTimeout = msTimeout / 1000.0
            notify.handleNotification(message, sTimeout, icon)

    def getModes(self):
        """return supported modes"""
        modes = {
            'cycle': 'Cycle',
            'walk': 'Foot',
            'car': 'Car',
            'train': 'Train',
            'bus': 'Bus',
        }
        return modes

    def getModeLabel(self, modeName):
        """get a label for a given mode"""
        try:
            return self.getModes()[modeName]
        except KeyError:
            print('modrana: mode %s does not exist and thus has no label' % modeName)
            return None

    def _modeChangedCB(self, key=None, oldMode=None, newMode=None):
        """handle mode change in regards to key modifiers and option key watchers"""
        # get keys that have both a key modifier and a watcher
        keys = filter(lambda x: x in self.keyModifiers.keys(), self.watches.keys())
        # filter out only those keys that have a modifier for the new mode
        # or had a modifier in the previous mode
        # otherwise their value would not change and thus
        # triggering a watch is not necessary
        keys = filter(
            lambda x: newMode in self.keyModifiers[x]['modes'].keys() or oldMode in self.keyModifiers[x][
                'modes'].keys(),
            keys)
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
            return dict((k, v) for k, v in six.iteritems(inputDict) if k[0] != '#')
        except Exception:
            e = sys.exc_info()[1]
            print(
                'options: error while filtering options\nsome nonpersistent keys might have been left in\nNOTE: keys should be strings of length>=1\n',
                e)
            return self.d

    def _saveOptions(self):
        """save the persistent dictionary to file"""
        print("modRana: saving options")
        try:
            f = open(self.paths.getOptionsFilePath(), "wb")
            # remove keys marked as nonpersistent
            self.d['keyModifiers'] = self.keyModifiers
            d = self._removeNonPersistentOptions(self.d)
            marshal.dump(d, f)
            f.close()
            print("modRana: options successfully saved")
        except IOError:
            print("modRana: Can't save options")
        except Exception:
            e = sys.exc_info()[1]
            print("modRana: saving options failed:", e)

    def _loadOptions(self):
        """load the persistent dictionary from file"""
        print("modRana: loading options")
        try:
            f = open(self.paths.getOptionsFilePath(), "rb")
            newData = marshal.load(f)
            f.close()
            purgeKeys = ["fix"]
            for key in purgeKeys:
                if key in newData:
                    del newData[key]
            for k, v in newData.items():
                self.set(k, v)
            success = True
            #print("Options content")
            #for key, value in newData.iteritems():
            #    print(key, value)


        except Exception:
            e = sys.exc_info()[1]
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
        userHomePath = os.getenv("HOME", "")
        profileFolderPath = os.path.join(userHomePath, modRanaProfileFolderName)
        # make sure it exists
        utils.createFolderPath(profileFolderPath)
        # return it
        return profileFolderPath

    ## STARTUP TIMING ##

    def addTime(self, message):
        timestamp = time.time()
        self.timing.append((message, timestamp))
        return timestamp

    def addCustomTime(self, message, timestamp):
        self.timing.append((message, timestamp))
        return timestamp

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
                t *= 1000# convert to ms
                timeSpent = t - lastTime
                timeSinceStart = t - startupTime
                print( "* %s (%1.0f ms), %1.0f/%1.0f ms" % (message, timeSpent, timeSinceStart, totalTime))
                lastTime = t
            print("** whole startup: %1.0f ms **" % totalTime)
        else:
            print("* timing list empty *")


if __name__ == "__main__":
    # change to folder where the main modRana file is located
    # * this enables to run modRana with absolute path without adverse
    # effect such as modRana not finding modules or
    currentAbsolutePath = os.path.dirname(os.path.abspath(__file__))
    os.chdir(currentAbsolutePath)
    # add the modules folder to path, so that third-party modules (such as Upoints),
    # that expect to be placed to path work correctly
    sys.path.append(os.path.join(currentAbsolutePath, 'modules'))

    # check if reload has been requested
    reloadArg = "--reload"
    if len(sys.argv) >= 3 and sys.argv[1] == reloadArg:
        # following argument is path to the modRana main class we want to reload to,
        # optionally followed by any argument for the main class
        print(" == modRana Reloading == ")
        reloadPath = sys.argv[2]
        callArgs = [reloadPath]
        callArgs.extend(sys.argv[3:])
        subprocess.call(callArgs)
    else:
        program = ModRana()


