import unittest
from core.way import Way
from core.point import Point

class WayTests(unittest.TestCase):

    def empty_way_test(self):
        """Test if an empty Way can be created."""
        way = Way()
        # points
        self.assertListEqual(way.points_lle, [])
        self.assertListEqual(way.points_radians_ll, [])
        self.assertListEqual(way.points_radians_lle, [])
        self.assertListEqual(way.points_radians_lle, [])
        self.assertListEqual(way.get_points_lle_radians(drop_elevation=False), [])
        self.assertListEqual(way.get_points_lle_radians(drop_elevation=True), [])
        self.assertIsNone(way.get_closest_point(point=Point(lat=0, lon=0)))

        #message points
        self.assertListEqual(way.message_points, [])
        self.assertListEqual(way.message_points_lle, [])
        self.assertEqual(way.message_point_count, 0)
        self.assertIsNone(way.get_closest_message_point(point=Point(lat=0, lon=0)))

        # misc
        self.assertIsNone(way.length)
        self.assertIsNone(way.duration)

        # test getters and setters
        with self.assertRaises(IndexError):
            way.get_point_by_index(1)
        with self.assertRaises(IndexError):
            way.get_message_point_by_index(1)
        with self.assertRaises(IndexError):
            way.set_message_point_by_index(1, Point(lat=1, lon=1))
        self.assertIsNone(way.get_closest_message_point(Point(lat=1, lon=1)))

        # clearing should also work
        way.clear_message_points()

    def basic_way_test(self):
        """Test basic Way creation and usage."""
        first = (0.0, 0.0, 0.0)
        second = (1.0, 1.0, 100.0)
        third = (2.0, 2.0, 200.0)
        lle_list = [first, second, third]
        way = Way(points=lle_list)
        self.assertListEqual(way.points_lle, lle_list)
        self.assertEqual(way.point_count, 3)
        # check getting points by index
        self.assertEqual(way.get_point_by_index(0).getLLE(), first)
        self.assertEqual(way.get_point_by_index(1).getLLE(), second)
        self.assertEqual(way.get_point_by_index(2).getLLE(), third)
        # negative indexing should work the same as in a list
        self.assertEqual(way.get_point_by_index(-1).getLLE(), third)
        self.assertEqual(way.get_point_by_index(-2).getLLE(), second)
        self.assertEqual(way.get_point_by_index(-3).getLLE(), first)
        # out of bounds access should throw an index error
        with self.assertRaises(IndexError):
            way.get_point_by_index(100)
        with self.assertRaises(IndexError):
            way.get_point_by_index(-100)
        # route length or duration has not been set
        self.assertIsNone(way.length)
        self.assertIsNone(way.duration)
        # there should be no message points
        self.assertListEqual(way.message_points, [])
        self.assertEqual(way.message_point_count, 0)

    def add_point_test(self):
        """Test adding regular points to a Way."""
        first = (0.0, 0.0, 0.0)
        second = (1.0, 1.0, 100.0)
        third = (2.0, 2.0, 200.0)
        lle_list = [first, second, third]
        way = Way(points=lle_list)
        way.add_point(Point(lat=50.0, lon=50.0, elevation=300.0))
        self.assertEqual(way.point_count, 4)
        self.assertListEqual(way.points_lle,
                             [first, second, third, (50.0, 50.0, 300.0)])
        way.add_point_lle(100.0, 100.0, 600.0)
        self.assertEqual(way.point_count, 5)
        self.assertListEqual(way.points_lle,
                             [first, second, third, (50.0, 50.0, 300.0), (100.0, 100.0, 600.0)])
        self.assertEqual(way.get_point_by_index(-1).getLLE(), (100.0, 100.0, 600.0))

    def _compare_points(self, p1, p2):
        return p1.getLLEM() == p2.getLLEM()

    def basic_message_points_test(self):
        """Test using Way with message points."""
        # put some regular points to the way first
        first = (0.0, 0.0, 0.0)
        second = (1.0, 1.0, 100.0)
        third = (2.0, 2.0, 200.0)
        lle_list = [first, second, third]
        way = Way(points=lle_list)
        # add some message points
        point1 = Point(lat=50.0, lon=50.0, elevation=300.0, message="foo")
        point2 = Point(lat=75.0, lon=75.0, elevation=600.0, message="bar")
        point3 = Point(lat=100.0, lon=100.0, elevation=1200.0, message="baz")
        point4 = Point(lat=125.0, lon=125.0, elevation=2400.0, message="abc")
        point5 = Point(lat=150.0, lon=150.0, elevation=4800.0, message="def")
        way.add_message_point(point1)
        way.add_message_point(point2)
        self.assertEqual(way.message_point_count, 2)
        self.assertListEqual(way.message_points, [point1, point2])
        expected_list1 = [(50.0, 50.0, 300.0), (75.0, 75.0, 600.0)]
        self.assertListEqual(way.message_points_lle, expected_list1)
        way.add_message_points([point3, point4, point5])
        expected_list2 = expected_list1.copy()
        expected_list2.extend([(100.0, 100.0, 1200.0),
                               (125.0, 125.0, 2400.0),
                               (150.0, 150.0, 4800.0)])
        self.assertEqual(way.message_point_count, 5)
        self.assertListEqual(way.message_points, [point1, point2, point3, point4, point5])
        self.assertListEqual(way.message_points_lle, expected_list2)
        # check getters
        self.assertTrue(self._compare_points(way.get_message_point_by_index(2), point3))
        self.assertTrue(self._compare_points(way.get_message_point_by_index(-1), point5))
        # get message point index
        # - note that this takes into account the point instance,
        #   so two points with the same content will not be considered the same
        # - it's a question if this a correct behavior or not :)
        self.assertEqual(way.get_message_point_index(point1), 0)
        self.assertEqual(way.get_message_point_index(point3), 2)
        foo_point = Point(lat=50.0, lon=50.0, elevation=300, message="foo")
        # foo_point has the same content as point1 but will be considered different
        self.assertIsNone(way.get_message_point_index(foo_point))
        # same thing for stuff that's not points
        self.assertIsNone(way.get_message_point_index(None))
        self.assertIsNone(way.get_message_point_index(1))
        self.assertIsNone(way.get_message_point_index(True))
        self.assertIsNone(way.get_message_point_index("bar"))
        self.assertIsNone(way.get_message_point_index([]))

    def set_message_point_test(self):
        """Test replacing message points already added to a Way."""
        way = Way()
        # add some message points
        point1 = Point(lat=50.0, lon=50.0, elevation=300.0, message="foo")
        point2 = Point(lat=75.0, lon=75.0, elevation=600.0, message="bar")
        point3 = Point(lat=100.0, lon=100.0, elevation=1200.0, message="baz")
        way.add_message_points([point1, point2, point3])
        self.assertEqual(way.get_message_point_by_index(0), point1)
        self.assertEqual(way.get_message_point_by_index(2), point3)

        # replace some of the points
        point11 = Point(lat=51.0, lon=51.0, elevation=301.0, message="foo1")
        point31 = Point(lat=101.0, lon=101.0, elevation=1201.0, message="baz1")
        way.set_message_point_by_index(0, point11)
        way.set_message_point_by_index(2, point31)

        # check the points have been replaced
        self.assertEqual(way.get_message_point_by_index(0), point11)
        self.assertEqual(way.get_message_point_by_index(2), point31)

        # some sanity checks
        self.assertEqual(way.message_point_count, 3)
        self.assertListEqual(way.message_points, [point11, point2, point31])
        self.assertListEqual(way.message_points_lle, [point11.getLLE(), point2.getLLE(), point31.getLLE()])
        lol_point = Point(lat=50.0, lon=50.0, elevation=300, message="lol")
        with self.assertRaises(IndexError):
            way.set_message_point_by_index(3, lol_point)
        with self.assertRaises(IndexError):
            way.set_message_point_by_index(-100, lol_point)
        with self.assertRaises(IndexError):
            way.set_message_point_by_index(100, lol_point)

    def radians_test(self):
        """Test that radians values for Way points are correct."""
        # create way with some regular points
        first = (0.0,0.0,0.0)
        second = (1.0, 1.0, 100.0)
        lle_list = [first, second]
        way = Way(points=lle_list)
        # check the radian output
        radians_list = [(0.0, 0.0, 0.0),
                        (0.017453292519943295, 0.017453292519943295, 100.0)]
        self.assertListEqual(way.points_radians_lle, radians_list)
        self.assertListEqual(way.points_radians_ll, list(map(lambda x: (x[0], x[1]), radians_list)))
        # add some more points
        way.add_point(Point(lat=3.0, lon=3.0, elevation=200.0))
        way.add_point_lle(5.0, 5.0, 300.0)
        radians_list.extend([(0.05235987755982989, 0.05235987755982989, 200.0),
                             (0.08726646259971647, 0.08726646259971647, 300.0)])
        # check again
        self.assertListEqual(way.points_radians_lle, radians_list)
        self.assertListEqual(way.points_radians_ll, list(map(lambda x: (x[0], x[1]), radians_list)))

    def get_closest_point_test(self):
        """Test the get-closest-point functions of the Way class."""
        # put some regular points to the way first
        first = (0.0,0.0,0.0)
        second = (1.0, 0.0,100.0)
        third = (2.0, 0.0, 200.0)
        lle_list = [first, second, third]
        way = Way(points=lle_list)
        # add some message points
        point1 = Point(lat=50.0, lon=0.0, elevation=300.0, message="foo")
        point2 = Point(lat=75.0, lon=0.0, elevation=600.0, message="bar")
        way.add_message_point(point1)
        way.add_message_point(point2)
        # get closest point
        result = way.get_closest_point(Point(lat=2.5, lon=0.0))
        self.assertEqual(result.getLLE(), third)
        # get closest message point
        result = way.get_closest_message_point(Point(lat=76.0, lon=0.0))
        self.assertEqual(result, point2)

    def clear_test(self):
        """Test if the clear() methods of the Way class works correctly."""
        # put some regular points to the way first
        first = (0.0,0.0,0.0)
        second = (1.0, 1.0,100.0)
        third = (2.0, 2.0, 200.0)
        lle_list = [first, second, third]
        way = Way(points=lle_list)
        # add some message points
        point1 = Point(lat=50.0, lon=50.0, elevation=300.0, message="foo")
        point2 = Point(lat=75.0, lon=75.0, elevation=600.0, message="bar")
        way.add_message_point(point1)
        way.add_message_point(point2)
        # check there are points & message points
        self.assertEqual(way.point_count, 3)
        self.assertEqual(way.message_point_count, 2)
        self.assertTrue(len(way.points_lle)>0)
        self.assertTrue(len(way.message_points)>0)
        self.assertTrue(len(way.message_points_lle)>0)
        # call the clear methods
        way.clear()
        way.clear_message_points()
        # check that the way is empty
        self.assertEqual(way.point_count, 0)
        self.assertEqual(way.message_point_count, 0)
        self.assertListEqual(way.points_lle, [])
        self.assertListEqual(way.message_points, [])
        self.assertListEqual(way.message_points_lle, [])




