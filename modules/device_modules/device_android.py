# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# An Android device-specific module.
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

from core import constants

MAIN_MODRANA_DATA_FOLDER = "/sdcard/modrana"  # main modRana data folder on Android
MAP_FOLDER_PATH = os.path.join(MAIN_MODRANA_DATA_FOLDER, "maps")
ROUTING_DATA_FOLDER_PATH = os.path.join(MAIN_MODRANA_DATA_FOLDER, "routing_data")
TRACKLOG_FOLDER_PATH = os.path.join(MAIN_MODRANA_DATA_FOLDER, "tracklogs")
DEBUG_LOG_FOLDER_PATH = os.path.join(MAIN_MODRANA_DATA_FOLDER, "debug_logs")
POI_FOLDER_PATH = os.path.join(MAIN_MODRANA_DATA_FOLDER, "poi")

def getModule(*args, **kwargs):
    return Android(*args, **kwargs)


class Android(DeviceModule):
    """A modRana device-specific module for Android"""

    def __init__(self, *args, **kwargs):
        DeviceModule.__init__(self, *args, **kwargs)
        self.tempUnfullscreen = False

    @property
    def device_id(self):
        return "android"

    @property
    def device_name(self):
        return "Android device"

    @property
    def window_wh(self):
        #return 480, 800
        return None

    @property
    def start_in_fullscreen(self):
        return True

    @property
    def fullscreen_only(self):
        return True

    @property
    def supported_gui_module_ids(self):
        return ["qt5"]

    @property
    def location_type(self):
        # TODO: get to location data on Android
        return None

    @property
    def screen_blanking_control_supported(self):
        """
        Screen blanking support is handled through Qt Mobility
        """
        return False

    @property
    def needs_quit_button(self):
        """due to no window decoration, own quit button
        might be needed so that users can quit modRana when
        they want to"""
        return False

    @property
    def map_folder_path(self):
        return MAP_FOLDER_PATH

    @property
    def routing_data_folder_path(self):
        return ROUTING_DATA_FOLDER_PATH

    @property
    def tracklog_folder_path(self):
        return TRACKLOG_FOLDER_PATH

    @property
    def log_folder_path(self):
        return DEBUG_LOG_FOLDER_PATH

    @property
    def poi_folder_path(self):
        return POI_FOLDER_PATH

    @property
    def device_type(self):
        # TODO: device type detection
        return None

    @property
    def defaultTileStorageType(self):
        """Use Sqlite tile storage by default on Android to both
        make sure the tiles would not be indexed into the gallery and also as
        sharing the tile image files with another mapping application is not
        very probably on Android. And who knows how would the usual Android
        filesystems handle such a big amount of very small files.
        """
        return constants.TILE_STORAGE_SQLITE
