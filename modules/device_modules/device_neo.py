#!/usr/bin/python
#----------------------------------------------------------------------------
# A Neo FreeRunner modRana device-specific module.
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
  return(device_neo(m,d))

class device_neo(deviceModule):
  """A Neo FreeRunner modRana device-specific module"""
  
  def __init__(self, m, d):
    deviceModule.__init__(self, m, d)
    self.tempUnfullscreen = False

  def getDeviceName(self):
    return "OpenMoko Neo FreeRunner"

  def textEntryIminent(self):
    """in SHR on Neo, we need to temporarry disable fullscreen
    (if we are in fullscreen),
    or else the text entry box won't show up"""
    display = self.m.get('display', None)
    if display:
      if display.getFullscreenEnabled():
        display.fullscreenToggle()
        self.tempUnfullscreen = True

  def textEntryDone(self):
    """restore fullscreen if needed"""
    if self.tempUnfullscreen:
      display = self.m.get('display', None)
      if display:
        if not display.getFullscreenEnabled():
          display.fullscreenToggle()
          self.tempUnfullscreen = False

    

if(__name__ == "__main__"):
  a = device_example({}, {})
  a.update()
  a.update()
  a.update()
