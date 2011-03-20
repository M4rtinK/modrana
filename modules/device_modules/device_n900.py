#!/usr/bin/python
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
from base_device_module import deviceModule
import dbus.glib
import hildon
import gtk
"""
why dbus.glib ?
if you import only "dbus", it can't find its mainloop for callbacks

"""

def getModule(m,d,i):
  return(device_n900(m,d,i))

class device_n900(deviceModule):
  """A N900 modRana device-specific module"""
  
  def __init__(self, m, d, i):
    deviceModule.__init__(self, m, d, i)
    self.rotationObject = None
    # start the N900 specific automatic GUI rotation support
    self.done = False

    #osso app name
    self.ossoAppName = 'modrana'

    # screen blanking related
    self.bus = dbus.SystemBus()
    self.mceRequest = self.bus.get_object('com.nokia.mce','/com/nokia/mce/request')
    self.mceSignal = self.bus.get_object('com.nokia.mce','/com/nokia/mce/signal')
    self.mceSignalInterface = dbus.Interface(self.mceSignal,'com.nokia.mce.signal')
    self.mceSignalInterface.connect_to_signal("display_status_ind", self.screenStateChangedCallback)
    print "N900: dbus initialized"

    # app menu and buttons
    self.centeringToggleButton = None
    self.rotationToggleButton = None
    self.soundToggleButton = None
    self._addHildonAppMenu()

    # enable volume keys usage
    if self.get('useVolumeKeys', True):
      self._updateVolumeKeys()


    print "N900: application menu added"

    print "N900 device specific module initialized"

  def firstTime(self):
    # load the rotation object
    rotationObject = self.startAutorotation()
    if rotationObject != False:
      print "N900: rotation object loaded"
      self.rotationObject = rotationObject
    else:
      print "N900: loading rotation object failed"

    # setup window state callbacks
    self.modrana.topWindow.connect('notify::is-active', self.windowIsActiveChangedCallback)
    """
    on the Maemo 5@N900, is-active == True signalizes that the modRana window is
    the current active window (there is always only one active window)
    is-active == False signalizes that the window is either minimzed on the
    dashboard or the screen is blanked
    """
  def update(self):
    """initialize the automatic rotation"""
    if not self.done:
      if self.topWindow: #TODO: do this more efficiently
        self.startAutorotation()
        self.done = True

  def handleMessage(self, message, type, args):
    if message == 'modeChanged':
      rotationMode = self.get('rotationMode', None)
      if rotationMode:
        self.setRotationMode(rotationMode)
        print "rotation mode changed"
    elif message == 'updateAppMenu':
      self._updateAppMenu()
      
  def getDeviceName(self):
    return "Nokia N900"

  def locationType(self):
    """modRana uses liblocation on N900"""
    return "liblocation"

  def startAutorotation(self):
    """start the GUI autorotation feature"""
    try:
      from n900_maemo5_portrait import FremantleRotation
      rotationMode = self.get('rotationMode', "auto") # get last used mode
      lastModeNumber = self.getRotationModeNumber(rotationMode) # get last used mode number
      rotationObject = FremantleRotation(self.ossoAppName, main_window=self.modrana.topWindow, mode=lastModeNumber)
      self.rotationObject = rotationObject
      print "N900 rotation object initialized"
    except Exception, e:
      print e
      print "intializing N900 rotation object failed"

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

  def getLogFolderPath(self):
    return "/home/user/MyDocs/modrana_debug_log/" #N900 specific log folder

  def getPOIFolderPath(self):
    """get the N900 specific POI folder path"""
    return "/home/user/MyDocs/.maps/"

  def screenBlankingControlSupported(self):
    """it is possible to controll screen balnking on the N900"""
    return True

  def usesDashboard(self):
    """the N900 uses a dashboard type task switcher"""
    return True

  def pauseScreenBlanking(self):
    self.mceRequest.req_display_blanking_pause()

  def unlockScreen(self):
    self.mceRequest.req_tklock_mode_change('unlocked')

  def windowIsActiveChangedCallback(self, window, event):
    """this is called when the window gets or looses focus
    it basically menas:
    - has focus - it is the active window and the user is working wit it
    - no focus -> the window is switched to dashboard or the uanother widnow is active or
    the screen is balnked"""
    redrawOnDashboard = self.get('redrawOnDashboard', False)
    """
    NOTE: this updates the snapshot in task switcher,
    but also UPDATES WHEN MINIMISED AND NOT VISIBLE
    so use with caution
    balnking overrides this so when the screen is balnked it does not redraw
    TODO: see if hildon signalizes that a the task switcher is visible or not
    """

    if not redrawOnDashboard: # we dont redraw on dashboard by default
      display = self.m.get('display', None)
      if display:
        if window.is_active():
          display.enableRedraw(reason="N900 window is active")
        else:
          # check if text entry is in progress
          textEntry = self.m.get('textEntry', None)
          if textEntry:
            if textEntry.isEntryBoxvisible():
              # we redraw modRana behind text entry box
              return
          display.disableRedraw(reason="N900 window is not active")

  def screenStateChangedCallback(self, state):
    """this is called when the display is blanked or unblanked"""
    display = self.m.get('display', None)
    if display:
      if state == "on" or state == "dimm":
        display.enableRedraw(reason="N900 display on or dimmed")
      elif state== "off":
        display.disableRedraw(reason="N900 display blanked")

  def hasNativeNotificationSupport(self):
    return True

  def notify(self, message, msTimeout=0, icon="icon_text"):
    """the third barameter has to be a non zerolength string or
    else the banner is not created"""
    #TODO: find what strings to submit to actually get an icon displayed

    if len(icon) == 0:
      icon = "spam" # as mentioned above, the string has to be longer tahn zero

    banner = hildon.hildon_banner_show_information_with_markup(self.modrana.topWindow, icon, message)
    if msTimeout:
      banner.set_timeout(msTimeout)

  def hasVolumeKeys(self):
    return True

  def enableVolumeKeys(self):
    if self.modrana.topWindow.flags() & gtk.REALIZED:
      self.enable_volume_cb()
    else:
      self.modrana.topWindow.connect("realize", self.enable_volume_cb)

  def disableVolumeKeys(self):
    self.modrana.topWindow.property_change(gtk.gdk.atom_intern("_HILDON_ZOOM_KEY_ATOM"), gtk.gdk.atom_intern("INTEGER"), 32, gtk.gdk.PROP_MODE_REPLACE, [0]);

  def enable_volume_cb(self):
    self.modrana.topWindow.window.property_change(gtk.gdk.atom_intern("_HILDON_ZOOM_KEY_ATOM"), gtk.gdk.atom_intern("INTEGER"), 32, gtk.gdk.PROP_MODE_REPLACE, [1]);

  def _updateVolumeKeys(self):
    """check if volume keys should be used or not"""
    if self.get('useVolumeKeys', True):
      self.enableVolumeKeys()
    else:
      self.disableVolumeKeys()


  def _addHildonAppMenu(self):
    menu = hildon.AppMenu()
    self.centeringToggleButton = gtk.ToggleButton(label="Centering")
    self.centeringToggleButton.connect('toggled',self._toggle, 'centred')
#    openFolderButton.connect('clicked',self.startFolderChooser)
    self.rotationToggleButton = gtk.ToggleButton(label="Map rotation")
    self.rotationToggleButton.connect('toggled',self._toggle,'rotateMap')
    self.soundToggleButton = gtk.ToggleButton(label="Sound")
    self.soundToggleButton.connect('toggled',self._toggle,'soundEnabled')

    mapButton = gtk.Button("Map screen")
    mapButton.connect('clicked',self._switchToMenu, None)
    optionsButton = gtk.Button("Options")
    optionsButton.connect('clicked',self._switchToMenu,'options')
    searchButton = gtk.Button("Search")
    searchButton.connect('clicked',self._switchToMenu,'search')
    routeButton = gtk.Button("Route")
    routeButton.connect('clicked',self._switchToMenu,'route')

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
    self.modrana.topWindow.set_app_menu(menu)

  def _toggle(self,toggleButton, key):
    print "N900: key %s toggled" % key
    self.set(key, toggleButton.get_active())

  def _switchToMenu(self,toggleButton, menu):
    """callback for the appMenu buttons, switch to a specified menu"""
    self.set('menu', menu)
    self.set('needRedraw', True)

  def _updateAppMenu(self):
    if self.centeringToggleButton:
      self.centeringToggleButton.set_active(self.get("centred",True))
    if self.rotationToggleButton:
      self.rotationToggleButton.set_active(self.get("rotateMap",True))
    if self.soundToggleButton:
      self.soundToggleButton.set_active(self.get("soundEnabled",True))

if(__name__ == "__main__"):
  a = n900({}, {})
  a.update()
  a.update()
  a.update()
