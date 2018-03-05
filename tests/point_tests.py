import unittest
from core.point import Point
from core.point import TurnByTurnPoint

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

    def full_point_test(self):
        """Check if a point with all constructor options is correctly created"""
        point = Point(1.0, 2.0, elevation=100.5, name="foo name",
                      summary="bar summary", message="baz message")
        self.assertEqual(point.lat, 1.0)
        self.assertEqual(point.lon, 2.0)
        self.assertEqual(point.elevation, 100.5)
        # test name, etc.
        self.assertEqual(point.name, "foo name")
        self.assertEqual(point.summary, "bar summary")
        self.assertEqual(point.description, "baz message")
        # test the tuple getters/setters
        self.assertEqual(point.getLL(), (1.0, 2.0))
        point.setLL(3.0, 4.0)
        self.assertEqual(point.getLL(), (3.0, 4.0))
        self.assertEqual(point.getLLE(), (3.0, 4.0, 100.5))
        point.setLLE(5.0, 6.0, 200.5)
        self.assertEqual(point.getLLE(), (5.0, 6.0, 200.5))
        self.assertEqual(point.getLLEM(), (5.0, 6.0, 200.5, "baz message"))


class TurnByTurnPointTests(unittest.TestCase):

    def basic_test(self):
        """Test basic TurnByTurn point functionality"""
        point = TurnByTurnPoint(1.0, 2.0, elevation=123.45,
                                message="foo message",
                                ssml_message="ssml message",
                                icon="some_icon_id")

        # distances should be None by default
        self.assertIsNone(point.current_distance)
        self.assertIsNone(point.distance_from_start)

        # visited should be False as well
        self.assertFalse(point.visited)

        self.assertEqual(point.ssml_message, "ssml message")
        self.assertEqual(point.icon, "some_icon_id")

        # check if the LLEMI tuple is correct as well
        self.assertEqual(point.llemi, (1.0, 2.0, 123.45, "foo message", "some_icon_id"))

        # try setting the distances
        point.current_distance = 200
        point.distance_from_start = 300
        self.assertEqual(point.current_distance, 200)
        self.assertEqual(point.distance_from_start, 300)