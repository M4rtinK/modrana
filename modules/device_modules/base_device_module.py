from __future__ import with_statement  # for Python 2.5
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
from core import constants
from modules.base_module import RanaModule
from core.signal import Signal

class DeviceModule(RanaModule):
    """A modRana device module"""

    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)
        self.internetConnectivityChanged = Signal()

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
        return 640, 480

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
        """supported GUI module IDs, ordered by preference from left to right

        THE ":" NOTATION
        single GUI modules might support different subsets, the usability of
        these subsets can vary based on the current platform
        -> this functions enabled device modules to report which GUI subsets
        are most suitable for the given platform
        -> the string starts with the module id prefix, is separated by : and
        continues with the subset id
        EXAMPLE: ["QML:harmattan","QML:indep","GTK"]
        -> QML GUI with Harmattan Qt Components is preferred,
        QML GUI with platform independent Qt Components is less preferred
        and the GTK GUI is set as a fallback if everything else fails
        CURRENT USAGE
        there are different incompatible native Qt Component sets
        on various platforms (Harmattan QTC, Plasma Active QTC, Jolla QTC,...)
        the QML GUI aims to support most of these components sets to provide
        native look & feel and the subset id is used by the device module
        to signal the GUI module which QTC component to use
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

    def hasKineticScrollingList(self):
        """report if the device provides a native kinetic scrolling list
        widget/dialog"""
        return False

    def startLocation(self, startMainLoop=False):
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

    def getRoutingDataFolderPath(self):
        """return device specific map folder or None if default should be used"""
        return None

    def getPOIFolderPath(self):
        """return device specific POI folder or None if default should be used"""
        return None

    def getLogFolderPath(self):
        """default path is handled through the options module"""
        return None

    def needsQuitButton(self):
        """On some platforms (Android chroot) applications
        need to provide their own shutdown buttons"""
        return False

    def needsBackButton(self):
        """Some platforms (Jolla) don't need a in-UI back button"""
        return True

    def needsPageBackground(self):
        """Some platforms (Jolla) don't need a page background"""
        return True

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

    @property
    def connectivityStatus(self):
        """report the current status of internet connectivity on the device
        None - status reporting not supported or status unknown
        True - connected to the Internet
        False - disconnected from the Internet
        """
        connected = constants.OFFLINE
        # open the /proc/net/route file
        with open('/proc/net/route', 'rc') as f:
            for line in f:
                # the line is delimited by tabulators
                lineSplit = line.split('\t')
                # check if the length is valid
                if len(lineSplit) >= 11:
                    if lineSplit[1] == '00000000' and lineSplit[7] == '00000000':
                        # if destination and mask are 00000000,
                        # it is probably an Internet connection
                        connected = constants.ONLINE
                        break
        return connected



    def enableInternetConnectivity(self):
        """try to make sure that the device connects to the internet"""
        # TODO: respect the modRana internet connectivity state
        pass

    def getStartDragDistance(self):
        """Distance in pixel for discerning drag from a click
        A correct start drag distance is important on high DPI screens
        as the default values don't work correctly on them.
        """
        return None

    def getDeviceType(self):
        """Returns type of the current device

        The device can currently be either a PC
        (desktop or laptop/notebook),
        smartphone or a tablet.
        This is currently used mainly for rough
        DPI estimation.
        Example:
        * high resolution & PC -> low DPI
        * high resolution & smartphone -> high DPI
        * high resolution & smartphone -> low DPI

        This could also be used in the future to
        use different PC/smartphone/tablet GUI styles.

        By default, the device type is unknown.
        """
        return None

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
