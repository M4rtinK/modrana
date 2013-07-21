# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# ModRana config files handling
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
import shutil
import traceback
from modules.configobj import ConfigObj

CONFIGS = ["map_config.conf", "user_config.conf"]


class Configs(object):
    def __init__(self, modrana):
        self.modrana = modrana
        self.paths = modrana.paths

        self.userConfig = {}
        self.mapConfig = {}

        # check if config files exist
        self.checkConfigFilesExist()

    def checkConfigFilesExist(self):
        """
        assure that configuration files are available in the profile folder
        - provided the default configuration files exist and that the profile folder
        exists and is writable
        """
        profilePath = self.modrana.getProfilePath()
        for config in CONFIGS:
            configPath = os.path.join(profilePath, config)
            if not os.path.exists(configPath):
                try:
                    source = os.path.join("data/default_configuration_files", config)
                    print(" ** config:copying default configuration file to profile folder")
                    print(" ** from: %s" % source)
                    print(" ** to: %s" % configPath)
                    shutil.copy(source, configPath)
                    print(" ** DONE")
                except Exception:
                    import sys

                    e = sys.exc_info()[1]
                    print("config: copying default configuration file to profile folder failed", e)

    def upgradeConfigFiles(self):
        """
        upgrade config files, if needed
        """
        upgradeCount = 0
        profilePath = self.modrana.getProfilePath()
        print("modRana configs: upgrading configuration files in %s" % profilePath)
        # first check the configs actually exist
        self.checkConfigFilesExist()

        for config in CONFIGS:
            # load default config
            defaultConfigPath = os.path.join("data/default_configuration_files", config)
            installedConfigPath = os.path.join(profilePath, config)
            try:
                defaultRev = int(ConfigObj(defaultConfigPath).get("revision", 0))
                installedRev = int(ConfigObj(installedConfigPath).get("revision", 0))

                if defaultRev > installedRev: # is installed config is outdated ?
                    print('modRana configs: %s is outdated, upgrading' % config)
                    # rename installed config as the user might have modified it
                    newName = "%s_old_revision_%d" % (config, installedRev)
                    newPath = os.path.join(profilePath, newName)
                    shutil.move(installedConfigPath, newPath)
                    print('modRana configs: old file renamed to %s' % newName)

                    # install the (newer) default config
                    shutil.copy(defaultConfigPath, profilePath)

                    # update upgrade counter
                    upgradeCount += 1
            except Exception:
                import sys

                e = sys.exc_info()[1]
                print("modRana configs: upgrading config file: %s failed" % config)
                print(e)
        if upgradeCount:
            print("modRana configs: %d configuration files upgraded" % upgradeCount)
        else:
            print("modRana configs: no configuration files needed upgrade")

    def loadAll(self):
        """
        load all configuration files
        """
        self.loadMapConfig()
        self.loadUserConfig()

    def getUserConfig(self):
        return self.userConfig

    def loadUserConfig(self):
        """load the user oriented configuration file."""
        path = os.path.join(self.modrana.getProfilePath(), "user_config.conf")

        try:
            config = ConfigObj(path)
            if 'enabled' in config:
                if config['enabled'] == 'True':
                    self.userConfig = config

        except Exception:

            import sys

            e = sys.exc_info()[1]
            print("modRana configs: loading user_config.conf failed")
            print("modRana configs: check the syntax")
            print("modRana configs: and if the config file is present in the main directory")
            print("modRana configs: this happened:\n%s\nconfig: that's all" % e)

    def getMapConfig(self):
        """
        get the "raw" map config
        """
        return self.mapConfig

    def loadMapConfig(self):
        """
        load the map configuration file
        """

        configVariables = {
            'label': 'label',
            'url': 'tiles',
            'max_zoom': 'maxZoom',
            'min_zoom': 'minZoom',
            'type': 'type',
            'folder_prefix': 'folderPrefix',
            'coordinates': 'coordinates',
        }

        def allNeededIn(needed, layerDict):
            """
            check if all required values are filled in
            """
            # TODO: optimize this ?
            for key in needed:
                if key in layerDict:
                    continue
                else:
                    return False
            return True

        mapConfigPath = os.path.join(self.modrana.getProfilePath(), 'map_config.conf')
        # check if the map configuration file is installed
        if not os.path.exists(mapConfigPath):
            # nothing in profile folder -> try to use the default config
            print("modRana configs: no config in profile folder, using default map layer configuration file")
            mapConfigPath = os.path.join("data/default_configuration_files", 'map_config.conf')
            if not os.path.exists(mapConfigPath):
                # no map layer config available
                print("modRana configs: map layer configuration file not available")
                return False
        try:
            self.mapConfig = ConfigObj(mapConfigPath)
        except Exception:
            import sys

            e = sys.exc_info()[1]
            print("modRana configs: loading map_config.conf failed: %s" % e)
            traceback.print_exc(file=sys.stdout) # find what went wrong
            return False
        return True

    def getUserAgent(self):
        """return the default modRana User-Agent"""
        #debugging:
        # return "Mozilla/5.0 (compatible; MSIE 5.5; Linux)"
        #TODO: setting from configuration file, CLI & interface
        return "modRana flexible GPS navigation system (compatible; Linux)"