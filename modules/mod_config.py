#!/usr/bin/python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Configuration options
#
# Rename this file to mod_config.py to use it
#----------------------------------------------------------------------------
# Copyright 2007-2008, Oliver White
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
from base_module import ranaModule
from configobj import ConfigObj
import os
import shutil

def getModule(m,d,i):
  return(config(m,d,i))

class config(ranaModule):
  """Handle configuration, options, and setup"""
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.userConfigPath = 'user_config.conf'
    self.userConfig = {}

    """ make sure the config files are present
    in the profile folder"""
    self.checkConfigs()
    """parse the main configration file"""
    userConfPath = os.path.join(self.modrana.getProfilePath(), 'user_config.conf')
    self.parseUserConfig(userConfPath)

  def firstTime(self):

    # *** Various hardcoded peristant variables ***

    # Option: Number of threads for batch-downloading tiles
    self.set('maxBatchThreads', 5)

    # Option: Bath tile download threads
    # this sets the number of threads for bach tile download
    # even values of 10 can lead to 3000+ open sockets on a fast internet connection
    # handle with care :)
    # UPDATE: modRana now reuses open sockets so it might not be that bad any more
    self.set('maxDlThreads', 5)
    # Option: Batch size estimation threads
    # this sets the number of threads used for determining the size of the batch (from http headers)
    # NOTE: even though we are downloading only the headers,
    # for a few tousand tiles this can be an untrival amount of data
    # (so use this with caution on metered connections)
    self.set('maxSizeThreads', 20)

    # Google API key for modRana
    self.set('googleAPIKey', 'ABQIAAAAv84YYgTIjdezewgb8xl5_xTKlax5G-CAZlpGqFgXfh-jq3S0yRS6XLrXE9CkHPS6KDCig4gHvHK3lw')

    # Option: set your start position
    #self.set("pos", (49.2, 16.616667)) # Brno

  def checkConfigs(self):
    """assure that configuration files are available in the profile folder"""
    profilePath = self.modrana.getProfilePath()
    configs = ["map_config.conf", "user_config.conf"]
    for config in configs:
      configPath = os.path.join(profilePath, config)
      if not os.path.exists(configPath):
        try:
          source = os.path.join("data/default_configuration_files", config)
          print(" ** config:copying default configuration file to profile folder")
          print(" ** from: %s" % source)
          print(" ** to: %s" % configPath)
          shutil.copy(source, configPath)
          print(" ** DONE")
        except Exception, e:
          print("config: copying default configuration file to profile folder failed", e)

  def getMapFolderPath(self):
    """return the prefered map folder path from the user
    configuration file an None if no such path is specified"""
    if 'map_folder' in self.userConfig:
      return self.userConfig['map_folder']
    else:
      return None

  def getTracklogFolderPath(self):
    """return the prefered tracklog folder path from the user
    configuration file an None if no such path is specified"""
    if 'tracklog_folder' in self.userConfig:
      return self.userConfig['tracklog_folder']
    else:
      return None

  def parseUserConfig(self, path):
    """Par user created configuration file."""

    try:
      config = ConfigObj(path)
      if 'enabled' in config:
        if config['enabled'] == 'True':
          self.userConfig = config        

    except Exception, e:
      print "config: loading user_config.conf failed"
      print "config: check the syntax"
      print "config: and if the config file is present in the main directory"
      print "config: this happended:\n%s\nconfig: thats all" % e
