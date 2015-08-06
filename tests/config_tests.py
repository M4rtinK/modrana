import os
import unittest

class BasicDefaultConfigFilesTests(unittest.TestCase):
    def default_configs_exist_test(self):
        """Check that the default configuration files exist"""
        self.assertTrue(os.path.exists("../data/default_configuration_files/map_config.conf"))
        self.assertTrue(os.path.exists("../data/default_configuration_files/user_config.conf"))
        
