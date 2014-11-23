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
from modules.device_modules.base_device_module import DeviceModule

import os

MAIN_MODRANA_DATA_FOLDER = "/sdcard/modrana"  # main modRana data folder on Android
MAP_FOLDER_PATH = os.path.join(MAIN_MODRANA_DATA_FOLDER, "maps")
ROUTING_DATA_FOLDER_PATH = os.path.join(MAIN_MODRANA_DATA_FOLDER, "routing_data")
TRACKLOG_FOLDER_PATH = os.path.join(MAIN_MODRANA_DATA_FOLDER, "tracklogs")
DEBUG_LOG_FOLDER_PATH = os.path.join(MAIN_MODRANA_DATA_FOLDER, "debug_logs")
POI_FOLDER_PATH = os.path.join(MAIN_MODRANA_DATA_FOLDER, "poi")

def getModule(m, d, i):
    return Android(m, d, i)


class Android(DeviceModule):
    """A modRana device-specific module for Android"""

    def __init__(self, m, d, i):
        DeviceModule.__init__(self, m, d, i)
        self.tempUnfullscreen = False

    def getDeviceIDString(self):
        return "android"

    def getDeviceName(self):
        return "Android device"

    def getWinWH(self):
        #return 480, 800
        return None

    def startInFullscreen(self):
        return True

    def fullscreenOnly(self):
        return True

    def getSupportedGUIModuleIds(self):
        return ["qt5"]

    def getLocationType(self):
        # TODO: get to location data on Android
        return None

    def screenBlankingControlSupported(self):
        """
        Screen blanking support is handled through Qt Mobility
        """
        return False

    def needsQuitButton(self):
        """due to no window decoration, own quit button
        might be needed so that users can quit modRana when
        they want to"""
        return False

    def getMapFolderPath(self):
        return MAP_FOLDER_PATH

    def getRoutingDataFolderPath(self):
        return ROUTING_DATA_FOLDER_PATH

    def getTracklogFolderPath(self):
        return TRACKLOG_FOLDER_PATH

    def getLogFolderPath(self):
        return DEBUG_LOG_FOLDER_PATH
    
    def getPOIFolderPath(self):
        return POI_FOLDER_PATH

    def getDeviceType(self):
        # TODO: device type detection
        return None
