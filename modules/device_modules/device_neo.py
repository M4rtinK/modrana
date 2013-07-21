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
from base_device_module import DeviceModule, DEVICE_SMARTPHONE
import subprocess


def getModule(m, d, i):
    return DeviceNeo(m, d, i)


class DeviceNeo(DeviceModule):
    """A Neo FreeRunner modRana device-specific module"""

    def __init__(self, m, d, i):
        DeviceModule.__init__(self, m, d, i)
        self.tempUnfullscreen = False
        # connect to the location start & stop signals,
        # so that the FreeRunners GPS can be started/stopped
        l = self.m.get('location', None)
        if l is not None:
            l.startSignal.connect(self._startLocationCB)
            l.stopSignal.connect(self._stopLocationCB)


    def _startLocationCB(self):
        """start the GPS hardware"""
        print("HANDLE GPS STARTUP")

    def _stopLocationCB(self):
        """stop the GPS hardware"""
        print("HANDLE GPS SHUTDOWN")


    def getDeviceIDString(self):
        return "neo"

    def getDeviceName(self):
        return "OpenMoko Neo FreeRunner"

    def getWinWH(self):
        return 480, 600

    def startInFullscreen(self):
        return True

    def simpleMapDragging(self):
        return True

    def getSupportedGUIModuleIds(self):
        return ["GTK"]

    def lpSkipCount(self):
        """SHR on Neo fires two clicks after a long press, so we need to skip
        both of them, to avoid clicking some new button that
        shows up after the screen redraws"""
        return 2

    def textEntryIminent(self):
        """in SHR on Neo, we need to temporarily disable fullscreen
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

    def getLocationType(self):
        """we use GPSD for location on the Neo FreeRunner
        as it should be available on both the DH & QtMoko"""
        return "gpsd"

    def getDeviceType(self):
        return DEVICE_SMARTPHONE
