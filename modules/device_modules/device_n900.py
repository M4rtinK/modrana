# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# modRana N900 module
# It is a basic modRana module, that has some special features
# and is loaded only on the correpsponding device.
#----------------------------------------------------------------------------
# Copyright 2010, Martin Kolman
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
import subprocess
import time
from base_device_module import DeviceModule, DEVICE_SMARTPHONE
#N900 specific:
import dbus.glib

from core import gs
# only import GTK, Hildon & Liblocation when using GTK GUI
if gs.GUIString == "GTK":
    import hildon
    import location
    import conic # provide by python-conic on Maemo 5
    # NOTE: conic imports Glib & Gobject, which cause segfaults for the Qt based QML GUI
    # therefore, it is important it is loaded only with fort the GTK GUI
    #  import dbus.glib
    import gtk
    # why dbus.glib ?
    # if you import only "dbus", it can't find its mainloop for callbacks
elif gs.GUIString == "QML":
    from QtMobility.SystemInfo import QSystemScreenSaver
    # ^^ back-light control for QML GUI

TRACKLOGS_PATH = "/home/user/MyDocs/tracklogs"
MAP_FOLDER_PATH = "/home/user/MyDocs/.maps/"
POI_FOLDER_PATH = "/home/user/MyDocs/.maps"
DEBUG_LOG_FOLDER_PATH = "/home/user/MyDocs/modrana_debug_logs/"


def getModule(m, d, i):
    return DeviceN900(m, d, i)


class DeviceN900(DeviceModule):
    """A N900 modRana device-specific module"""

    def __init__(self, m, d, i):
        DeviceModule.__init__(self, m, d, i)
        self.rotationObject = None
        # start the N900 specific automatic GUI rotation support
        self.done = False

        #osso app name
        self.ossoAppName = 'modrana'

        # screen blanking related
        self.bus = dbus.SystemBus()
        self.mceRequest = self.bus.get_object('com.nokia.mce', '/com/nokia/mce/request')
        self.mceSignal = self.bus.get_object('com.nokia.mce', '/com/nokia/mce/signal')
        self.mceSignalInterface = dbus.Interface(self.mceSignal, 'com.nokia.mce.signal')
        self.mceSignalInterface.connect_to_signal("display_status_ind", self.screenStateChangedCallback)
        print("N900: DBUS initialized")

        # Internet connectivity related
        self.connectivityStatus = False
        self.conicConnection = None

        # Mainloop for headless location support
        self.mainloop = None

        if gs.GUIString == "GTK":
            # liblocation
            self.lControl = None
            self.lDevice = None
            """location starting is handled by mod_location
            in its firstTime call"""

            # libconic
            self._conicConnect()

        elif gs.GUIString == "QML":
            print("N900 Qt screen saver controller created")
            self.qScreenSaver = QSystemScreenSaver()

        print("N900 device specific module initialized")

    def _conicConnect(self):
        if self.conicConnection is None:
            self.conicConnection = conic.Connection()
            self.conicConnection.connect("connection-event", self._connectionStateCB)
            self.conicConnection.set_property("automatic-connection-events", True)
            #Todo: connectivity state monitoring for the QML GUI (Qt mobility probably does this ?)


    def firstTime(self):
        # setup window state callbacks
        gui = self.modrana.gui
        if gs.GUIString == "GTK":
            # load the rotation object
            rotationObject = self.startAutorotation()
            if rotationObject != False:
                print("N900: rotation object loaded")
                self.rotationObject = rotationObject
            else:
                print("N900: loading rotation object failed")

            self.topWindow = gui.getGTKTopWindow()

            # app menu and buttons
            self.centeringToggleButton = None
            self.rotationToggleButton = None
            self.soundToggleButton = None
            self._addHildonAppMenu()
            print("N900: application menu added")

            # window-active detection
            self.topWindow.connect('notify::is-active', self.windowIsActiveChangedCallback)
            # on Maemo 5@N900, is-active == True signalizes that the modRana window is
            # the current active window (there is always only one active window)
            # is-active == False signalizes that the window is either minimized on the
            # dashboard or the screen is blanked
            # enable volume keys usage
            if self.get('useVolumeKeys', True):
                self._updateVolumeKeys()

    def shutdown(self):
        # disconnect libconic connection tracking
        if self.conicConnection:
            self.conicConnection.set_property("automatic-connection-events", False)

    def startInFullscreen(self):
        return True

    def fullscreenOnly(self):
        return False

    def handleMessage(self, message, messageType, args):
        if message == 'modeChanged':
            rotationMode = self.get('rotationMode', None)
            if rotationMode:
                self.setRotationMode(rotationMode)
                print("rotation mode changed")
        elif message == 'updateKeys':
            self._updateVolumeKeys()

    def getDeviceIDString(self):
        return "n900"

    def getDeviceName(self):
        return "Nokia N900"

    def getWinWH(self):
        return 800, 480

    def startInFullscreen(self):
        return True

    def getSupportedGUIModuleIds(self):
        return ["GTK", "QML:harmattan", "QML:indep"]

    def startAutorotation(self):
        """start the GUI automatic rotation feature"""
        try:
            import n900_maemo5_portrait

            rotationMode = self.get('rotationMode', "auto") # get last used mode
            lastModeNumber = self.getRotationModeNumber(rotationMode) # get last used mode number
            rObject = n900_maemo5_portrait.FremantleRotation(self.ossoAppName, main_window=self.topWindow,
                                                             mode=lastModeNumber)
            print("N900 rotation object initialized")
            return rObject
        except Exception:
            import sys

            e = sys.exc_info()[1]
            print("initializing N900 rotation object failed")
            print(e)

    def setRotationMode(self, rotationMode):
        rotationModeNumber = self.getRotationModeNumber(rotationMode)
        self.rotationObject.set_mode(rotationModeNumber)

    def getRotationModeNumber(self, rotationMode):
        if rotationMode == "auto":
            return 0
        elif rotationMode == "landscape":
            return 1
        elif rotationMode == "portrait":
            return 2

    def screenBlankingControlSupported(self):
        """it is possible to control screen blanking on the N900"""
        return True

    def usesDashboard(self):
        """the N900 uses a dashboard type task switcher"""
        return True

    def pauseScreenBlanking(self):
        if gs.GUIString == "GTK":
        #      print("n900: pausing screen blanking in GTK GUI")
            self.mceRequest.req_display_blanking_pause()
        elif gs.GUIString == "QML":
        #      print("n900: pausing screen blanking in QML GUI")
            QSystemScreenSaver.setScreenSaverInhibit(self.qScreenSaver)

    def unlockScreen(self):
        self.mceRequest.req_tklock_mode_change('unlocked')

    def windowIsActiveChangedCallback(self, window, event):
        """this is called when the window gets or looses focus
        it basically means:
        - has focus - it is the active window and the user is working wit it
        - no focus -> the window is switched to dashboard or the another window is active or
        the screen is blanked"""
        redrawOnDashboard = self.get('redrawOnDashboard', False)
        # NOTE: this updates the snapshot in task switcher,
        # but also UPDATES WHEN MINIMISED AND NOT VISIBLE
        # so use with caution
        # blanking overrides this so when the screen is blanked it does not redraw
        # TODO: see if hildon signalizes that a the task switcher is visible or not

        if not redrawOnDashboard: # we don't redraw on dashboard by default
            display = self.m.get('display', None)
            if display:
                if window.is_active():
                    display.enableRedraw(reason="N900 window is active")
                else:
                    # check if text entry is in progress
                    textEntry = self.m.get('textEntry', None)
                    if textEntry:
                        if textEntry.isEntryBoxVisible():
                            # we redraw modRana behind text entry box
                            return
                    display.disableRedraw(reason="N900 window is not active")

    def screenStateChangedCallback(self, state):
        """this is called when the display is blanked or un-blanked"""
        display = self.m.get('display', None)
        if display:
            if state == "on" or state == "dimm":
                display.enableRedraw(reason="N900 display on or dimmed")
            elif state == "off":
                display.disableRedraw(reason="N900 display blanked")

    def hasNotificationSupport(self):
        if gs.GUIString == "GTK":
            return True
        else:
            return False

    def notify(self, message, msTimeout=0, icon="icon_text"):
        """the third parameter has to be a non zero-length string or
        else the banner is not created"""
        #TODO: find what strings to submit to actually get an icon displayed

        if len(icon) == 0:
            icon = "spam" # as mentioned above, the string has to be longer than zero
        if gs.GUIString == "GTK":
            topWindow = self.modrana.gui.getWindow()
            banner = hildon.hildon_banner_show_information_with_markup(topWindow, icon, message)
            if msTimeout:
                banner.set_timeout(msTimeout)
        else:
            print("n900: the N900 device module currently handles only Hildon based notifications")

    def hasButtons(self):
        """the N900 has the volume keys (2 buttons), the camera trigger (2 states)
        and the proximity sensor,
        other than that state of the camera cover and keyboard slider can be sensed
        AND there is the accelerometer and light sensor :)
        """
        return True

    def hasVolumeKeys(self):
        return True

    def enableVolumeKeys(self):
        if self.topWindow.flags() & gtk.REALIZED:
            self.enable_volume_cb()
        else:
            self.topWindow.connect("realize", self.enable_volume_cb)

    def disableVolumeKeys(self):
        self.topWindow.window.property_change(gtk.gdk.atom_intern("_HILDON_ZOOM_KEY_ATOM"),
                                              gtk.gdk.atom_intern("INTEGER"),
                                              32, gtk.gdk.PROP_MODE_REPLACE, [0]);

    def enable_volume_cb(self, window=None):
        self.topWindow.window.property_change(gtk.gdk.atom_intern("_HILDON_ZOOM_KEY_ATOM"),
                                              gtk.gdk.atom_intern("INTEGER"),
                                              32, gtk.gdk.PROP_MODE_REPLACE, [1]);

    def _updateVolumeKeys(self):
        """check if volume keys should be used or not"""
        if self.get('useVolumeKeys', True):
            self.enableVolumeKeys()
        else:
            self.disableVolumeKeys()


    # ** Hildon App menu **

    def handlesUrlOpening(self):
        """
        PyGTK version on Maemo 5 is too old and does not have the gtk.open_uri() function,
        -> a platform specific implementation is needed
        """
        return True

    def openUrl(self, url):
        """
        open a URL using the Maemo specific browser command
        """
        subprocess.Popen(['browser', '--url=%s' % url])

    def _addHildonAppMenu(self):
        menu = hildon.AppMenu()
        self.centeringToggleButton = gtk.ToggleButton(label="Centering")
        self.centeringToggleButton.connect('toggled', self._toggle, 'centred')
        self.rotationToggleButton = gtk.ToggleButton(label="Map rotation")
        self.rotationToggleButton.connect('toggled', self._toggle, 'rotateMap')
        self.soundToggleButton = gtk.ToggleButton(label="Sound")
        self.soundToggleButton.connect('toggled', self._toggle, 'soundEnabled')

        mapButton = gtk.Button("Map screen")
        mapButton.connect('clicked', self._switchToMenu, None)
        optionsButton = gtk.Button("Options")
        optionsButton.connect('clicked', self._switchToMenu, 'options')
        searchButton = gtk.Button("Search")
        searchButton.connect('clicked', self._switchToMenu, 'search')
        routeButton = gtk.Button("Route")
        routeButton.connect('clicked', self._switchToMenu, 'route')

        self._updateAppMenu() # update initial button states

        menu.append(self.centeringToggleButton)
        menu.append(self.rotationToggleButton)
        menu.append(self.soundToggleButton)
        menu.append(mapButton)
        menu.append(optionsButton)
        menu.append(searchButton)
        menu.append(routeButton)

        # Show all menu items
        menu.show_all()

        # Add the menu to the window
        self.topWindow.set_app_menu(menu)

        # register callbacks to update upp menu toggle buttons
        # when the controlled value changes from elsewhere
        self.watch('rotateMap', self._updateAppMenu)
        self.watch('soundEnabled', self._updateAppMenu)
        self.watch('centred', self._updateAppMenu)


    def _toggle(self, toggleButton, key):
        print("N900: key %s toggled" % key)
        self.set(key, toggleButton.get_active())

    def _switchToMenu(self, toggleButton, menu):
        """callback for the appMenu buttons, switch to a specified menu"""
        self.set('menu', menu)
        self.set('needRedraw', True)

    def _updateAppMenu(self, key=None, value=None, oldValue=None):
        print(self.get("centred", True))
        if self.centeringToggleButton:
            self.centeringToggleButton.set_active(self.get("centred", True))
        if self.rotationToggleButton:
            self.rotationToggleButton.set_active(self.get("rotateMap", True))
        if self.soundToggleButton:
            self.soundToggleButton.set_active(self.get("soundEnabled", True))

    def hasKineticScrollingList(self):
        return True

    # ** PATHS **

    def getTracklogFolderPath(self):
        return TRACKLOGS_PATH

    def getMapFolderPath(self):
        return MAP_FOLDER_PATH

    def getPOIFolderPath(self):
        return POI_FOLDER_PATH

    def getLogFolderPath(self):
        # N900 specific log folder
        return DEBUG_LOG_FOLDER_PATH

    def getRoutingDataFolderPath(self):
        # routing data is on the N900 traditionally stored
        # directly in the map folder, by using the path from
        # the paths module, if the map folder is redirected
        # by a configuration file value, path to the
        # routing data folder will also be redirected
        return self.modrana.paths.getMapFolderPath()

    # ** LOCATION **

    def handlesLocation(self):
        """on N900 location is handled through liblocation"""
        if gs.GUIString == "GTK":
            # use liblocation
            return True
        else:
            return False

    def getLocationType(self):
        """modRana uses liblocation on N900"""
        if gs.GUIString == "GTK":
            # use liblocation for GTK
            return "liblocation"
        else:
            # use Qt Mobility for Qt
            return "qt_mobility"

    def startLocation(self, startMainLoop=False):
        """this will called by mod_location automatically"""
        self._libLocationStart()
        if startMainLoop:
            import gobject

            self.mainloop = gobject.MainLoop()
            print('N900: location: starting headless mainloop')
            self.mainloop.run()

    def stopLocation(self):
        """this will called by mod_location automatically"""
        self._libLocationStop()
        if self.mainloop:
            print('N900: location: stopping headless mainloop')
            self.mainloop.quit()

    def _libLocationStart(self):
        """start the liblocation based location update method"""
        try:
            try:
                # as the location module drags inside gobject related modules
                # that make the QML GUI segfault, we need to make sure they are not
                # the module is not loaded when running the QML GUI
                if gs.GUIString != "QML":
                    import location
                self.lControl = location.GPSDControl.get_default()
                self.lDevice = location.GPSDevice()
            except Exception:
                import sys

                e = sys.exc_info()[1]
                print("n900 - location: - cant create location objects: %s" % e)

            try:
                self.lControl.set_properties(preferred_method=location.METHOD_USER_SELECTED)
            except Exception:
                import sys

                e = sys.exc_info()[1]
                print("n900 - location: - cant set preferred location method: %s" % e)

            try:
                self.lControl.set_properties(preferred_interval=location.INTERVAL_1S)
            except Exception:
                import sys

                e = sys.exc_info()[1]
                print("n900 - location: - cant set preferred location interval: %s" % e)
            try:
                self.lControl.start()
                print("** n900 - location: - GPS successfully activated **")
                self.connected = True
            except Exception:
                import sys

                e = sys.exc_info()[1]
                print("n900 - location: - opening the GPS device failed: %s" % e)
                self.status = "No GPSD running"

            # connect callbacks
            #self.lControl.connect("error-verbose", self._liblocationErrorCB)
            self.lDevice.connect("changed", self._libLocationUpdateCB)
            print("n900 - location: activated")
        except Exception:
            import sys

            e = sys.exc_info()[1]
            self.status = "No GPSD running"
            print("n900 - location: - importing location module failed, please install the python-location package")
            print(e)
            self.sendMessage('notification:install python-location package to enable GPS#7')


    def _libLocationStop(self):
        """stop the liblocation based location update method"""
        print('n900 - location: stopping')
        if self.lControl:
            self.lControl.stop()
            # cleanup
            self.lControl = None
            self.lDevice = None
            self.location = None

    def _liblocationErrorCB(self, control, error):
        if error == location.ERROR_USER_REJECTED_DIALOG:
            print("User didn't enable requested methods")
        elif error == location.ERROR_USER_REJECTED_SETTINGS:
            print("User changed settings, which disabled location")
        elif error == location.ERROR_BT_GPS_NOT_AVAILABLE:
            print("Problems with BT GPS")
        elif error == location.ERROR_METHOD_NOT_ALLOWED_IN_OFFLINE_MODE:
            print("Requested method is not allowed in offline mode")
        elif error == location.ERROR_SYSTEM:
            print("System error")

    def _libLocationUpdateCB(self, device):
        """from:  http://wiki.maemo.org/PyMaemo/Using_Location_API
        result tuple in order:
        * mode: The mode of the fix
        * fields: A bitfield representing which items of this tuple contain valid data
        * time: The timestamp of the update (location.GPS_DEVICE_TIME_SET)
        * ept: Time accuracy
        * latitude: Fix latitude (location.GPS_DEVICE_LATLONG_SET)
        * longitude: Fix longitude (location.GPS_DEVICE_LATLONG_SET)
        * eph: Horizontal position accuracy
        * altitude: Fix altitude in meters (location.GPS_DEVICE_ALTITUDE_SET)
        * double epv: Vertical position accuracy
        * track: Direction of motion in degrees (location.GPS_DEVICE_TRACK_SET)
        * epd: Track accuracy
        * speed: Current speed in km/h (location.GPS_DEVICE_SPEED_SET)
        * eps: Speed accuracy
        * climb: Current rate of climb in m/s (location.GPS_DEVICE_CLIMB_SET)
        * epc: Climb accuracy"""
        try:
            if device.fix:
                # make sure the location module is imported, but not with QML GUI
                # as the location module drags inside gobject related modules
                # that make the QML GUI segfault, we need to make sure they are not
                # the module is not loaded when running the QML GUI
                if gs.GUIString != "QML":
                    import location

                fix = device.fix
                self.set('fix', fix[0])
                # from liblocation reference:
                # 0 =	The device has not seen a satellite yet.
                # 1 =	The device has no fix.
                # 2 =	The device has latitude and longitude fix.
                # 3 =	The device has latitude, longitude, and altitude.
                if fix[1] & location.GPS_DEVICE_LATLONG_SET:
                    (lat, lon) = fix[4:6]
                    self.set('pos', (lat, lon))

                if fix[1] & location.GPS_DEVICE_TRACK_SET:
                    bearing = fix[9]
                    self.set('bearing', bearing)

                if fix[1] & location.GPS_DEVICE_SPEED_SET:
                    self.set('speed', fix[11]) # km/h
                    metersPerSecSpeed = fix[11] / 3.6 # km/h -> metres per second
                    self.set('metersPerSecSpeed', metersPerSecSpeed) # m/s

                if fix[1] & location.GPS_DEVICE_ALTITUDE_SET:
                    elev = fix[7]
                    self.set('elevation', elev)

                if self.get('n900GPSDebug', False):
                    print("## N900 GPS debugging info ##")
                    print("fix tuple from the Location API:")
                    print(fix)
                    print("position,bearing,speed (in descending order):")
                    print(self.get('pos', None))
                    print(self.get('bearing', None))
                    print(self.get('speed', None))
                    print("#############################")
                    # always set this key to current epoch once the location is updated
                # so that modules can watch it and react
                self.set('locationUpdated', time.time())
                #        print("updating location")
                self.set('needRedraw', True)

            else:
                self.status = "Unknown"
                print("n900 - location: getting fix failed (on a regular update)")
        except Exception:
            import sys

            e = sys.exc_info()[1]
            self.status = "Unknown"
            print("n900 - location:getting fix failed (on a regular update + exception: %s)" % e)


    # ** Internet connectivity **

    def getInternetConnectivityStatus(self):
        """report Internet connectivity status based on data from libconic"""
        return self.connectivityStatus

    def _connectionStateCB(self, connection, event):
        """handle Internet connectivity state changes"""
        #    print("connection_cb(%s, %s)" % (connection, event))
        status = event.get_status()
        error = event.get_error()
        iap_id = event.get_iap_id()
        bearer = event.get_bearer_type()

        if status == conic.STATUS_CONNECTED:
            self.connectivityStatus = True
        elif status == conic.STATUS_DISCONNECTED:
            self.connectivityStatus = False
        elif status == conic.STATUS_DISCONNECTING:
            self.connectivityStatus = False

    def enableInternetConnectivity(self):
        """autoconnect to the Internet using DBUS"""
        subprocess.call(["sh", "modules/device_modules/n900_maemo5_autoconnect_dbus.sh"])

    def getDeviceType(self):
        return DEVICE_SMARTPHONE
