"""a modRana class representing an unified tracklog or route"""
# -*- coding: utf-8 -*-
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
    self.points = points
    self.messagePoints = []
    self.messagePointsLLE = []
    self.length = None # in meters
    # caching
    self.dirty = False # signalizes that cached data needs to be updated
    # now update the cache
    self._updateCache()

  def getPointByID(self, index):
    self.points[index]

  def getPointCount(self):
    return len(self.points)

    # * message points

  def _updateCache(self):
    """update the various caches"""

    # update message point LLE cache
    mpLLE = []
    for point in self.messagePoints:
      mpLLE.append(point.getLLE())
    self.messagePointsLLE = mpLLE


#    messagePoints = []
#    for point in self.points:
#      if point.getMessage() is None:
#        messagePoints.append(point)


  def addMessagePoint(self, point):
    self.messagePoints.append(point)
    self._updateCache()

  def addMessagePoints(self, points):
    self.messagePoints.extend(points)
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

  def getLength(self):
    """way length in meters"""
    return self.length

  def _setLength(self, mLength):
    """for use if the length on of the way is reliably known from external
    sources"""
    self.length = mLength

  def getMessagePoints(self):
    return self.messagePoints

  def getMessagePointsLLE(self):
    return self.messagePointsLLE

  def getMessagePointCount(self):
    return len(self.messagePoints)

  def __str__(self):
    pCount = self.getPointCount()
    mpCount = self.getMessagePointCount()
    return "segment: %d points and %d message points" % (pCount, mpCount)

def fromGoogleDirectionsResult(gResult):
  steps = gResult['Directions']['Routes'][0]['Steps']
  points = _decodePolyline(gResult['Directions']['Polyline']['points'])
  # length of the route can computed from its metadata

  print gResult

  mLength = gResult['Directions']['Distance']['meters']
  mLength += gResult['Directions']['Routes'][0]['Steps'][-1]["Distance"]["meters"]
  way = Way(points)
  way._setLength(mLength)
  messagePoints = []

  mDistanceFromStart = gResult['Directions']['Routes'][0]['Steps'][-1]["Distance"]["meters"]
  #          # add and compute the distance from start
  #          step['mDistanceFromStart'] = mDistanceFromStart
  #          mDistanceFromLast = step["Distance"]["meters"]
  #          mDistanceFromStart = mDistanceFromStart + mDistanceFromLast

  for step in steps:
    # TODO: abbreviation filtering
    message = step['descriptionHtml']
    SSMLMessage = step['descriptionEspeak']
    # as you can see, for some reason,
    # the coordinates in Google Directions steps are reversed:
    # (lon,lat,0)
    lat = step['Point']['coordinates'][1]
    lon = step['Point']['coordinates'][0]
    point = TurnByTurnPoint(lat, lon, message=message)
    point.setDistanceFromStart(mDistanceFromStart)
    point.setSSMLMessage(SSMLMessage)
    # store point to temporary list
    messagePoints.append(point)
    # update distance for next point
    mDistanceFromLast = step["Distance"]["meters"]
    mDistanceFromStart = mDistanceFromStart + mDistanceFromLast

  way.addMessagePoints(messagePoints)
  return way

def fromMonavResult(mResult):
  pass

def fromGPX(GPX):
  pass


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

      array.append((lat * 1e-5, lng * 1e-5))

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