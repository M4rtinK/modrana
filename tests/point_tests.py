import unittest
from core.point import Point

class PointTests(unittest.TestCase):
    def basic_point_test(self):
        """Test basic Point functionality"""

    def lat_lon_only_point_test(self):
        """Test that a lat-lon-only point can be created"""
        point = Point(1.0, 2.0)
        self.assertEqual(point.lat, 1.0)
        self.assertEqual(point.lon, 2.0)
        self.assertIsNone(point.name)
        self.assertEqual(point.summary, "")
        self.assertIsNone(point.description)
        self.assertIsNone(point.elevation)
        self.assertEqual(point.getUrls(), [])

