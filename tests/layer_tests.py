import unittest
import io
from configobj import ConfigObj
from unittest.mock import MagicMock

from core.layers import MapLayer, MapLayerGroup

MAP_CONFIG = """
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
  timeout=240.5
  connection_timeout=30

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

config = ConfigObj(io.StringIO(MAP_CONFIG))

class MapLayerTests(unittest.TestCase):

    def layer_parsing_test(self):
        """Check layer parsing works correctly."""
        mapnik_config = config["layers"]["mapnik"]
        layer = MapLayer(layerId="mapnik", config=mapnik_config)
        self.assertEqual(layer.id, "mapnik")
        self.assertEqual(layer.label, "Mapnik (default)")
        self.assertEqual(layer.url, "http://c.tile.openstreetmap.org/")
        self.assertEqual(layer.type, "png")
        self.assertEqual(layer.max_zoom, 18)
        self.assertEqual(layer.min_zoom, 0)
        self.assertEqual(layer.folder_name, "OpenStreetMap I")
        self.assertEqual(layer.group_id, "osm")
        self.assertEqual(layer.icon, "mapnik")
        self.assertEqual(layer.timeout, 240.5)

        expected_dict = {
            "id": "mapnik",
            "label": "Mapnik (default)",
            "url": "http://c.tile.openstreetmap.org/",
            "type": "png",
            "max_zoom": 18,
            "min_zoom": 0,
            "folder_name": "OpenStreetMap I",
            "coordinates": "osm",
            "group_id": "osm",
            "icon": "mapnik",
            "timeout": 240.5,
            "connection_timeout": 30
        }
        self.assertDictEqual(layer.dict, expected_dict)