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


def getModule(m, d, i):
    return AndroidChroot(m, d, i)


class AndroidChroot(DeviceModule):
    """A modRana device-specific module for Android chroot"""

    def __init__(self, m, d, i):
        DeviceModule.__init__(self, m, d, i)
        self.tempUnfullscreen = False

    def getDeviceIDString(self):
        return "android_chroot"

    def getDeviceName(self):
        return "Android chroot"

    def getWinWH(self):
        return 480, 600

    def startInFullscreen(self):
        return False

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
        """In SHR on Neo, we need to temporary disable fullscreen
        (if we are in fullscreen),
        or else the text entry box won't show up"""
        display = self.m.get('display', None)
        if display:
            if display.getFullscreenEnabled():
                display.fullscreenToggle()
                self.tempUnfullscreen = True

    def textEntryDone(self):
        """Restore fullscreen if needed"""
        if self.tempUnfullscreen:
            display = self.m.get('display', None)
            if display:
                if not display.getFullscreenEnabled():
                    display.fullscreenToggle()
                    self.tempUnfullscreen = False

    def needsQuitButton(self):
        """Due to missing window decoration, own quit button
        might be needed"""
        return True