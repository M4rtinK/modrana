import math

"""Polygon intersection classes - SOURCE: http://gpwiki.org/index.php/Physics:2D_Physics_Engine:Intersection_Detection"""


class Vector(object):
    """Basic vector implementation"""

    def __init__(self, x, y):
        self.x, self.y = x, y

    def dot(self, other):
        """Returns the dot product of self and other (Vector)"""
        return self.x * other.x + self.y * other.y

    def __add__(self, other): # overloads vec1+vec2
        return Vector(self.x + other.x, self.y + other.y)

    def __neg__(self): # overloads -vec
        return Vector(-self.x, -self.y)

    def __sub__(self, other): # overloads vec1-vec2
        return -other + self

    def __mul__(self, scalar): # overloads vec*scalar
        return Vector(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__ # overloads scalar*vec

    def __div__(self, scalar): # overloads vec/scalar
        return 1.0 / scalar * self

    def magnitude(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalize(self):
        """Returns this vector's unit vector (vector of
        magnitude 1 in the same direction)"""
        inverse_magnitude = 1.0 / self.magnitude()
        return Vector(self.x * inverse_magnitude, self.y * inverse_magnitude)

    def perpendicular(self):
        """Returns a vector perpendicular to self"""
        return Vector(-self.y, self.x)


class Projection(object):
    """A projection (1d line segment)"""

    def __init__(self, min, max):
        self.min, self.max = min, max

    def intersects(self, other):
        """returns whether or not self and other intersect"""
        return self.max > other.min and other.max > self.min


class Polygon(object):
    def __init__(self, points):
        """points is a list of Vectors"""
        self.points = points

        # Build a list of the edge vectors
        self.edges = []
        for i in range(len(points)): # equal to Java's for(int i=0; i<points.length; i++)
            point = points[i]
            next_point = points[(i + 1) % len(points)]
            self.edges.append(next_point - point)

    def project_to_axis(self, axis):
        """axis is the unit vector (vector of magnitude 1) to project the polygon onto"""
        projected_points = []
        for point in self.points:
            # Project point onto axis using the dot operator
            projected_points.append(point.dot(axis))
        return Projection(min(projected_points), max(projected_points))

    def intersects(self, other):
        """returns whether or not two polygons intersect"""
        # Create a list of both polygons' edges
        edges = []
        edges.extend(self.edges)
        edges.extend(other.edges)

        for edge in edges:
            axis = edge.normalize().perpendicular() # Create the separating axis (see diagrams)

            # Project each to the axis
            self_projection = self.project_to_axis(axis)
            other_projection = other.project_to_axis(axis)

            # If the projections don't intersect, the polygons don't intersect
            if not self_projection.intersects(other_projection):
                return False

        # The projections intersect on all axes, so the polygons are intersecting
        return True


"""Point and Rectangle classes.

This code is in the public domain.

Point  -- point with (x,y) coordinates
Rect  -- two points, forming a rectangle

SOURCE: http://wiki.python.org/moin/PointsAndRectangles
"""


class Point(object):
    """A point identified by (x,y) coordinates.

    supports: +, -, *, /, str, repr

    length  -- calculate length of vector to point from origin
    distance_to  -- calculate distance between two points
    as_tuple  -- construct tuple (x,y)
    clone  -- construct a duplicate
    integerize  -- convert x & y to integers
    floatize  -- convert x & y to floats
    move_to  -- reset x & y
    slide  -- move (in place) +dx, +dy, as spec'd by point
    slide_xy  -- move (in place) +dx, +dy
    rotate  -- rotate around the origin
    rotate_about  -- rotate around another point
    """

    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def __add__(self, p):
        """Point(x1+x2, y1+y2)"""
        return Point(self.x + p.x, self.y + p.y)

    def __sub__(self, p):
        """Point(x1-x2, y1-y2)"""
        return Point(self.x - p.x, self.y - p.y)

    def __mul__(self, scalar):
        """Point(x1*x2, y1*y2)"""
        return Point(self.x * scalar, self.y * scalar)

    def __div__(self, scalar):
        """Point(x1/x2, y1/y2)"""
        return Point(self.x / scalar, self.y / scalar)

    def __str__(self):
        return "(%s, %s)" % (self.x, self.y)

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self.x, self.y)

    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def distance_to(self, p):
        """Calculate the distance between two points."""
        return (self - p).length()

    def as_tuple(self):
        """(x, y)"""
        return (self.x, self.y)

    def clone(self):
        """Return a full copy of this point."""
        return Point(self.x, self.y)

    def integerize(self):
        """Convert co-ordinate values to integers."""
        self.x = int(self.x)
        self.y = int(self.y)

    def floatize(self):
        """Convert co-ordinate values to floats."""
        self.x = float(self.x)
        self.y = float(self.y)

    def move_to(self, x, y):
        """Reset x & y coordinates."""
        self.x = x
        self.y = y

    def slide(self, p):
        '''Move to new (x+dx,y+dy).

        Can anyone think up a better name for this function?
        slide? shift? delta? move_by?
        '''
        self.x = self.x + p.x
        self.y = self.y + p.y

    def slide_xy(self, dx, dy):
        '''Move to new (x+dx,y+dy).

        Can anyone think up a better name for this function?
        slide? shift? delta? move_by?
        '''
        self.x = self.x + dx
        self.y = self.y + dy

    def rotate(self, rad):
        """Rotate counter-clockwise by rad radians.

        Positive y goes *up,* as in traditional mathematics.

        Interestingly, you can use this in y-down computer graphics, if
        you just remember that it turns clockwise, rather than
        counter-clockwise.

        The new position is returned as a new Point.
        """
        s, c = [f(rad) for f in (math.sin, math.cos)]
        x, y = (c * self.x - s * self.y, s * self.x + c * self.y)
        #        return Point(x,y)
        self.x = x
        self.y = y
        return self

    def rotate_about(self, p, theta):
        """Rotate counter-clockwise around a point, by theta degrees.

        Positive y goes *up,* as in traditional mathematics.

        The new position is returned as a new Point.
        """
        result = self.clone()
        result.slide_xy(-p.x, -p.y)
        result.rotate(theta)
        result.slide_xy(p.x, p.y)
        return result


class Rect(object):
    """A rectangle identified by two points.

    The rectangle stores left, top, right, and bottom values.

    Coordinates are based on screen coordinates.

    origin                               top
       +-----> x increases                |
       |                           left  -+-  right
       v                                  |
    y increases                         bottom

    set_points  -- reset rectangle coordinates
    contains  -- is a point inside?
    overlaps  -- does a rectangle overlap?
    top_left  -- get top-left corner
    bottom_right  -- get bottom-right corner
    expanded_by  -- grow (or shrink)
    """

    def __init__(self, pt1, pt2):
        """Initialize a rectangle from two points."""
        self.set_points(pt1, pt2)

    def set_points(self, pt1, pt2):
        """Reset the rectangle coordinates."""
        (x1, y1) = pt1.as_tuple()
        (x2, y2) = pt2.as_tuple()
        self.left = min(x1, x2)
        self.top = min(y1, y2)
        self.right = max(x1, x2)
        self.bottom = max(y1, y2)

    def contains(self, pt):
        """Return true if a point is inside the rectangle."""
        x, y = pt.as_tuple()
        return (self.left <= x <= self.right and
                self.top <= y <= self.bottom)

    def overlaps(self, other):
        """Return true if a rectangle overlaps this rectangle."""
        return (self.right > other.left and self.left < other.right and
                self.top < other.bottom and self.bottom > other.top)

    def top_left(self):
        """Return the top-left corner as a Point."""
        return Point(self.left, self.top)

    def bottom_right(self):
        """Return the bottom-right corner as a Point."""
        return Point(self.right, self.bottom)

    def expanded_by(self, n):
        """Return a rectangle with extended borders.

        Create a new rectangle that is wider and taller than the
        immediate one. All sides are extended by "n" points.
        """
        p1 = Point(self.left - n, self.top - n)
        p2 = Point(self.right + n, self.bottom + n)
        return Rect(p1, p2)

    def rotate(self, rad):
        """rotate around rectangle center"""
        # get center point
        w = self.right - self.right
        h = self.top - self.bottom
        centreX = w / 2.0
        centreY = h / 2.0
        # rotate
        self.rotate_around_xy(centreX, centreY, rad)

    def rotate_around(self, p, rad):
        """rotate around a point"""
        (x, y) = (p.x, p.y)
        self.rotate_around_xy(x, y, rad)

    def rotate_around_xy(self, x, y, rad):
        """rotate around x,y coordinates"""
        (x1, y1) = (self.left, self.top)
        (x2, y2) = (self.right, self.bottom)
        # rottate the points
        (x1, y1) = self._rotate_point_around(x1, y1, x, y, rad)
        (x2, y2) = self._rotate_point_around(x2, y2, x, y, rad)
        # update coordinates
        pt1 = Point(x1, y1)
        pt2 = Point(x2, y2)
        self.set_points(pt1, pt2)

    def _rotate_point_around(self, x, y, centerX, centerY, rad):
        # get coordinates relative to center
        dx = x - centerX
        dy = y - centerY
        # calculate angle and distance
        a = math.atan2(dy, dx)
        dist = math.sqrt(dx * dx + dy * dy)
        # calculate new angle
        a2 = a + rad
        # calculate new coordinates
        dx2 = math.cos(a2) * dist
        dy2 = math.sin(a2) * dist
        # return coordinates relative to top left corner
        return (dx2 + centerX, dy2 + centerY)


    def __str__(self):
        return "<Rect (%s,%s)-(%s,%s)>" % (self.left, self.top,
                                           self.right, self.bottom)

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__,
                               Point(self.left, self.top),
                               Point(self.right, self.bottom))

                    
