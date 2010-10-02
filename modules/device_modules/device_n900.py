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

def getModule(m,d):
  return(device_n900(m,d))

class device_n900(deviceModule):
  """A N900 modRana device-specific module"""
  
  def __init__(self, m, d):
    deviceModule.__init__(self, m, d)
    self.rotationObject = None
    # start the N900 specific automatic GUI rotation support
    self.done = False
    print "N900 device specific module initialized"
    
  def firstTime(self):
    pass
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
    return "/home/user/MyDocs/" #N900 specific log folder

    



  

if(__name__ == "__main__"):
  a = n900({}, {})
  a.update()
  a.update()
  a.update()
