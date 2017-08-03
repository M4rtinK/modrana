"""a modRana class representing an unified tracklog or route"""
# -*- coding: utf-8 -*-
from __future__ import with_statement # for python 2.5
import csv
import os
import threading
import itertools
import core.exceptions
import core.paths
from core import geo
from upoints import gpx
from core.point import Point, TurnByTurnPoint
from core.instructions_generator import detect_monav_turns

import logging
log = logging.getLogger("core.way")
aoLog = logging.getLogger("core.way.ao")

class Way(object):
    """A segment of a way
        * points denote the way
        * message points are currently mainly used for t-b-t routing announcements
        * points can be returned either as Point objects or a lists of
          (lat,lon) tuples for the whole segment
        * by default, message points are stored and returned separately from non-message
          points (similar to trackpoints vs waypoints in GPX)
    """

    def __init__(self, points=None):
        if not points: points = []
        self._points = points # stored as LLE tuples
        self._points_in_radians = None
        self._message_points = []
        self._message_points_lle = []
        self._length = None # in meters
        self._duration = None # in seconds
        self._points_lock = threading.RLock()

        # caching
        self._cache_dirty = False # signalizes that cached data needs to be updated
        # now update the cache
        self._update_cache()

    def get_point_by_index(self, index):
        p = self._points[index]
        (lat, lon, elevation) = (p[0], p[1], p[2])
        return Point(lat, lon, elevation)

    @property
    def points_lle(self):
        """Return the way points as LLE tuples"""
        return self._points

    def get_points_lle_radians(self, drop_elevation=False):
        """Return the way as LLE tuples in radians"""
        # do we have cached radians version of the LLE tuples ?
        if self._points_in_radians is not None:
            return self._points_in_radians
        else:
            radians = geo.lleTuples2radians(self._points, drop_elevation)
            self._points_in_radians = radians
            return radians

    def add_point(self, point):
        lat, lon, elevation = point.getLLE()
        self._points.append((lat, lon, elevation))

    def add_point_lle(self, lat, lon, elevation=None):
        self._points.append((lat, lon, elevation))

    @property
    def point_count(self):
        return len(self._points)

    # Duration specifies how long it takes to travel a route
    # it can either come from logging (it took this many seconds
    # to record this way) or from routing (it is expected that
    # traveling this route with this travel mode takes this seconds)

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, seconds_duration):
        self._duration = seconds_duration

        # * message points

    def _update_cache(self):
        """Update the various caches"""

        # update message point LLE cache
        mpLLE = []
        for point in self._message_points:
            mpLLE.append(point.getLLE())
        self._message_points_lle = mpLLE

    def add_message_point(self, point):
        self._message_points.append(point)
        self._update_cache()

    def add_message_points(self, points):
        self._message_points.extend(points)
        self._update_cache()

    def set_message_point_by_index(self, index, mPoint):
        self._message_points[index] = mPoint
        self._update_cache()

    def get_message_point_by_index(self, index):
        return self._message_points[index]

    def get_message_point_index(self, point):
        """Return the index of a given message point or None
        if the given point doesn't exist in the message point list
        """
        try:
            return self._message_points.index(point)
        except ValueError:
            return None

    @property
    def message_points(self):
        """Return a list of message point objects"""
        return self._message_points

    @property
    def message_points_lle(self):
        """Return a list of message point LLE tuples"""
        return self._message_points_lle

    def clear_message_points(self):
        """Clear all message points"""
        self._message_points = []
        self._update_cache()

    @property
    def message_point_count(self):
        return len(self._message_points)

    @property
    def length(self):
        """Way length in meters"""
        return self._length

    def _setLength(self, mLength):
        """For use if the length on of the way is reliably known from
           external sources"""
        self._length = mLength


    # GPX export

    def saveToGPX(self, path, turns=False):
        """Save way to GPX file
        points are saved as trackpoints,
        message points as routepoints with turn description in the <desc> field
        """
        try: # first check if we cant open the file for writing
            f = open(path, "wb")
            # Handle trackpoints
            trackpoints = gpx.Trackpoints()
            # check for stored timestamps
            if self._points and len(self._points[0]) >= 4: # LLET
                trackpoints.append(
                    [gpx.Trackpoint(x[0], x[1], None, None, x[2], x[3]) for x in self._points]
                )

            else: # LLE
                trackpoints.append(
                    [gpx.Trackpoint(x[0], x[1], None, None, x[2], None) for x in self._points]
                )

            # Handle message points

            # TODO: find how to make a GPX trac with segments of different types
            # is it as easy just dumping the segment lists to Trackpoints ?

            # message is stored in <desc>
            messagePoints = self.message_points
            index = 1
            mpCount = len(messagePoints)
            if turns: # message points contain Turn-By-Turn directions
                routepoints = gpx.Routepoints()
                for mp in messagePoints:
                    name = ""
                    if turns:
                        name = "Turn %d/%d" % (index, mpCount)
                    lat, lon, elev, message = mp.getLLEM()
                    routepoints.append(gpx.Routepoint(lat, lon, name, message, elev, None))
                    index += 1
                log.info('%d points, %d routepoints saved to %s in GPX format',
                         path, len(trackpoints), len(routepoints))
            else:
                waypoints = []
                for mp in messagePoints:
                    name = ""
                    if turns:
                        name = "Turn %d/%d" % (index, mpCount)
                    lat, lon, elev, message = mp.getLLEM()
                    waypoints.append(gpx.Routepoint(lat, lon, name, message, elev, None))
                    index += 1
                log.info('%d points, %d waypoints saved to %s in GPX format',
                         len(trackpoints[0]), len(waypoints), path)

            # write the GPX tree to file
            # TODO: waypoints & routepoints support
            xmlTree = trackpoints.export_gpx_file()
            xmlTree.write(f)
            # close the file
            f.close()
            return True
        except Exception:
            log.exception('saving to GPX format failed')
            return False

    # CSV  export

    def saveToCSV(self, path, append=False):
        """Save all points to a CSV file
        NOTE: message points are not (yet) handled
        TODO: message point support
        """
        timestamp = geo.timestampUTC()
        try:
            f = open(path, "w")
            writer = csv.writer(f, dialect=csv.excel)
            points = self.points_lle
            for p in points:
                writer.writeRow(p[0], p[1], p[2], timestamp)
            f.close()
            log.info('%d points saved to %s as CSV', path, len(points))
            return True
        except Exception:
            log.exception('saving to CSV failed')
            return False

    def __str__(self):
        pCount = self.point_count
        mpCount = self.message_point_count
        return "segment: %d points and %d message points" % (pCount, mpCount)

    @classmethod
    def from_google_directions_result(cls, gResult):
        """Convert Google Directions result to a way object"""
        leg = gResult['routes'][0]['legs'][0]
        steps = leg['steps']

        points = decode_polyline(gResult['routes'][0]['overview_polyline']['points'])
        # length of the route can computed from its metadata
        if 'distance' in leg: # this field might not be present
            mLength = leg['distance']['value']
        else:
            mLength = None
        # the route also contains the expected duration in seconds
        if 'duration' in leg: # this field might not be present
            sDuration = leg['duration']['value']
        else:
            sDuration = None

        way = cls(points)
        way._setLength(mLength)
        way.duration = sDuration
        messagePoints = []

        mDistanceFromStart = 0

        for step in steps:
            # TODO: abbreviation filtering
            message = step['html_instructions']
            # as you can see, for some reason,
            # the coordinates in Google Directions steps are reversed:
            lat = step['start_location']['lat']
            lon = step['start_location']['lng']
            #TODO: end location ?
            point = TurnByTurnPoint(lat, lon, message=message)
            point.distanceFromStart = mDistanceFromStart
            # store point to temporary list
            messagePoints.append(point)
            # update distance for next point
            mDistanceFromLast = step["distance"]['value']
            mDistanceFromStart = mDistanceFromStart + mDistanceFromLast

        way.add_message_points(messagePoints)
        return way

    @classmethod
    def from_monav_result(cls, result):
        """Convert route nodes from the Monav routing result"""
        # to (lat, lon) tuples
        if result:
            # route points
            routePoints = []
            mLength = 0 # in meters
            if result.nodes:
                firstNode = result.nodes[0]
                prevLat, prevLon = firstNode.latitude, firstNode.longitude
                # there is one from first to first calculation on start,
                # but as it should return 0, it should not be an issue
                for node in result.nodes:
                    routePoints.append((node.latitude, node.longitude, None))
                    mLength += geo.distance(prevLat, prevLon, node.latitude, node.longitude) * 1000
                    prevLat, prevLon = node.latitude, node.longitude

            way = cls(routePoints)
            way.duration = result.seconds
            way._setLength(mLength)

            # detect turns
            messagePoints = detect_monav_turns(result)
            way.add_message_points(messagePoints)
            return way
        else:
            return None

    @classmethod
    def from_gpx(cls, GPX):
        """Create a way from a GPX file"""
        #TODO: implement this
        pass

    @classmethod
    def from_csv(cls, path, delimiter=',', fieldCount=None):
        """Create a way object from a CSV file specified by path
        Assumed field order:
        lat,lon,elevation,timestamp

        If the fieldCount parameter is set, modRana assumes that the file has exactly the provided number
        of fields. As a result, content of any additional fields on a line will be dropped and
        if any line has less fields than fieldCount, parsing will fail.

       If the fieldCount parameter is not set, modRana checks the field count for every filed and tries to get usable
        data from it. Lines that fail to parse (have too 0 or 1 fields or fail at float parsing) are dropped. In this mode,
        a list of LLET tuples is returned.

        TODO: some range checks ?
        """
        f = None
        try:
            f = open(path, 'r')
        except IOError:
            import sys
            e = sys.exc_info()[1]
            if e.errno == 2:
                raise core.exceptions.FileNotFound
            elif e.errno == 13:
                raise core.exceptions.FileAccessPermissionDenied
            if f:
                f.close()

        points = []
        parsingErrorCount = 0

        reader = csv.reader(f, delimiter=delimiter)

        if fieldCount:  # assume fixed field count
            try:
                if fieldCount == 2: # lat, lon
                    points = [(x[0], x[1]) for x in reader]
                elif fieldCount == 3: # lat, lon, elevation
                    points = [(x[0], x[1], x[2]) for x in reader]
                elif fieldCount == 4: # lat, lon, elevation, timestamp
                    points = [(x[0], x[1], x[2], x[3]) for x in reader]
                else:
                    log.error("wrong field count - use 2, 3 or 4")
                    raise ValueError
            except Exception:
                log.exception('parsing CSV file at path: %s failed')
                f.close()
                return None
        else:
            parsingErrorCount = 0
            lineNumber = 1

            def eFloat(item):
                if item:  # 0 would still be '0' -> nonempty string
                    try:
                        return float(item)
                    except Exception:
                        log.error("parsing elevation failed, data:")
                        log.error(item)
                        log.exception()
                        return None
                else:
                    return None

            for r in reader:
                fields = len(r)
                try:
                    # float vs mFloat
                    #
                    # we really need lat & lon, but can live with missing elevation
                    #
                    # so we use float far lat and lon
                    # (which means that the line will error out if lat or lon
                    # is missing or corrupted)
                    # but use eFloat for elevation (we can live with missing elevation)
                    if fields >= 4:
                        points.append((float(r[0]), float(r[1]), eFloat(r[2]), r[3]))
                    elif fields == 3:
                        points.append((float(r[0]), float(r[1]), eFloat(r[2]), None))
                    elif fields == 2:
                        points.append((float(r[0]), float(r[1]), None, None))
                    else:
                        log.error('line %d has 1 or 0 fields, needs at least 2 (lat, lon):\n%r',
                              reader.line_no, r)
                        parsingErrorCount += 1
                except Exception:
                    log.exception('parsing CSV line %d failed', lineNumber)
                    parsingErrorCount += 1
                lineNumber += 1

        # close the file
        f.close()
        log.info('CSV file parsing finished, %d points added with %d errors',
                 len(points), parsingErrorCount)
        return cls(points)

    @classmethod
    def from_handmade(cls, start, middlePoints, destination):
        """Convert hand-made route data to a way """
        if start and destination:
            # route points & message points are generated at once
            # * empty string as message => no message point, just route point
            routePoints = [(start[0], start[1], None)]
            messagePoints = []
            mLength = 0 # in meters
            lastLat, lastLon = start[0], start[1]
            for point in middlePoints:
                lat, lon, elevation, message = point
                mLength += geo.distance(lastLat, lastLon, lat, lon) * 1000
                routePoints.append((lat, lon, elevation))
                if message != "": # is it a message point ?
                    point = TurnByTurnPoint(lat, lon, elevation, message)
                    point.distanceFromStart = mLength
                    messagePoints.append(point)
                lastLat, lastLon = lat, lon
            routePoints.append((destination[0], destination[1], None))
            way = cls(routePoints)
            way.add_message_points(messagePoints)
            # huge guestimation (avg speed 60 km/h = 16.7 m/s)
            seconds = mLength / 16.7
            way.duration = seconds
            way._setLength(mLength)
            # done, return the result
            return way
        else:
            return None

    @classmethod
    def from_osm_scout_json(cls, result):
        """Convert OSM Scout Server routig result json to a way"""
        if result:
            routePoints = []
            # get route as (lat, lon, None)
            route_lle_tuples = list(itertools.zip_longest(result["lat"], result["lng"], [None]))
            # create a way from the lle tuples
            way = cls(route_lle_tuples)

            way.duration = result["summary"]["time"]
            way._setLength(result["summary"]["length"])

            # get turns from the json result
            turns = []
            for maneuver in result.get("maneuvers", []):
                lat = maneuver["lat"]
                lon = maneuver["lng"]
                description = maneuver.get("verbal_pre_transition_instruction", "")
                turns.append(TurnByTurnPoint(lat, lon, message=description))
            way.add_message_points(turns)
            return way
        else:
            return None

    @classmethod
    def from_valhalla(cls, result):
        """Convert Valhalla routing result json to a way"""
        if result:
            route = []
            turns = []
            for leg in result['trip']['legs']:
                poly = decode_valhalla(leg['shape'])

                mans = []
                for m in leg['maneuvers']:
                    mans.append( TurnByTurnPoint(poly[m['begin_shape_index']][0],
                                                 poly[m['begin_shape_index']][1],
                                                 message=m['instruction']) )
                    
                route.extend( poly )
                turns.extend( mans )
                
            way = cls(route)
            
            way.duration = result['trip']['summary']['time']
            way._setLength(result['trip']["summary"]["length"])
            
            way.add_message_points(turns)
            return way
        else:
            return None
        
class AppendOnlyWay(Way):
    """A way subclass that is optimized for efficient incremental file storage
    -> points can be only appended or completely replaced, no insert support at he moment
    -> only CSV storage is supported at the moment
    -> call openCSV(path) to start incremental file storage
    -> call flush() if to write the points added since openCSV() or last flush to disk
    -> call close() once you are finished - this flushes any remaining points to disk
       and closes the file
    NOTE: this subclass also records per-point timestamps when points are added and these timestamps
    are stored in the output file

    Point storage & point appending
    -> points are added both to the main point list and the increment temporary list
    -> on every flush, the increment list is added to the file in storage and cleared
    -> like this, we don't need to combine the two lists when we need to return all points
    -> only possible downside is duplicate space needed for the points if flush is never called,
       as the same points would be stored both in points and increment
    -> if flush is called regularly (which is the expected behaviour when using this class),
       this should not be an issue
    """

    def __init__(self, points=None):
        if not points: points = []
        Way.__init__(self)

        self._points = [] # stored as (lat, lon, elevation, timestamp) tuples
        self.increment = [] # not yet saved increment, also LLET
        self.file = None
        self.filePath = None
        self.writer = None

        if points:
            with self._points_lock:
                # mark all points added on startup with a single timestamp
                timestamp = geo.timestampUTC()
                # convert to LLET
                points = [(x[0], x[1], x[2], timestamp) for x in points]

                # mark points as not yet saved
                self.increment = points
                # and also add to main point list
                self._points = points

    @property
    def points_lle(self):
        # drop the timestamp
        return [(x[0], x[1], x[2]) for x in self._points]

    @property
    def points_llet(self):
        """returns all points in LLET format, both saved an not yet saved to storage"""
        return self._points

    @property
    def point_count(self):
        return len(self._points)

    def add_point(self, point):
        with self._points_lock:
            lat, lon, elevation = point.getLLE()
            self._points.append((lat, lon, elevation, geo.timestampUTC()))
            self.increment.append((lat, lon, elevation, geo.timestampUTC()))

    def add_point_lle(self, lat, lon, elevation=None):
        with self._points_lock:
            self._points.append((lat, lon, elevation, geo.timestampUTC()))
            self.increment.append((lat, lon, elevation, geo.timestampUTC()))

    def add_point_llet(self, lat, lon, elevation, timestamp):
        with self._points_lock:
            self._points.append((lat, lon, elevation, timestamp))
            self.increment.append((lat, lon, elevation, timestamp))

    @property
    def file_path(self):
        return self.filePath

    def start_writing_csv(self, path):
        try:
            self.file = open(path, "w")
            self.writer = csv.writer(self.file)
            self.filePath = path
            # flush any pending points
            self.flush()
            aoLog.info('started writing to: %s' % path)
        except Exception:
            aoLog.exception('opening CSV file for writing failed, path: %s', path)
            self._cleanup() # revert to initial state
            return False

    def flush(self):
        """Flush all points that are only in memory to storage"""
        # get the pointsLock, the current increment to local variable and clear the original
        # we release the lock afterwards so that other threads can start adding more points right away
        with self._points_lock:
            increment = self.increment
            self.increment = []
            # write the rows
        self.writer.writerows(increment)
        # make sure it actually gets written to storage
        self.file.flush()
        os.fsync(self.file.fileno())

    def close(self):
        # save any increments
        if self.increment:
            self.flush()
            # close the file
        self.file.close()
        aoLog.info('file closed: %s', self.filePath)
        # cleanup
        self._cleanup()

    def delete_file(self):
        """Delete the currently open file"""
        path = self.filePath
        if self.file:
            try:
                self.close()  # close it
                os.remove(path)  # and delete it
            except Exception:
                aoLog.exception('deleting currently open file failed')
        else:
            aoLog.error("can't delete current file - no file open")

    def _cleanup(self):
        self.file = None
        self.writer = None
        self.filePath = None
        self.increment = []


#from: http://seewah.blogspot.com/2009/11/gpolyline-decoding-in-python.html
def decode_polyline(encoded):
    """Decodes a polyline that was encoded using the Google Maps method.

    See http://code.google.com/apis/maps/documentation/polylinealgorithm.html

    This is a straightforward Python port of Mark McClure's JavaScript polyline decoder
    (http://facstaff.unca.edu/mcmcclur/GoogleMaps/EncodePolyline/decode.js)
    and Peter Chng's PHP polyline decode
    (http://unitstep.net/blog/2008/08/02/decoding-google-maps-encoded-polylines-using-php/)
    """

    encoded_len = len(encoded)
    index = 0
    array = []
    lat = 0
    lng = 0

    while index < encoded_len:
        b = 0
        shift = 0
        result = 0

        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break

        dLat = ~(result >> 1) if result & 1 else result >> 1
        lat += dLat

        shift = 0
        result = 0

        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break

        dLng = ~(result >> 1) if result & 1 else result >> 1
        lng += dLng

        # append empty width for LLE tuple compatibility
        array.append((lat * 1e-5, lng * 1e-5, None))

    return array

def decode_valhalla(encoded):
    """ Decode polyline encoded by Valhalla

    Decoder taken from https://mapzen.com/documentation/mobility/decoding/
    """
    #six degrees of precision in valhalla
    inv = 1.0 / 1e6;
    decoded = []
    previous = [0,0]
    i = 0
    #for each byte
    while i < len(encoded):
        #for each coord (lat, lon)
        ll = [0,0]
        for j in [0, 1]:
            shift = 0
            byte = 0x20
            #keep decoding bytes until you have this coord
            while byte >= 0x20:
                byte = ord(encoded[i]) - 63
                i += 1
                ll[j] |= (byte & 0x1f) << shift
                shift += 5
            #get the final value adding the previous offset and remember it for the next
            ll[j] = previous[j] + (~(ll[j] >> 1) if ll[j] & 1 else (ll[j] >> 1))
            previous[j] = ll[j]

        # scale by the precision and add as lat,lon. None added for
        # LLE tuple compatibility
        decoded.append((float('%.6f' % (ll[0] * inv)), float('%.6f' % (ll[1] * inv)), None))
    #hand back the list of coordinates
    return decoded


    #class Ways(object):
    #  """a way consisting of one or more segments"""
    #  def __init__(self):
    #    self.segments = []
    #
    #  def addSegment(self, segment):
    #    """add a segment"""
    #    self.segments.append(segment)
    #
    #  def getSegmentByID(self, index):
    #    return self.segments[index]
    #
    #  def getSegmentCount(self):
    #    return len(self.segments)
    #
    #  def __str__(self):
    #    """textual state description"""
    #    count = 0
    #    for segment in self.segments:
    #      count+=segment.point_count
    #    return "way: %d segments, %d points total" % (self.getSegmentCount(), count)
