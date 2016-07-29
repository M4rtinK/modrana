import os
import unittest
from configobj import ConfigObj

MAP_CONFIG_PATH = "../data/default_configuration_files/map_config.conff"
USER_CONFIG_PATH = "../data/default_configuration_files/user_config.conf"

class BasicDefaultConfigFilesTests(unittest.TestCase):
    def default_configs_exist_test(self):
        """Check that the default configuration files exist"""
        self.assertTrue(os.path.exists(MAP_CONFIG_PATH))
        self.assertTrue(os.path.exists(USER_CONFIG_PATH))

    def map_config_valid_Test(self):
        """Check if the map config is valid (can be parsed by ConfigObj)"""
        ConfigObj(MAP_CONFIG_PATH)

    def user_config_valid_Test(self):
        """Check if the user config is valid (can be parsed by ConfigObj)"""
        ConfigObj(USER_CONFIG_PATH)

