# -*- coding: utf-8 -*-
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
from base_device_module import DeviceModule
import bbpy

def getModule(m,d,i):
  return BB10(m,d,i)

class BB10(DeviceModule):
  """A modRana device-specific module for Android chroot"""
  
  def __init__(self, m, d, i):
    DeviceModule.__init__(self, m, d, i)
    self.tempUnfullscreen = False

  def getDeviceIDString(self):
    return "bb10"

  def getDeviceName(self):
    return "BlackBerry 10 device"

  def getWinWH(self):
    return 720,1280

  def startInFullscreen(self):
    return True

  def getSupportedGUIModuleIds(self):
    return ["QML:harmattan", "QML:indep"]

  def getLocationType(self):
    return None

  def screenBlankingControlSupported(self):
    """
    Screen blanking support is handled through Qt Mobility
    """
    return False

  def pauseScreenBlanking(self):
    """
    inhibit screen blanking
    """
    from QtMobility.SystemInfo import QSystemScreenSaver

    if self.qScreenSaver:
      QSystemScreenSaver.setScreenSaverInhibit(self.qScreenSaver)
    else:
      self.qScreenSaver = QSystemScreenSaver()

  def needsQuitButton(self):
    return False

  def usesDashboard(self):
    return False

  def getStartDragDistance(self):
    """BB10 devices have a high DPI screen and need a higher value than
    the default in Qt."""
    return 32