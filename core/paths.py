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

import os
from core import utils

# paths
THEMES_FOLDER_PATH = "themes"
# folder names
MONAV_DATA_FOLDER_NAME = "monav_data"
CACHE_FOLDER_NAME = "cache"
TRACKLOG_FOLDER_NAME = "tracklogs"
MAPS_FOLDER_NAME = "maps"
POI_FOLDER_NAME = "poi"
ROUTING_DATA_FOLDER_NAME = "routing_data"
DEBUG_LOGS_FOLDER_NAME = "debug_logs"
# file names
OPTIONS_FILENAME = "options.bin"
POI_DB_FILENAME = "modrana_poi.db"
VERSION_INFO_FILENAME = "version.txt"


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

        # profile folder
        self.profileFolderPath = self.modrana.getProfilePath()
        # check the profile path and create the folders if necessary
        utils.createFolderPath(self.profileFolderPath)

        # load version string
        self.versionString = None
        self._loadVersionString()


    ## Important modRana folders ##

    def getProfilePath(self):
        """return path to the profile folder"""
        # check if the path exists and create it if not
        utils.createFolderPath(self.profileFolderPath)
        return self.profileFolderPath

    def getOptionsFilePath(self):
        """return path to the options store filename"""
        return os.path.join(self.getProfilePath(), OPTIONS_FILENAME)

    def getCacheFolderPath(self):
        """return path to a folder used for various cache data"""
        return self._assurePathFolder(self.getProfilePath(), CACHE_FOLDER_NAME)

    def getTracklogsFolderPath(self):
        """return path to a folder for storing tracklogs"""
        path = None
        # first check if the user overrode the tracklog folder path
        config = self.modrana.configs.getUserConfig()
        if config:
            path = config.get("tracklog_folder", None)
        if path is None:
        # try to get the path from device module
            if self.modrana.dmod:
                path = self.modrana.dmod.getTracklogFolderPath()

        if path is None: # this means there is no config or device path
            # use default path & assure it exists
            return self._assurePathFolder(self.getProfilePath(), TRACKLOG_FOLDER_NAME)
        else:
            return self._assurePath(path)

    def getMapFolderPath(self):
        """return a path to folder for map data storage"""
        path = None
        # first check if the user overrode the map folder path
        config = self.modrana.configs.getUserConfig()
        if config:
            path = config.get("map_folder", None)
        if path is None:
        # try to get the path from device module
            if self.modrana.dmod:
                path = self.modrana.dmod.getMapFolderPath()

        if path is None: # this means there is no config or device path
            # use default path & assure it exists
            return self._assurePathFolder(self.getProfilePath(), MAPS_FOLDER_NAME)
        else:
            return self._assurePath(path)

    def getPOIFolderPath(self):
        """return path to the POI folder"""
        if self.modrana.dmod:
            path = self.modrana.dmod.getPOIFolderPath()
            if path is not None: # None means there is no device dependent path
                return self._assurePath(path)
            else:
                return self._assurePathFolder(self.getProfilePath(), POI_FOLDER_NAME)
        else:
            return self._assurePathFolder(self.getProfilePath(), POI_FOLDER_NAME)

    def getPOIDatabasePath(self):
        """return path to the POI database file"""
        POIDBFilename = self.modrana.get('POIDBFilename', POI_DB_FILENAME)
        POIFolderPath = self.getPOIFolderPath()
        return os.path.join(POIFolderPath, POIDBFilename)

    def getLogFolderPath(self):
        """return path to the POI folder"""
        if self.modrana.dmod:
            path = self.modrana.dmod.getLogFolderPath()
            if path is not None: # None means there is no device dependent path
                return self._assurePath(path)
            else:
                return self._assurePathFolder(self.getProfilePath(), DEBUG_LOGS_FOLDER_NAME)
        else:
            return self._assurePathFolder(self.getProfilePath(), DEBUG_LOGS_FOLDER_NAME)


    def getThemesFolderPath(self):
        """Return path to the themes folder"""
        return THEMES_FOLDER_PATH

    def getRoutingDataFolderPath(self):
        """Return path to the routing data folder"""
        path = self.modrana.dmod.getRoutingDataFolderPath()
        if path is not None:
            return self._assurePath(path)
        else:
            return self._assurePath(os.path.join(self.getProfilePath(), ROUTING_DATA_FOLDER_NAME))

    ## Monav ##

    def getMonavDataPath(self):
        """return a path where the all the Monav routing data is stored,
        this path can be used both for manipulating the data (add,delete, update) &
        using the data for routing)
        """
        path = os.path.join(self.getRoutingDataFolderPath(), MONAV_DATA_FOLDER_NAME)
        return self._assurePath(path)

    def getMonavServerBinaryPath(self):
        arch = None
        deviceID = self.modrana.dmod.getDeviceIDString()
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
                print("routing: monav routing server binary missing")
                print("(%s does not exist)" % monavBinaryPath)
                return None
        else:
            # no known path to Monav binaries for this architecture
            return None

    def getVersionString(self):
        """
        return current version string or None if not available
        """
        return self.versionString

    def _loadVersionString(self):
        """
        load version string from file
        """
        self.versionString = None
        versionFilePath = VERSION_INFO_FILENAME
        # try read the version file
        if os.path.exists(versionFilePath):
            try:
                f = open(versionFilePath, 'r')
                versionString = f.read()
                f.close()
                # is it really string ?
                versionString = str(versionString)
                self.versionString = versionString
            except Exception:
                import sys

                e = sys.exc_info()[1]
                print("modRana config: loading version info failed")
                print(e)

    def _assurePathFolder(self, path, folder):
        """combine the given path and folder and make sure the path exists,
        return the resulting path"""
        path = os.path.join(path, folder)
        return self._assurePath(path)

    def _assurePath(self, path):
        """assure path exists and return it back"""
        # check if the path exists and create it if not
        utils.createFolderPath(path)
        return path