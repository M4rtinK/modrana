# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Base class for Rana device-specific modules
# * it inherits everything in the base module
# * ads some default functions and handling,
#   that can be overridden for a specific devices
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
from modules.base_module import RanaModule

class deviceModule(RanaModule):
  """A modRana device module"""
  
  def __init__(self, m, d, i):
    RanaModule.__init__(self, m, d, i)

  def getDeviceIDString(self):
    """
    return an unique string identifying the device module
    """
    return None

  def getDeviceName(self):
    """return a "human" name of the device"""
    return "unknown device"

  def getWinWH(self):
    """
    return the preferred application window size in pixels
    """
    # we'll use VGA as a default value
    return 640,480

  def startInFullscreen(self):
    """weather or not to start modRana in fullscreen
    NOTE: this is a default value and can be overridden by a
    user-set options key, etc."""
    return False

  def fullscreenOnly(self):
    """
    some platforms are basically fullscreen-only (Harmattan),
    as applications only switch between fullscreen and a task switcher
    """
    return False

  def screenBlankingControlSupported(self):
    """ there is no universal way to control screen blanking,
    so its off by default
    -> it can be implemented and enabled in the corresponding device module"""
    return False

  def pauseScreenBlanking(self):
    """
    calling this method should pause screen blanking
    * on mobile devices, screen balking needs to be paused every n seconds
    * on desktop, one call might be enough, still, several calls should
    be handled without issues
    * also what about restoring the screen blanking on Desktop
    once modRana exits ?
    """
    pass

  def usesDashboard(self):
    """report if the device minimizes the windows into a dashboard instead of hiding
    them out of view - the user might want that the window redraws on the dashboard or not"""
    return False

  def getSupportedGUIModuleIds(self):
    """
    supported GUI module IDs, ordered by preference from left to right
    (the most-preferred should be on the left)
    """
    return ["GTK", "QML"] # as default try GTK first and then QML

  def handlesLocation(self):
    """report whether the device module handles position updates by itself"""
    return False

  def getLocationType(self):
    """modRana uses gpsd by default"""
    return 'gpsd'

  def simpleMapDragging(self):
    """should we use a fast but less fluent
    or nice and but slow(-er) map dragging method ?
       by default, we use the nice method
    """
    return False

  def lpSkipCount(self):
    """how many clicks to skip after a long press is detected and exercised
    * this might be device specific, as for example SHR on the Neo FreeRunner
    fires two clicks after lp, but Maemo on N900 fires just one
    * default value -> 1
     * should work for Maemo and normal PC Linuxes (Ubuntu)
    """
    return 1

  def textEntryIminent(self):
    """text entry box will be shown after this method finishes
       - on some platforms, there are some steps needed to make sure
       it is actually visible (like disabling fullscreen, etc.)"""
    pass

  def textEntryDone(self):
    """we are done with text entry, so all the needed steps can be reversed again
       (enable fullscreen, etc.)"""
    pass

  def hasNotificationSupport(self):
    """report if the device provides its own notification method"""
    return False

  def notify(self, message, msTimeout=0, icon=""):
    """send a notification"""
    pass

  def hasKeyboard(self):
    """report if the device has a keyboard"""
    return True

  def hasButtons(self):
    """report if the device has some usable buttons other than keyboard"""
    if self.hasVolumeKeys():
      return True
    else:
      return False

  def hasVolumeKeys(self):
    """report if the device has application-usable volume control keys or their
    equivalent - basically just two nearby button that can be used for zooming up/down,
    skipping to next/last and similar actions"""
    return False

  def enableVolumeKeys(self):
    pass

  def enableVolumeKeys(self):
    pass

  def hasKineticScrollingList(self):
    """report if the device provides a native kinetic scrolling list
    widget/dialog"""
    return False

  def startLocation(self):
    """start handling location - check handlesLocation if this is supported"""
    pass

  def stopLocation(self):
    """stop handling location - check handlesLocation if this is supported"""
    pass

  def getTracklogFolderPath(self):
    """return device specific tracklog folder or None if default should be used"""
    return None

  def getMapFolderPath(self):
    """return device specific map folder or None if default should be used"""
    return None

  def getPOIFolderPath(self):
    """return device specific POI folder or None if default should be used"""
    return None

  def getLogFolderPath(self):
    """default path is handled through the options module"""
    None

  def needsQuitButton(self):
    """On some platforms (Android chroot) applications
    need to provide their own shutdown buttons"""
    return False

  def handlesUrlOpening(self):
    """
    report if opening of URI is handled by the device module
    * for example, on the N900 a special DBUS command not available
    elsewhere needs to be used
    """
    return False

  def openUrl(self, url):
    """
    open an URL
    """
    pass

  def getInternetConnectivityStatus(self):
    """report the current status of internet connectivity on the device
    None - status reporting not supported or status unknown
    True - connected to the Internet
    False - disconnected from the Internet
    """

  def enableInternetConnectivity(self):
    """try to make sure that the device connects to the internet"""
    # TODO: respect the modRana internet connectivity state
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
