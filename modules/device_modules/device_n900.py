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
import osso

def getModule(m,d):
  return(device_n900(m,d))

class device_n900(deviceModule):
  """A N900 modRana device-specific module"""
  
  def __init__(self, m, d):
    deviceModule.__init__(self, m, d)
    self.rotationObject = None
    # start the N900 specific automatic GUI rotation support
    self.done = False
    
    # screen blanking related
    self.ossoContext = osso.Context("osso_test_device_on", "0.0.1", False)
    self.ossoDevice = osso.DeviceState(self.ossoContext)
    """according to documentation on:
    (http://wiki.maemo.org/PyMaemo/Python-osso_examples#Device_State),
    every display_blanking_pause() call pauses screenblank for 60 secconds,
    to make sure, we request every 30 secconds"""
    self.screenBlankPauseInterval = 30
    self.lastScreenblankPauseRequest = time.time()

    print "N900 device specific module initialized"
    
  def firstTime(self):
    rotationObject = self.startAutorotation()
    if rotationObject != False:
      print "N900 rotation object loaded"
      self.rotationObject = rotationObject
    else:
      print "N900 loading rotation object failed"

  def update(self):
    """initialize the automatic rotation"""
    if not self.done:
      if self.topWindow: #TODO: do this more efficiently
        self.startAutorotation()
        self.done = True

    currentTime = time.time()
    if (currentTime - self.lastScreenblankPauseRequest)>self.screenBlankPauseInterval:
      # reaguest to pause screen blanking for 60 secconds every 30 secconds
      self.pauseScreenBlanking()
      self.lastScreenblankPauseRequest = currentTime

  def handleMessage(self, message, type, args):
    if message == 'modeChanged':
      rotationMode = self.get('rotationMode', None)
      if rotationMode:
        self.setRotationMode(rotationMode)
        print "rotation mode changed"

  def getDeviceName(self):
    return "Nokia N900"

  def startAutorotation(self):
    """start the GUI autorotation feature"""
    try:
      from n900_maemo5_portrait import FremantleRotation
      app_name = 'modrana' # the name this app
      rotationMode = self.get('rotationMode', "auto") # get last used mode
      lastModeNumber = self.getRotationModeNumber(rotationMode) # get last used mode number
      rotationObject = FremantleRotation(app_name, main_window=self.topWindow, mode=lastModeNumber)
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

  def screenBlankingControllSupported(self):
    """it is possible to controll screen balnking on the N900"""
    return True

  def pauseScreenBlanking(self):
    self.ossoDevice.display_blanking_pause()

if(__name__ == "__main__"):
  a = n900({}, {})
  a.update()
  a.update()
  a.update()
