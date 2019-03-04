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
from core import constants
from core import paths
import os
import sys

# third party apps for Sailfish OS should use the harbour- prefix
SAILFISH_MODRANA_PROFILE_NAME = "harbour-modrana"

# NOTE: use the device_ prefix when naming the module

def getModule(*args, **kwargs):
    return Jolla(*args, **kwargs)


class Jolla(DeviceModule):
    """A Jolla device module"""

    def __init__(self, *args, **kwargs):
        DeviceModule.__init__(self, *args, **kwargs)

        # override the default profile name to harbour-modrana
        paths.set_profile_name(SAILFISH_MODRANA_PROFILE_NAME)

    @property
    def device_id(self):
        return "jolla"

    @property
    def device_name(self):
        return "Jolla"

    @property
    def window_wh(self):
        """Jolla screen resolution"""
        return 960, 540

    @property
    def start_in_fullscreen(self):
        """
        non-fullscreen mode just draw some weird toolbar & status-bar
        on Harmattan
        """
        return True

    @property
    def fullscreen_only(self):
        """
        Applications running on Sailfish@Jolla are fullscreen only.
        """
        return True

    @property
    def screen_blanking_control_supported(self):
        """ Screen blanking is not supported yet,
        might need to be handled from the QML context
        """
        return False

    @property
    def supported_gui_module_ids(self):
        return ["qt5"]

    @property
    def location_type(self):
        """Location data is obtained through the QML context."""
        return "QML"

    @property
    def has_buttons(self):
        # TODO: support for volume buttons
        return False


    # ** LOCATION **

    @property
    def handles_location(self):
        """through QtPositioning in the GUI module"""
        return True

    # ** PATHS **

    # Sailfish OS uses paths based on the XDG standard,
    # and debug logs go to $HOME/Public/modrana_debug_logs
    # so that they are easily accessible to users

    @property
    def profile_path(self):
        return paths.get_xdg_config_path()

    @property
    def map_folder_path(self):
        return paths.get_xdg_map_folder_path()

    @property
    def routing_data_folder_path(self):
        return paths.get_xdg_routing_data_path()

    @property
    def tracklog_folder_path(self):
        """We have an option for making a symlink to the Documents folder,
        so the XDG path for the actual tracklog storage is fine.
        """
        return paths.get_xdg_tracklog_folder_path()

    @property
    def poi_folder_path(self):
        return paths.get_xdg_poi_folder_path()

    @property
    def log_folder_path(self):
        return os.path.join(paths.get_home_path(), "Documents", "modrana_debug_logs")

    @property
    def cache_folder_path(self):
        return paths.get_xdg_cache_path()

    @property
    def needs_quit_button(self):
        """No need for a separate Quit button thanks
        to the the Sailfish UI
        """
        return False

    @property
    def needs_back_button(self):
        return False

    @property
    def needs_page_background(self):
        return False

    @property
    def device_type(self):
        return DEVICE_TYPE_SMARTPHONE

    @property
    def default_theme(self):
        return "silica", "Silica"

    @property
    def connectivity_status(self):
        # TODO: actual connectivity tracking :)
        return True

    @property
    def offline_routing_providers(self):
        # report OSM Scout Server as always available
        # as we will do checking if it is running before
        # trying to send it a request
        providers = [constants.ROUTING_PROVIDER_OSM_SCOUT]
        # check if we also have Monav Light installed
        if os.path.isfile(self.monav_light_binary_path):
            providers.append(constants.ROUTING_PROVIDER_MONAV_LIGHT)
        return providers

    @property
    def universal_components_backend(self):
        """Path to a Universal Components backend suitable for the given platform.

        We default to the Silica UC backend on Sailfish OS

        :returns: path to suitable UC backend
        :rtype: str
        """
        return "silica"