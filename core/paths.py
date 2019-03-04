# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# ModRana paths handling
#----------------------------------------------------------------------------
# Copyright 2012, Martin Kolman
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
from __future__ import with_statement  # for Python 2.5
import os
from core import utils

import logging
log = logging.getLogger("core.paths")

# paths
THEMES_FOLDER_PATH = "themes"
# folder names
DEFAULT_PROFILE_FOLDER_NAME = "modrana"
MONAV_DATA_FOLDER_NAME = "monav_data"
CACHE_FOLDER_NAME = "cache"
TRACKLOG_FOLDER_NAME = "tracklogs"
MAPS_FOLDER_NAME = "maps"
POI_FOLDER_NAME = "poi"
ROUTING_DATA_FOLDER_NAME = "routing_data"
DEBUG_LOGS_FOLDER_NAME = "debug_logs"
OVERLAY_GROUPS_FOLDER_NAME = "overlay_groups"
# file names
OPTIONS_FILENAME = "options.bin"
POI_DB_FILENAME = "modrana_poi.db"
VERSION_INFO_FILENAME = "version.txt"
VERSION_STRING = None

_PROFILE_FOLDER_NAME = DEFAULT_PROFILE_FOLDER_NAME

def load_version_string():
    """ Load version string from file"""
    # try to read the version file
    versionString = get_version_string()
    if versionString is not None:
        global VERSION_STRING
        VERSION_STRING = versionString


def get_version_string():
    """ Get version string from the default version file

    :returns: version string or None if unknown
    :rtype: str or None
    """

    if os.path.exists(VERSION_INFO_FILENAME):
        try:
            with open(VERSION_INFO_FILENAME, 'r') as f:
                versionString = f.readline()
            # make sure it is string (or the conversion throws an exception)
            # and that it does not have any dangling newlines
            versionString = str(versionString).rstrip()
            return versionString
        except Exception:
            log.exception("loading version info failed")
            return None
    else:
        log.warning("local version file is missing")
        return None

## XDG path getters ##

def get_home_path():
    """Get the path specified by the $HOME variable

    :returns: path to current users home directory
    :rtype: str
    """

    # if $HOME is not set, return ~ in a desperate attempt
    # to save the situation
    return os.environ.get("HOME", os.path.expanduser("~"))

def get_profile_name():
    """Get name of the modRana profile folder

    :returns: modRana profile folder name
    :rtype: str
    """
    return _PROFILE_FOLDER_NAME

def set_profile_name(name):
    """Set the name of the modRana profile folder

    :param str name: new profile name
    """
    global _PROFILE_FOLDER_NAME
    _PROFILE_FOLDER_NAME = name

def get_xdg_config_path():
    """Check the contents of the $XDG_CONFIG_HOME/modrana variable and
    default to $HOME/.config/modrana if not set.

    :returns: path to the XDG config folder
    :rtype: str
    """
    return os.path.join(
        os.environ.get("$XDG_CONFIG_HOME", os.path.join(get_home_path(), ".config")),
        get_profile_name()
    )

def get_xdg_data_path():
    """Check the contents of the $XDG_DATA_HOME variable and
    default to "$HOME/.cache" if not set.

    :returns: path to the XDG config folder
    :rtype: str
    """
    return os.path.join(
        os.environ.get("$XDG_DATA_HOME", os.path.join(get_home_path(), ".local/share")),
        get_profile_name()
    )

def get_xdg_cache_path():
    """Check the contents of the $XDG_CONFIG_HOME variable and
    default to "$HOME/.local/share" if not set.

    :returns: path to the XDG config folder
    :rtype: str
    """
    return os.path.join(
        os.environ.get("$XDG_CACHE_HOME", os.path.join(get_home_path(), ".cache")),
        get_profile_name()
    )

def get_xdg_profile_path():
    """Return XDG-compatible profile folder path

    basically the same as get_xdg_config_path()
    """
    return get_xdg_config_path()

def get_xdg_map_folder_path():
    """Return XDG-compatible map folder path"""
    return os.path.join(get_xdg_data_path(), MAPS_FOLDER_NAME)

def get_xdg_tracklog_folder_path():
    """Return XDG-compatible tracklog folder path"""
    return os.path.join(get_xdg_data_path(), TRACKLOG_FOLDER_NAME)

def get_xdg_poi_folder_path():
    """Return XDG-compatible POI folder path"""
    return os.path.join(get_xdg_data_path(), POI_FOLDER_NAME)

def get_xdg_routing_data_path():
    """Return XDG-compatible routing data folder path"""
    return os.path.join(get_xdg_data_path(), ROUTING_DATA_FOLDER_NAME)

def get_xdg_debug_log_path():
    """Return XDG-compatible debug log folder path"""
    return os.path.join(get_xdg_data_path(), DEBUG_LOGS_FOLDER_NAME)

class Paths(object):
    """
    Handle paths to various folders:
    * main profile folder
    * tracklogs folder
    * map tiles folder
    * generic cache
    * log folder
    * POI folder
    Not only provide the paths but also assure
    that folders are created automatically if they
    don't exist yet.
    """

    def __init__(self, modrana):
        self.modrana = modrana

        # get profile folder path
        # -> first check for device module override
        if self.modrana.dmod.profile_path:
            self._profileFolderPath = self.modrana.dmod.profile_path
        else:
            self._profileFolderPath = self.modrana.get_profile_path()
        # check the profile path and create the folders if necessary
        utils.create_folder_path(self._profileFolderPath)

        # load version string
        self.versionString = None


    ## Important modRana folders ##

    @property
    def profile_path(self):
        """return path to the profile folder"""
        # check if the path exists and create it if not
        utils.create_folder_path(self._profileFolderPath)
        return self._profileFolderPath

    @property
    def options_file_path(self):
        """return path to the options store filename"""
        return os.path.join(self.profile_path, OPTIONS_FILENAME)

    @property
    def cache_folder_path(self):
        """return path to a folder used for various cache data"""
        path = self.modrana.dmod.cache_folder_path
        # if no path was provided by device module, use default,
        # which is a cache folder in the profile folder
        if path is None:
            path = os.path.join(self.profile_path, CACHE_FOLDER_NAME)

        return self._assurePath(path)

    @property
    def tracklog_folder_path(self):
        """return path to a folder for storing tracklogs"""
        path = None
        # first check if the user overrode the tracklog folder path
        config = self.modrana.configs.user_config
        if config:
            path = config.get("tracklog_folder", None)
        if path is None:
        # try to get the path from device module
            if self.modrana.dmod:
                path = self.modrana.dmod.tracklog_folder_path

        if path is None: # this means there is no config or device path
            # use default path & assure it exists
            return self._assurePathFolder(self.profile_path, TRACKLOG_FOLDER_NAME)
        else:
            return self._assurePath(path)

    @property
    def map_folder_path(self):
        """return a path to folder for map data storage"""
        path = None
        # first check if the user overrode the map folder path
        config = self.modrana.configs.user_config
        if config:
            path = config.get("map_folder", None)
        if path is None:
        # try to get the path from device module
            if self.modrana.dmod:
                path = self.modrana.dmod.map_folder_path

        if path is None: # this means there is no config or device path
            # use default path & assure it exists
            return self._assurePathFolder(self.profile_path, MAPS_FOLDER_NAME)
        else:
            return self._assurePath(path)

    @property
    def poi_folder_path(self):
        """return path to the POI folder"""
        if self.modrana.dmod:
            path = self.modrana.dmod.poi_folder_path
            if path is not None: # None means there is no device dependent path
                return self._assurePath(path)
            else:
                return self._assurePathFolder(self.profile_path, POI_FOLDER_NAME)
        else:
            return self._assurePathFolder(self.profile_path, POI_FOLDER_NAME)

    @property
    def poi_database_path(self):
        """return path to the POI database file"""
        POIDBFilename = self.modrana.get('POIDBFilename', POI_DB_FILENAME)
        POIFolderPath = self.poi_folder_path
        return os.path.join(POIFolderPath, POIDBFilename)

    @property
    def log_folder_path(self):
        """return path to the POI folder"""
        if self.modrana.dmod:
            path = self.modrana.dmod.log_folder_path
            if path is not None: # None means there is no device dependent path
                return self._assurePath(path)
            else:
                return self._assurePathFolder(self.profile_path, DEBUG_LOGS_FOLDER_NAME)
        else:
            return self._assurePathFolder(self.profile_path, DEBUG_LOGS_FOLDER_NAME)

    @property
    def themes_folder_path(self):
        """Return path to the themes folder"""
        return THEMES_FOLDER_PATH


    @property
    def routing_data_folder_path(self):
        """Return path to the routing data folder"""
        path = self.modrana.dmod.routing_data_folder_path
        if path is not None:
            return self._assurePath(path)
        else:
            return self._assurePath(os.path.join(self.profile_path, ROUTING_DATA_FOLDER_NAME))

    @property
    def overlay_groups_folder_path(self):
        """Return path to the folder where overlay groups are stored as JSON files"""
        return self._assurePathFolder(self.profile_path, OVERLAY_GROUPS_FOLDER_NAME)

    ## Monav ##

    @property
    def monav_data_path(self):
        """return a path where the all the Monav routing data is stored,
        this path can be used both for manipulating the data (add,delete, update) &
        using the data for routing)
        """
        path = os.path.join(self.routing_data_folder_path, MONAV_DATA_FOLDER_NAME)
        return self._assurePath(path)

    @property
    def monav_server_binary_path(self):
        arch = None
        deviceID = self.modrana.dmod.device_id
        if deviceID == 'n900':
            arch = 'armv7'
        elif deviceID == 'pc':
            # use the platform module to check if the PC is
            # 32bit or 64bit
            import platform

            binaryArch = platform.architecture()[0]
            if binaryArch == "32bit":
                arch = 'i386'
            elif binaryArch == "64bit":
                arch = 'amd64'
                # this is mostly for development testing and should
                # be superseded by properly packaged up-to-date Monav
                # with working Python bindings support & Unicode handling
        if arch:
            folder = "monav_%s" % arch
            monavBinaryPath = os.path.join('modules/mod_route/', folder, 'monav-server')
            if os.path.exists(monavBinaryPath):
                return monavBinaryPath
            else:
                log.error("monav routing server binary missing\n"
                          "(%s does not exist)", monavBinaryPath)
                return None
        else:
            # no known path to Monav binaries for this architecture
            return None

    @property
    def version_string(self):
        """
        return current version string or None if not available
        """
        return VERSION_STRING

    def _assurePathFolder(self, path, folder):
        """combine the given path and folder and make sure the path exists,
        return the resulting path"""
        path = os.path.join(path, folder)
        return self._assurePath(path)

    def _assurePath(self, path):
        """assure path exists and return it back"""
        # check if the path exists and create it if not
        utils.create_folder_path(path)
        return path
