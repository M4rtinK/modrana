"""The universal class representing a point and derived classes"""

from core import constants
from core.singleton import modrana
from core.backports.six import u

import logging
log = logging.getLogger("core.point")

class Point(object):
    """A point"""

    def __init__(self, lat, lon, elevation=None, name=None, summary=None, message=None):
        self._lat = lat
        self._lon = lon
        self._elevation = elevation  # in meters
        self._name = name
        self._summary = summary
        self._message = message

    def __unicode__(self):
        if self.elevation is None:
            elev = "unknown"
        else:
            elev = "%f m" % self.elevation

        return '%f,%f elev: %s "%s:%s"' % (self.lat, self.lon, elev, self.name, self.summary)

    def __str__(self):
        if self.elevation is None:
            elev = "unknown"
        else:
            elev = "%f m" % self.elevation
        return '%f,%f elev: %s "%s:%s"' % (self.lat, self.lon, elev, self.name, self.summary)

    @property
    def name(self):
        if self._name is not None:
            return self._name
        elif self._message:
            return self._message.split('\n', 1)[0]
        else:
            return None

    @name.setter
    def name(self, value):
        """A very short name of the point"""
        self._name = value

    @property
    def summary(self):
        """A short one-line summary describing the point"""
        if self._summary is not None:
            return self._summary
        elif self._message:
            return self._message.split('\n', 1)[0]
        else:
            return ""

    @summary.setter
    def summary(self, value):
        self._summary = value

    @property
    def description(self):
        """Long, long-line & multiline point description"""
        return self._message

    @description.setter
    def description(self, value):
        self._message = value

    @property
    def lat(self):
        return self._lat

    @lat.setter
    def lat(self, latitude):
        self._lat = latitude

    @property
    def lon(self):
        return self._lon

    @lon.setter
    def lon(self, longitude):
        self._lon = longitude

    @property
    def elevation(self):
        return self._elevation

    @elevation.setter
    def elevation(self, elevation):
        self._elevation = elevation

    def getLL(self):
        return self.lat, self.lon

    def setLL(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def getLLE(self):
        return self.lat, self.lon, self.elevation

    def setLLE(self, lat, lon, elevation):
        self.lat = lat
        self.lon = lon
        self.elevation = elevation

    def getLLEM(self):
        return self.lat, self.lon, self.elevation, self._message

    def getAbstract(self):
        """A short single line point description"""
        if self.summary:
            return self.summary
        elif self._message:
            return self._message.split('\n', 1)[0]
        else:
            return "no abstract"

    def getUrls(self):
        """Get a list of (Url, Url description) tuples corresponding to the point"""
        return []


class Waypoint(Point):
    """A waypoint class to be mainly used as input for routing requests.

    At the moment basically just adds the additional heading property.
    """
    def __init__(self,  lat, lon, elevation=None, name=None, summary=None,
                 message=None, heading=None):
        Point.__init__(self, lat, lon, elevation=elevation, name=name,
                       summary=summary, message=message)
        self._heading = heading

    @property
    def heading(self):
        """Current heading in degrees from the north."""
        return self._heading

    @heading.setter
    def heading(self, new_heading):
        self._heading = new_heading


class POI(Point):
    """This class represents a POI"""

    def __init__(self, name, description, lat, lon, db_cat_id, db_poi_id=None):
        self.id = db_poi_id
        # this probably handles some Unicode encoding issues
        name = u('%s') % name
        description = u('%s') % description
        Point.__init__(self, lat, lon, name=name, message=description)
        self._db_category_index = db_cat_id

    def __str__(self):
        return "POI named: %s, lat,lon: %f,%f with id: %s" % (
            self.name,
            self.lon,
            self.lon,
            self.db_index
        )

    def __eq__(self, other):
        return self.db_index == other.db_index

    @property
    def db_index(self):
        return self.id

    @property
    def db_category_index(self):
        return self._db_category_index

    @db_category_index.setter
    def db_category_index(self, new_category_index):
        self._db_category_index = new_category_index

    def commit(self):
        """Store the current state of this POI object to the database"""
        storePOI = modrana.m.get('storePOI', None)
        if storePOI:
            storePOI.db.store_poi(self)
        else:
            log.error("can't commit %s to POI database: storePOI module missing", self)

    def showOnMap(self):
        """Recentre to this POI and show its marker and label"""
        modrana.sendMessage('mapView:recentre %f %f|showPOI:drawActivePOI|set:menu:None' %
                            (self.lat, self.lon))

    def routeFrom(self, fromWhere):
        """Route from somewhere to this POI"""
        if fromWhere == 'currentPosition': # route from current position to this POI
            pos = modrana.get('pos', None)
            if pos:
                (fromLat, fromLon) = pos
                # clear old route (if any) and route to the point
                modrana.sendMessage(
                    'route:clearRoute|md:route:route:type=ll2ll;fromLat=%f;fromLon=%f;toLat=%f;toLon=%f;' %
                    (fromLat, fromLon, self.lat, self.lon)
                )

class TurnByTurnPoint(Point):
    def __init__(self, lat, lon, elevation=None,
                 message=None, ssml_message=None,
                 icon=constants.DEFAULT_NAVIGATION_STEP_ICON):
        Point.__init__(self, lat, lon, elevation=elevation, message=message)
        self._current_distance = None # in meters
        self._distance_from_start = None # in meters
        self._visited = False
        self._ssml_message = ssml_message
        self._icon = icon

    @property
    def current_distance(self):
        """Current distance from the step in meters.

        :returns: distance from step in meters
        :rtype: int or None
        """
        return self._current_distance

    @current_distance.setter
    def current_distance(self, distance_in_meters):
        self._current_distance = distance_in_meters

    @property
    def distance_from_start(self):
        """Distance of the point from the start of the route in meters.

        :returns: distance from start of the route in meters
        :rtype: int or None
        """
        return self._distance_from_start

    @distance_from_start.setter
    def distance_from_start(self, distance_from_start):
        self._distance_from_start = distance_from_start

    @property
    def visited(self):
        """Has the point been visited ?

        :returns: True is the point has already been visited, False otherwise
        :rtype: bool
        """
        return self._visited

    @visited.setter
    def visited(self, value):
        self._visited = value

    @property
    def ssml_message(self):
        """SSML message for TTS corresponding to the turn.

        :returns: SSML message describing the turn
        :rtype: str
        """
        return self._ssml_message

    @ssml_message.setter
    def ssml_message(self, message):
        self._ssml_message = message

    @property
    def icon(self):
        """Icon id corresponding to the turn.

        :returns: turn icon id
        :rtype: str
        """
        return self._icon

    @property
    def llemi(self):
        """Latitude, longitude, elevation, message, icon id tuple."""
        return self.lat, self.lon, self.elevation, self._message, self._icon
