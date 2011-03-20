#!/usr/bin/python
#----------------------------------------------------------------------------
# Base class for Rana device-specific modules
# * it inherits everything in the base module
# * ads some default functions and handling,
#   that can be overriden for specific devices
#----------------------------------------------------------------------------
# Copyright 2007, Oliver White
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
from base_module import ranaModule

class deviceModule(ranaModule):
  """A sample pyroute module"""
  
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    
  def getDeviceName(self):
    return "unknown device"

  def getLogFolderPath(self):
    return "data/log/" # default log folder

  def getPOIFolderPath(self):
    return "data/poi/" # default log folder

  def screenBlankingControlSupported(self):
    """ there is no universal way to control screen blanking,
    so its off by default
    -> it can be implemented and enabled in the coresponding device module"""
    return False

  def usesDashboard(self):
    """report if the device minimizes the windows into a dasboard instead of hiding
    them out of view - the user might want that the window redraws on the dashboard or not"""
    return False

  def locationType(self):
    """modRana uses gpsd by default"""
    return 'gpsd'

  def simpleMapDragging(self):
    """should we use a fast but less fluent
    or nice and but slow(-er) map dragging method ?
       by default, we use the nice method
    """
    return False

  def lpSkipCount(self):
    """how many clicks to skip after a long press is detected and execised
    * this might be device specific, as for example SHR on the Neo FreeRunner
    fires two clicks after lp, but Maemo on N900 fires just one
    * default value -> 1
     * should work for Maemo and normal PC Linuxes (Ubuntu)
    """
    return 1

  def textEntryIminent(self):
    """text entry box will be shown after this metod finishes
       - on some platforms, there are some steps needed to make sure
       it is actually visible (like disabling fullscreen, etc.)"""
    pass

  def textEntryDone(self):
    """we are done with text entry, so all the needed steps can be reversed again
       (enbale fullscreen, etc.)"""
    pass

  def hasNativeNotificationSupport(self):
    """report if the device provides its own notification method"""
    return False

  def notify(self, message, msTimeout=0, icon=""):
    """send a notification"""
    pass

  def hasVolumeKeys(self):
    """report if the device has application-usable volume control keys or their
    equivalent - basically just two nearby button that can be used for zooming up/down,
    skipping to next/last and similar actions"""
    return False

  def enableVolumeKeys(self):
    pass

  def enableVolumeKeys(self):
    pass

  
#  def getAutorotationSupported(self):
#    return False
#
#  def getAutorotationenabled(self):
#    pass
#
#  def getAutorotationState(self):
#    pass
#
#  def enableAutorotation(self):
#    pass
#
#  def disableAutorotation(self):
#    pass



if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
