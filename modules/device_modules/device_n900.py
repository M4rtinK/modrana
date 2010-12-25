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
import time
import dbus.glib
"""
why dbus.glib ?
if you import only "dbus", it can't find its mainloop for callbacks

"""
#from dbus.mainloop.glib import DBusGMainLoop


def getModule(m,d):
  return(device_n900(m,d))

class device_n900(deviceModule):
  """A N900 modRana device-specific module"""
  
  def __init__(self, m, d):
    deviceModule.__init__(self, m, d)
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

  def pauseScreenBlanking(self):
    self.mceRequest.req_display_blanking_pause()

  def unlockScreen(self):
    self.mceRequest.req_tklock_mode_change('unlocked')

  def windowIsActiveChangedCallback(self, window, event):
    display = self.m.get('display', None)
    if display:
      if window.is_active():
        display.enableRedraw(reason="N900 window is active")
      else:
        display.disableRedraw(reason="N900 window is not active")

  def screenStateChangedCallback(self, state):
    display = self.m.get('display', None)
    if display:
      if state == "on" or state == "dimm":
        display.enableRedraw(reason="N900 display on or dimmed")
      elif state== "off":
        display.disableRedraw(reason="N900 display blanked")


if(__name__ == "__main__"):
  a = n900({}, {})
  a.update()
  a.update()
  a.update()
