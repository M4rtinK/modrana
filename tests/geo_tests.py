import unittest
from core import geo
from core.point import Point

class GeoTests(unittest.TestCase):

    def get_closest_point_test(self):
        """Test the get_closest_point() function."""
        reference_point = Point(lat=0, lon=0)
        # empty point list should return None
        result = geo.get_closest_point(reference_point, [])
        self.assertIsNone(result)

        # check if closest point is returned
        closest_point = Point(lat=2, lon=0)
        point_list = [Point(lat=5, lon=0),
                      closest_point,
                      Point(lat=4, lon=5)]
        result = geo.get_closest_point(reference_point, point_list)
        self.assertEqual(closest_point, result)

        # if there is just one point in the list
        # it should be returned
        closest_point = Point(lat=5, lon=5)
        point_list = [closest_point]
        result = geo.get_closest_point(reference_point, point_list)
        self.assertEqual(closest_point, result)

    def get_closest_lle_test(self):
        """Test the get_closest_lle() function."""
        reference_lle = (0, 0)
        # empty point list should return None
        result = geo.get_closest_lle(reference_lle, [])
        self.assertIsNone(result)

        # check if closest point is returned
        closest_lle = (2, 0)
        lle_list = [(5, 0),
                    closest_lle,
                    (4, 5)]
        result = geo.get_closest_lle(reference_lle, lle_list)
        self.assertEqual(closest_lle, result)

        # if there is just one point in the list
        # it should be returned
        closest_lle = (5, 5)
        lle_list = [closest_lle]
        result = geo.get_closest_lle(reference_lle, lle_list)
        self.assertEqual(closest_lle, result)




