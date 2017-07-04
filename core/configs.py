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
from configobj import ConfigObj

import logging
log = logging.getLogger("core.config")

MAP_CONFIG_FILE = "map_config.conf"
USER_CONFIG_FILE = "user_config.conf"
CONFIGS = [MAP_CONFIG_FILE, USER_CONFIG_FILE]
DEFAULT_CONFIGS_DIR = "data/default_configuration_files"

class Configs(object):
    def __init__(self, configs_dir, default_configs_dir=DEFAULT_CONFIGS_DIR):
        self._configs_dir = configs_dir
        self._default_configs_dir = default_configs_dir

        self._user_config = {}
        self._map_config = {}

        # check if config files exist
        self.check_config_files_exist()

    def check_config_files_exist(self):
        """Assure that configuration files are available.

        Check that the default configuration files exist and that the profile folder
        exists and is writable.

        :returns: list of config file names found
        :rtype: list
        """
        existing_configs = []
        for config in CONFIGS:
            configPath = os.path.join(self._configs_dir, config)
            if os.path.exists(configPath):
                existing_configs.append(config)
            else:
                try:
                    source = os.path.join(self._default_configs_dir, config)
                    log.info(" ** copying default configuration file to profile folder")
                    log.info(" ** from: %s", source)
                    log.info(" ** to: %s", configPath)
                    shutil.copy(source, configPath)
                    log.info(" ** default config file copying DONE")
                except Exception:
                    log.exception("copying default configuration file to profile folder failed")

        return existing_configs

    def _safe_parse(self, config_path):
        parsed_config = None
        try:
            parsed_config = ConfigObj(config_path)
        except:
            log.exception("parsing of config file failed: %s", config_path)
        return parsed_config

    def upgrade_config_files(self):
        """Upgrade config files (if needed)."""
        upgrade_count = 0
        log.info("upgrading modRana configuration files in %s", self._configs_dir)
        # first check the configs actually exist
        self.check_config_files_exist()

        for config in CONFIGS:
            # try to upgrade the config
            default_config_path = os.path.join(self._default_configs_dir, config)
            config_path = os.path.join(self._configs_dir, config)
            try:
                # revision of default config
                default_config = self._safe_parse(default_config_path)
                default_rev = 0
                if default_config is not None:
                    default_rev = int(default_config.get("revision", 0))

                # revision of installed config
                installed_config = self._safe_parse(config_path)
                installed_rev = 0
                if installed_config is not None:
                    installed_rev = int(installed_config.get("revision", 0))

                if default_rev > installed_rev:  # is the installed config outdated ?
                    log.info('config file %s is outdated, upgrading', config)
                    # rename installed config as the user might have modified it
                    new_name = "%s_old_revision_%d" % (config, installed_rev)
                    new_path = os.path.join(self._configs_dir, new_name)
                    shutil.move(config_path, new_path)
                    log.info('old config file renamed to %s' % new_name)

                    # install the (newer) default config
                    shutil.copy(default_config_path, self._configs_dir)

                    # update upgrade counter
                    upgrade_count += 1
            except Exception:
                log.exception("upgrading config file: %s failed", config)

        if upgrade_count:
            log.info("%d configuration files upgraded", upgrade_count)
        else:
            log.info("no configuration files needed upgrade")

    def load_all(self):
        """"Load all configuration files.

        :returns: True if all configs were loaded successfully, False otherwise
        :rtype: bool
        """

        return all((self.load_map_config(), self.load_user_config()))

    @property
    def user_config(self):
        """The "raw" user config."""
        return self._user_config

    def load_user_config(self):
        """Load the user oriented configuration file."""

        config_path = os.path.join(self._configs_dir, USER_CONFIG_FILE)
        if not os.path.isfile(config_path):
            return False

        try:
            config = ConfigObj(config_path)
            if 'enabled' in config:
                if config['enabled'] == 'True':
                    self._user_config = config
            return True
        except Exception:
            log.exception("loading user_config.conf from %s failed, check the syntax\n"
                          "and if the config file is present in the modRana profile directory.",
                          self._configs_dir)
            return False

    @property
    def map_config(self):
        """The "raw" map config."""
        return self._map_config

    def load_map_config(self):
        """Load the map configuration file."""

        config_variables = {
            'label': 'label',
            'url': 'tiles',
            'max_zoom': 'max_zoom',
            'min_zoom': 'min_zoom',
            'type': 'type',
            'folder_prefix': 'folderPrefix',
            'coordinates': 'coordinates',
        }

        def all_needed_in(needed, layer_dict):
            """Check if all required values are filled in."""
            # TODO: optimize this ?
            for key in needed:
                if key in layer_dict:
                    continue
                else:
                    return False
            return True

        map_config_path = os.path.join(self._configs_dir, MAP_CONFIG_FILE)
        default_map_config_path = os.path.join(DEFAULT_CONFIGS_DIR, MAP_CONFIG_FILE)
        map_config = None
        # check if the map configuration file is installed
        if os.path.exists(map_config_path):
            map_config = self._safe_parse(map_config_path)
        # installed config missing or invalid -> try to use the default config
        if map_config is None:
            log.error("installed map_config.conf unusable, falling back to default map_config.conf")
            map_config = self._safe_parse(default_map_config_path)
        if map_config:
            self._map_config = map_config
            return True
        else:
            log.critical("even default map_config.conf is missing or invalid")
            return False

    @property
    def user_agent(self):
        """Returns the default modRana User-Agent.

        :returns: default modRana user agent
        :rtype: str
        """

        #debugging:
        # return "Mozilla/5.0 (compatible; MSIE 5.5; Linux)"
        #TODO: setting from configuration file, CLI & interface
        return "modRana flexible GPS navigation system (compatible; Linux)"