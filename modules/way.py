"""a modRana class representing an unified tracklog or route"""
# -*- coding: utf-8 -*-
from __future__ import with_statement # for python 2.5
import csv
import os
import threading
import core.exceptions
import core.paths
from modules import geo
from modules.upoints import gpx
from point import Point

class TurnByTurnPoint(Point):
  def __init__(self, lat, lon, elevation=None, message=None, SSMLMessage=None):
    Point.__init__(self, lat, lon, elevation, message)
    self.currentDistance = None # in meters
    self.distanceFromStart = None # in meters
    self.visited = False
    self.SSMLMessage = None

  def getCurrentDistance(self):
    return self.currentDistance

  def setCurrentDistance(self, mDistance):
    self.currentDistance = mDistance

  def getDistanceFromStart(self):
    return self.distanceFromStart

  def setDistanceFromStart(self, distanceFromStart):
    self.distanceFromStart = distanceFromStart

  def getVisited(self):
    return self.visited

  def setVisited(self, value):
    self.visited = value

  def getSSMLMessage(self):
    return self.SSMLMessage

  def setSSMLMessage(self, message):
    self.SSMLMessage = message


class Way:
  """a segment of the way
      * Points denote the way
      * Message points are currently mainly used for t-b-t routing announcements
      * points can be returned either as Point objects or a lists of
        (lat,lon) tuples for the whole segment
      * by default, message points are stored and returned separately from non-message
      points (similar to trackpoints vs waypoints in GPX)
  """

  def __init__(self, points=[]):
    self.points = points # stored as LLE tuples
    self.pointsInRadians = None
    self.messagePoints = []
    self.messagePointsLLE = []
    self.length = None # in meters
    self.duration = None # in seconds
    self.pointsLock = threading.RLock()

    # caching
    self.dirty = False # signalizes that cached data needs to be updated
    # now update the cache
    self._updateCache()


  def getPointByID(self, index):
    p = self.points[index]
    (lat, lon, elevation) = (p[0], p[1], p[2])
    return Point(lat, lon, elevation)

  def getPointsLLE(self):
    """return the way points as LLE tuples"""
    return self.points

  def getPointsLLERadians(self, dropElevation=False):
    """return the way as LLE tuples in radians"""
    # do we have cached radians version of the LLE tuples ?
    if self.pointsInRadians is not None:
      return self.pointsInRadians
    else:
      radians = geo.lleTuples2radians(self.points, dropElevation)
      self.pointsInRadians = radians
      return radians

  def addPoint(self, point):
    lat, lon, elevation = point.getLLE()
    self.points.append((lat, lon, elevation))

  def addPointLLE(self, lat, lon, elevation=None):
    self.points.append((lat, lon, elevation))

  def getPointCount(self):
    return len(self.points)

  # Duration specifies how long it takes to travel a route
  # it can either come from logging (it took this many seconds
  # to record this way) or from routing (it is expected that
  # traveling this route with this travel mode takes this seconds)

  def getDuration(self, sDuration):
    self.duration = sDuration

  def setDuration(self, sDuration):
    return self.duration

    # * message points

  def _updateCache(self):
    """update the various caches"""

    # update message point LLE cache
    mpLLE = []
    for point in self.messagePoints:
      mpLLE.append(point.getLLE())
    self.messagePointsLLE = mpLLE

  def addMessagePoint(self, point):
    self.messagePoints.append(point)
    self._updateCache()

  def addMessagePoints(self, points):
    self.messagePoints.extend(points)
    self._updateCache()

  def setMessagePointByID(self, index, mPoint):
    self.messagePoints[index] = mPoint
    self._updateCache()

  def getMessagePointByID(self, index):
    return self.messagePoints[index]

  def getMessagePointID(self, point):
    """return the index of a given message point or None
    if the given point doesn't exist in the message point list"""
    try:
      return self.messagePoints.index(point)
    except ValueError:
      return None

  def getMessagePoints(self):
    """ return a list of message point objects"""
    return self.messagePoints

  def getMessagePointsLLE(self):
    """return list of message point LLE tuples"""
    return self.points

  def clearMessagePoints(self):
    """clear all message points"""
    self.messagePoints = []
    self._updateCache()

  def getMessagePoints(self):
    return self.messagePoints

  def getMessagePointsLLE(self):
    return self.messagePointsLLE


  def getMessagePointCount(self):
    return len(self.messagePoints)

  def getLength(self):
    """way length in meters"""
    return self.length

  def _setLength(self, mLength):
    """for use if the length on of the way is reliably known from external
    sources"""
    self.length = mLength


  # GPX export

  def saveToGPX(self, path, turns=False):
    """save way to GPX file
    points are saved as trackpoints,
    message points as routepoints with turn description in the <desc> field"""
    try: # first check if we cant open the file for writing
      f = open(path, "wb")
      # Handle trackpoints
      trackpoints = gpx.Trackpoints()
      # check for stored timestamps
      if self.points and len(self.points[0]) >= 4: # LLET
        trackpoints.append(
          map(lambda x:
          gpx.Trackpoint(x[0], x[1], None, None, x[2], x[3]),
            self.points)
        )

      else: # LLE
        trackpoints.append(
          map(lambda x:
          gpx.Trackpoint(x[0], x[1], None, None, x[2], None),
            self.points)
        )

      # Handle message points

      # TODO: find how to make a GPX trac with segments of different types
      # is it as easy just dumping the segment lists to Trackpoints ?

      # message is stored in <desc>
      messagePoints = self.getMessagePoints()
      index = 1
      mpCount = len(messagePoints)
      if turns: # message points contain Turn-By-Turn directions
        routepoints = gpx.Routepoints()
        for mp in messagePoints:
          if turns:
            name = "Turn %d/%d" % (index, mpCount)
          lat, lon, elev, message = mp.getLLEM()
          routepoints.append(gpx.Routepoint(lat, lon, name, message, elev, None))
          index += 1
        print('way: %d points, %d routepoints saved to %s in GPX format' % (path, len(trackpoints), len(routepoints)))
      else:
        waypoints = []
        for mp in messagePoints:
          if turns:
            name = "Turn %d/%d" % (index, mpCount)
          lat, lon, elev, message = mp.getLLEM()
          waypoints.append(gpx.Routepoint(lat, lon, name, message, elev, None))
          index += 1
        print('way: %d points, %d waypoints saved to %s in GPX format' % (len(trackpoints[0]), len(waypoints), path))

      # write the GPX tree to file
      # TODO: waypoints & routepoints support
      xmlTree = trackpoints.export_gpx_file()
      xmlTree.write(f)
      # close the file
      f.close()
      return True
    except Exception, e:
      print('way: saving to GPX format failed')
      print(e)
      return False


  # CSV  export

  def saveToCSV(self, path, append=False):
    """save all points to a CSV file
    NOTE: message points are not (yet) handled
    TODO: message point support"""
    timestamp = geo.timestampUTC()
    try:
      f = open(path, "wb")
      writer = csv.writer(f, dialect=csv.excel)
      points = self.getPointsLLE()
      for p in points:
        writer.writeRow(p[0], p[1], p[2], timestamp)
      f.close()
      print('way: %d points saved to %s as CSV' % (path, len(points)))
      return True
    except Exception, e:
      print('way: saving to CSV failed')
      print(e)
      return False

  def __str__(self):
    pCount = self.getPointCount()
    mpCount = self.getMessagePointCount()
    return "segment: %d points and %d message points" % (pCount, mpCount)


def fromGoogleDirectionsResult(gResult):
  """convert Google Directions result to a way object """
  leg = gResult['routes'][0]['legs'][0]
  steps = leg['steps']
#  points = leg['polyline']['points']


  points = _decodePolyline(gResult['routes'][0]['overview_polyline']['points'])
  # length of the route can computed from its metadata
  if 'distance' in leg: # this field might not be present
    mLength = leg['distance']['value']
  else:
    mLength = None
#  mLength += gResult['Directions']['Routes'][0]['Steps'][-1]["Distance"]["meters"]
  # the route also contains the expected duration in seconds
  if 'duration' in leg: # this field might not be present
    sDuration = leg['duration']['value']
  else:
    sDuration = None

  way = Way(points)
  way._setLength(mLength)
  way.setDuration(sDuration)
  messagePoints = []

#  mDistanceFromStart = gResult['Directions']['Routes'][0]['Steps'][-1]["Distance"]["meters"]
  mDistanceFromStart = 0
  #          # add and compute the distance from start
  #          step['mDistanceFromStart'] = mDistanceFromStart
  #          mDistanceFromLast = step["Distance"]["meters"]
  #          mDistanceFromStart = mDistanceFromStart + mDistanceFromLast

  for step in steps:
    # TODO: abbreviation filtering
    message = step['html_instructions']
    # as you can see, for some reason,
    # the coordinates in Google Directions steps are reversed:
    # (lon,lat,0)
    lat = step['start_location']['lat']
    lon = step['start_location']['lng']
    #TODO: end location ?
    point = TurnByTurnPoint(lat, lon, message=message)
    point.setDistanceFromStart(mDistanceFromStart)
    # store point to temporary list
    messagePoints.append(point)
    # update distance for next point
    mDistanceFromLast = step["distance"]['value']
    mDistanceFromStart = mDistanceFromStart + mDistanceFromLast

  way.addMessagePoints(messagePoints)
  return way

def fromGoogleDirectionsResultOld(gResult):
  """convert Google Directions result to a way object """
  steps = gResult['Directions']['Routes'][0]['Steps']
  points = _decodePolyline(gResult['Directions']['Polyline']['points'])
  # length of the route can computed from its metadata
  mLength = gResult['Directions']['Distance']['meters']
  mLength += gResult['Directions']['Routes'][0]['Steps'][-1]["Distance"]["meters"]
  # the route also contains the expected duration in seconds
  sDuration = gResult['Directions']['Duration']['seconds']

  way = Way(points)
  way._setLength(mLength)
  way.setDuration(sDuration)
  messagePoints = []

  mDistanceFromStart = gResult['Directions']['Routes'][0]['Steps'][-1]["Distance"]["meters"]
  #          # add and compute the distance from start
  #          step['mDistanceFromStart'] = mDistanceFromStart
  #          mDistanceFromLast = step["Distance"]["meters"]
  #          mDistanceFromStart = mDistanceFromStart + mDistanceFromLast

  for step in steps:
    # TODO: abbreviation filtering
    message = step['descriptionHtml']
    # as you can see, for some reason,
    # the coordinates in Google Directions steps are reversed:
    # (lon,lat,0)
    lat = step['Point']['coordinates'][1]
    lon = step['Point']['coordinates'][0]
    point = TurnByTurnPoint(lat, lon, message=message)
    point.setDistanceFromStart(mDistanceFromStart)
    # store point to temporary list
    messagePoints.append(point)
    # update distance for next point
    mDistanceFromLast = step["Distance"]["meters"]
    mDistanceFromStart = mDistanceFromStart + mDistanceFromLast

  way.addMessagePoints(messagePoints)
  return way

def fromMonavResult(result, getTurns=None):
  """convert route nodes from the Monav routing result"""
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

    way = Way(routePoints)
    way.setDuration(result.seconds)
    way._setLength(mLength)

    # was a directions generation method provided ?
    if getTurns:
      # generate directions
      messagePoints = getTurns(result)
      way.addMessagePoints(messagePoints)
    return way
  else:
    return None

def fromGPX(GPX):
  pass

def fromCSV(path, delimiter=',', fieldCount=None):
  """create a way object from a CSV file specified by path
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
  try:
    f = open(path, 'r')
  except IOError, e:
    if e.errno == 2:
      raise core.exceptions.FileNotFound
    elif e.errno == 13:
      raise core.exceptions.FileAccessPermissionDenied
    f.close()

  points = []

  reader = csv.reader(f, delimiter=delimiter)

  if fieldCount: # assume fixed field count
    try:
      if fieldCount == 2: # lat, lon
        points = map(lambda x: (x[0], x[1]), reader)
      elif fieldCount == 3: # lat, lon, elevation
        points = map(lambda x: (x[0], x[1], x[2]), reader)
      elif fieldCount == 4: # lat, lon, elevation, timestamp
        points = map(lambda x: (x[0], x[1], x[2], x[3]), reader)
      else:
        print("Way: wrong field count - use 2, 3 or 4")
        raise ValueError
    except Exception, e:
      print('Way: parsing CSV file at path: %s failed')
      print(e)
      f.close()
      return None
  else:
    parsingErrorCount = 0
    lineNumber = 1

    def eFloat(item):
      """"""
      if item: # 0 would still be '0' -> nonempty string
        try:
          return float(item)
        except Exception: # parsing error
          print("way: parsing elevation failed, data: ", item)
          print(e)
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
          print('Way: error, line %d has 1 or 0 fields, needs at least 2 (lat, lon):\n%r' % (reader.line_no, r))
          parsingErrorCount += 1
      except Exception, e:
        print('Way: parsing CSV line %d failed' % lineNumber)
        print(e)
        parsingErrorCount += 1
      lineNumber += 1

  # close the file
  f.close()
  print('Way: CSV file parsing finished, %d points added with %d errors' % (len(points), parsingErrorCount))
  return Way(points)


def fromHandmade(start, middlePoints, destination):
  """convert hand-made route data to a way """
  if start and destination:
    # route points & message points are generated at once
    # * empty string as message => no message point, just route point
    routePoints = [(start[0], start[1], None)]
    messagePoints = []
    mLength = 0 # in meters
    lastLat, lastLon = start[0], start[1]
    for point in middlePoints:
      lat, lon, elevation, message = point
      mLength+= geo.distance(lastLat, lastLon, lat, lon)*1000
      routePoints.append((lat, lon, elevation))
      if message != "": # is it a message point ?
        point = TurnByTurnPoint(lat, lon, elevation, message)
        point.setDistanceFromStart(mLength)
        messagePoints.append(point)
      lastLat, lastLon = lat, lon
    routePoints.append((destination[0], destination[1], None))
    way = Way(routePoints)
    way.addMessagePoints(messagePoints)
    # huge guestimation (avg speed 60 km/h = 16.7 m/s)
    seconds = mLength / 16.7
    way.setDuration(seconds)
    way._setLength(mLength)
    # done, return the result
    return way
  else:
    return None

  #point.setDistanceFromStart(mDistanceFromStart)

class AppendOnlyWay(Way):
  """a way subclass that is optimized for efficient incremental file storage
  -> points can be only appended or completely replaced, no insert support at he moment
  -> only CSV storage is supported at the moment
  -> call openCSV(path) to start incremental file storage
  -> call flush() if to write the points added since open* or last flush to disk
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
  -> if flush is called regularly (which is the expected behaviour when using this class), this should not be an issue

  """

  def __init__(self, points=[]):
    Way.__init__(self)

    self.points = [] # stored as (lat, lon, elevation, timestamp) tuples
    self.increment = [] # not yet saved increment, also LLET
    self.file = None
    self.filePath = None
    self.writer = None

    if points:
      with self.pointsLock:
        #mark all points added on startup with a single timestamp
        timestamp = geo.timestampUTC()
        # convert to LLET
        points = map(lambda x: (x[0], x[1], x[2], timestamp), points)

        # mark points as not yet saved
        self.increment = points
        # and also add to main point list
        self.points = points

  def getPointsLLE(self):
    # drop the timestamp
    return map(lambda x: (x[0], x[1], x[2]), self.points)

  def getPointsLLET(self):
    """returns all points in LLET format, both saved an not yet saved to storage"""
    return self.points

  def getPointCount(self):
    return len(self.points) + len(self.increment)

  def addPoint(self, point):
    with self.pointsLock:
      lat, lon, elevation = point.getLLE()
      self.points.append((lat, lon, elevation, geo.timestampUTC()))
      self.increment.append((lat, lon, elevation, geo.timestampUTC()))

  def addPointLLE(self, lat, lon, elevation):
    with self.pointsLock:
      self.points.append((lat, lon, elevation, geo.timestampUTC()))
      self.increment.append((lat, lon, elevation, geo.timestampUTC()))

  def addPointLLET(self, lat, lon, elevation, timestamp):
    with self.pointsLock:
      self.points.append((lat, lon, elevation, timestamp))
      self.increment.append((lat, lon, elevation, timestamp))

  def getFilePath(self):
    return self.filePath

  def startWritingCSV(self, path):
    try:
      self.file = open(path, "wb")
      self.writer = csv.writer(self.file)
      self.filePath = path
      # flush any pending points
      self.flush()
      print('AOWay: started writing to: %s' % path)
    except Exception, e:
      print('AOWay: opening CSV file for writing failed, path: %s' % path)
      print(e)
      self._cleanup() # revert to initial state
      return False

  def flush(self):
    """flush all points that are only in memory to storage"""
    # get the pointsLock, the current increment to local variable and clear the original
    # we release the lock afterwards so that other threads can start adding more points right away
    with self.pointsLock:
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
    print('AOWay: file closed: %s' % self.filePath)
    # cleanup
    self._cleanup()

  def deleteFile(self):
    """delete the currently open file"""
    path = self.filePath
    if self.file:
      try:
        self.close() # close it
        os.remove(path) # and delete it
      except Exception, e:
        print('AOWay: deleting currently open file failed')
        print(e)
    else:
      print("AOWay: can't delete current file - no file open")


  def _cleanup(self):
    self.file = None
    self.writer = None
    self.filePath = None
    self.increment = []


#from: http://seewah.blogspot.com/2009/11/gpolyline-decoding-in-python.html
def _decodePolyline(encoded):
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


  #class Ways:
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
  #      count+=segment.getPointCount()
  #    return "way: %d segments, %d points total" % (self.getSegmentCount(), count)