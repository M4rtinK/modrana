import os
import unittest

MONAV_MODE_DIRS = ["routing_bike", "routing_car", "routing_pedestrian"]
MONAV_MODA_DATA_REQUIRED_FILES = [
    "Contraction Hierarchies_edges",
    "Contraction Hierarchies_names",
    "Contraction Hierarchies_paths",
    "Contraction Hierarchies_types",
    "GPSGrid_grid",
    "GPSGrid_index_1",
    "GPSGrid_index_2",
    "GPSGrid_index_3",
    "Module.ini"
]

class MonavRoutingTests(unittest.TestCase):


    def setUp(self):
        """Prepare folder structure for checking the Monav data discovery code"""
        pass

    def tearDown(self):
        """Remove the testing data structures"""
        pass

    def default_configs_exist_test(self):
        """Check that the default configuration files exist"""
        self.assertTrue(os.path.exists("../data/default_configuration_files/map_config.conf"))
        self.assertTrue(os.path.exists("../data/default_configuration_files/user_config.conf"))
        
