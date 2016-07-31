import os
import unittest
import tempfile
import shutil
from configobj import ConfigObj

from core import configs

MAP_CONFIG_PATH = os.path.join("..", configs.DEFAULT_CONFIGS_DIR, configs.MAP_CONFIG_FILE)
USER_CONFIG_PATH = os.path.join("..", configs.DEFAULT_CONFIGS_DIR, configs.USER_CONFIG_FILE)

MAP_CONFIG_R1 = """
revision=1
[layers]

## OpenStreetMap layers

[[mapnik]]
  label=Mapnik (default)
  url="http://c.tile.openstreetmap.org/"
  type=png
  max_zoom=18
  min_zoom=0
  folder_prefix=OpenStreetMap I
  coordinates=osm
  group="osm"
  icon="mapnik"

[[osm_landscape]]
  label=Landscape
  url="http://b.tile3.opencyclemap.org/landscape/"
  type=png
  max_zoom=18
  min_zoom=0
  folder_prefix=osm_landscape
  coordinates=osm
  group="osm"

[groups]

[[osm]]
  label="OpenStreetMap"
  icon="osm_icon"
"""

MAP_CONFIG_R2 = """

revision=2
[layers]

## OpenStreetMap layers

[[mapnik]]
  label=Mapnik (default)
  url="http://c.tile.openstreetmap.org/"
  type=png
  max_zoom=18
  min_zoom=0
  folder_prefix=OpenStreetMap I
  coordinates=osm
  group="osm"
  icon="mapnik"

[[mapnik_bw]]
  label=Mapnik b/w
  url="http://a.www.toolserver.org/tiles/bw-mapnik/"
  type=png
  max_zoom=18
  min_zoom=0
  folder_prefix=osm_mapnik_bw
  coordinates=osm
  group="osm"

[groups]

[[osm]]
  label="OpenStreetMap"
  icon="osm_icon"
"""

class BasicDefaultConfigFilesTests(unittest.TestCase):
    def default_configs_exist_test(self):
        """Check that the default configuration files exist"""
        self.assertTrue(os.path.exists(MAP_CONFIG_PATH))
        self.assertTrue(os.path.exists(USER_CONFIG_PATH))

    def map_config_valid_test(self):
        """Check if the map config is valid (can be parsed by ConfigObj)"""
        ConfigObj(MAP_CONFIG_PATH)

    def user_config_valid_test(self):
        """Check if the user config is valid (can be parsed by ConfigObj)"""
        ConfigObj(USER_CONFIG_PATH)

    def missing_default_configs_test(self):
        """Check that missing default configs raise an error"""
        with tempfile.TemporaryDirectory() as temp_dir:
            confs = configs.Configs(default_configs_dir=temp_dir, configs_dir=temp_dir)
            self.assertEqual(confs.check_config_files_exist(), [])
            self.assertFalse(confs.load_all())
            self.assertFalse(confs.load_user_config())
            self.assertFalse(confs.load_map_config())

    def setUp(self):
        # setup the folders
        self._temp_dir = tempfile.TemporaryDirectory()
        self._defaults_path = os.path.join(self._temp_dir.name, "defaults")
        self._profile_path = os.path.join(self._temp_dir.name, "profile")
        os.mkdir(self._defaults_path)
        os.mkdir(self._profile_path)
        shutil.copy(USER_CONFIG_PATH, self._defaults_path)
        shutil.copy(MAP_CONFIG_PATH, self._defaults_path)

    def tearDown(self):
        self._temp_dir.cleanup()

    def config_loading_test(self):
        """Check that the map config can be succesfully loaded"""
        confs = configs.Configs(default_configs_dir=self._defaults_path, configs_dir=self._profile_path)
        # check if modRana correctly copies the default config files to the
        # profile directory if none are found there
        loaded_configs = confs.check_config_files_exist()
        self.assertTrue(configs.MAP_CONFIG_FILE in loaded_configs)
        self.assertTrue(configs.USER_CONFIG_FILE in loaded_configs)
        self.assertTrue(confs.load_all())
        self.assertTrue(confs.load_user_config())
        self.assertTrue(confs.load_map_config())
        # check map config contents
        user_config = confs.user_config
        map_config = confs.map_config
        # the parsed config should contain something
        self.assertTrue(user_config)
        self.assertTrue(map_config)
        # check if user config contains what we expect
        self.assertTrue(user_config["enabled"])
        self.assertGreater(int(user_config["revision"]), 0)
        self.assertTrue("cycle" in user_config)
        self.assertTrue("car" in user_config)
        self.assertTrue("train" in user_config)
        self.assertTrue("foot" in user_config)
        self.assertTrue("bus" in user_config)
        # check if map config contains what we expect
        self.assertGreater(int(map_config["revision"]), 0)
        # do we have some layers & layer groups ?
        # - we need at least one layer & one group
        self.assertGreater(len(map_config["layers"]), 0)
        self.assertTrue(map_config["layers"]["mapnik"])
        self.assertGreater(len(map_config["groups"]), 0)
        self.assertTrue(map_config["groups"]["osm"])

    def config_upgrade_test(self):
        """Check that config file upgrades work"""
        confs = configs.Configs(default_configs_dir=self._defaults_path, configs_dir=self._profile_path)
        # NOTE: just testing the map config file as that's
        #       what gets updated the most often

        # overwrite the actual default file with a custom one with revision == 2
        with open(os.path.join(self._defaults_path, configs.MAP_CONFIG_FILE), "wt") as f:
             f.write(MAP_CONFIG_R2)

        # also place another custom config with revision == 1 to the profile folder
        config_path = os.path.join(self._profile_path, configs.MAP_CONFIG_FILE)
        with open(config_path, "wt") as f:
             f.write(MAP_CONFIG_R1)

        # check the file before upgrade
        conf_r1 = ConfigObj(config_path)
        self.assertEqual(int(conf_r1["revision"]), 1)
        self.assertTrue("mapnik" in conf_r1["layers"])
        self.assertTrue("osm_landscape" in conf_r1["layers"])
        self.assertTrue("mapnik_bw" not in conf_r1["layers"])
        self.assertTrue("osm" in conf_r1["groups"])

        # trigger the upgrade
        confs.upgrade_config_files()

        # check if the old file has been renamed & is the revision 1 file
        renamed_map_config_path = os.path.join(self._profile_path, configs.MAP_CONFIG_FILE + "_old_revision_1")
        self.assertTrue(os.path.isfile(renamed_map_config_path))
        conf_renamed = ConfigObj(renamed_map_config_path)
        self.assertEqual(int(conf_renamed["revision"]), 1)
        self.assertTrue("mapnik" in conf_renamed["layers"])
        self.assertTrue("osm_landscape" in conf_renamed["layers"])
        self.assertTrue("mapnik_bw" not in conf_renamed["layers"])
        self.assertTrue("osm" in conf_renamed["groups"])

        # check content of the upgraded file
        conf_r2 = ConfigObj(config_path)
        self.assertEqual(int(conf_r2["revision"]), 2)
        self.assertTrue("mapnik" in conf_r2["layers"])
        self.assertTrue("osm_landscape" not in conf_r2["layers"])
        self.assertTrue("mapnik_bw" in conf_r2["layers"])
        self.assertTrue("osm" in conf_r2["groups"])
