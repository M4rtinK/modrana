#!/usr/bin/python
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
import modrana_utils

class Paths:
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
    modrana_utils.createFolderPath(self.profileFolderPath)


  ## Important modRana folders ##

  def getProfilePath(self):
    """return path to the profile folder"""
    # check if the path exists and create it if not
    modrana_utils.createFolderPath(self.profileFolderPath)
    return self.profileFolderPath

  def getOptionsFilePath(self):
    """return path to the options store filename"""
    return os.path.join(self.getProfilePath(),"options.bin")

  def getCacheFolderPath(self):
    """return path to a folder used for various cache data"""
    return self._assurePathFolder(self.getProfilePath(), "cache")

  def getTracklogsFolderPath(self):
    """return path to a folder for storing tracklogs"""
    path = None
    # first check if the user overrode the tracklog folder path
    config = self.modrana.m.get('config', None)
    if config:
      path = config.getTracklogFolderPath()
    if path == None:
    # try to get the path from device module
      if self.modrana.dmod:
        path = self.modrana.dmod.getTracklogFolderPath()

    if path == None: # this means there is no config or device path
      # use default path & assure it exists
      return self._assurePathFolder(self.getProfilePath(), "tracklogs")
    else:
      return self._assurePath(path)

  def getMapFolderPath(self):
    """return a path to folder for map data storage"""
    path = None
    # first check if the user overrode the map folder path
    config = self.modrana.m.get('config', None)
    if config:
      path = config.getMapFolderPath()
    if path == None:
    # try to get the path from device module
      if self.modrana.dmod:
        path = self.modrana.dmod.getMapFolderPath()

    if path == None: # this means there is no config or device path
      # use default path & assure it exists
      return self._assurePathFolder(self.getProfilePath(), "maps")
    else:
      return self._assurePath(path)

  def getPOIFolderPath(self):
    """return path to the POI folder"""
    if self.modrana.dmod:
      path = self.modrana.dmod.getPOIFolderPath()
      if path != None: # None means there is no device dependent path
        return self._assurePath(path)
      else:
        return self._assurePathFolder(self.getProfilePath(), "poi")
    else:
      return self._assurePathFolder(self.getProfilePath(), "poi")

  def getPOIDatabasePath(self):
    """return path to the POI database file"""
    POIDBFilename = self.modrana.get('POIDBFilename', 'modrana_poi.db')
    POIFolderPath = self.getPOIFolderPath()
    return os.path.join(POIFolderPath,POIDBFilename)

  def getLogFolderPath(self):
    """return path to the POI folder"""
    if self.modrana.dmod:
      path = self.modrana.dmod.getLogFolderPath()
      if path != None: # None means there is no device dependent path
        return self._assurePath(path)
      else:
        return self._assurePathFolder(self.getProfilePath(), "debug_logs")
    else:
      return self._assurePathFolder(self.getProfilePath(), "debug_logs")

  def _assurePathFolder(self, path, folder):
    """combine the given path and folder and make sure the path exists,
    return the resulting path"""
    path = os.path.join(path, folder)
    return self._assurePath(path)

  def _assurePath(self, path):
    """assure path exists and return it back"""
    # check if the path exists and create it if not
    modrana_utils.createFolderPath(path)
    return path
