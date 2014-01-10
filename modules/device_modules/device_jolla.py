# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Jolla device module.
# It is a basic modRana module, that has some special features
# and is loaded only on the corresponding device.
#----------------------------------------------------------------------------
# Copyright 2013, Martin Kolman
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
from modules.device_modules.base_device_module import DeviceModule
from core.constants import DEVICE_TYPE_SMARTPHONE

# NOTE: use the device_ prefix when naming the module

def getModule(m, d, i):
    return Jolla(m, d, i)


class Jolla(DeviceModule):
    """A Nokia N9 device module"""

    def __init__(self, m, d, i):
        DeviceModule.__init__(self, m, d, i)

    def getDeviceIDString(self):
        return "jolla"

    def getDeviceName(self):
        return "Jolla"

    def getWinWH(self):
        """Jolla screen resolution"""
        return 960, 540

    def startInFullscreen(self):
        """
        non-fullscreen mode just draw some weird toolbar & status-bar
        on Harmattan
        """
        return True

    def fullscreenOnly(self):
        """
        Applications running on Sailfish@Jolla are fullscreen only.
        """
        return True

    def screenBlankingControlSupported(self):
        """ Screen blanking is not supported yet,
        might need to be handled from the QML context
        """
        return False

    def getSupportedGUIModuleIds(self):
        return ["Qt5"]

    def getLocationType(self):
        """Location data is obtained through the QML context."""
        return "QML"

    def hasButtons(self):
        # TODO: support for volume buttons
        return False


    # ** LOCATION **

    def handlesLocation(self):
        """using Qt Mobility"""
        return False

    # ** PATHS **

    # NOTE: basically the same as on
    # maemo 5 on the N900
    # TODO: check Sailfish paths

    def getTracklogFolderPath(self):
        return "/home/nemo/Public/tracklogs"

    def getMapFolderPath(self):
        return "/home/nemo/Public/maps/"

    def getPOIFolderPath(self):
        return "/home/nemo/Public/maps/"

    def getLogFolderPath(self):
        return "/home/nemo/Public/modrana_debug_logs/"

    def needsQuitButton(self):
        """No need for a separate Quit button thanks
        to the the Sailfish UI
        """
        return False

    def needsBackButton(self):
        return False

    def needsPageBackground(self):
        return False

    def getDeviceType(self):
        return DEVICE_TYPE_SMARTPHONE