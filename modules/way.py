"""a modRana class representing an unified tracklog or route"""
# -*- coding: utf-8 -*-
from point import Point

class Segment:
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

  def getMessagePointByID(self, index):
    return self.messagePoints[index]

  def addMessagePoint(self, point):
    self.messagePoints.append(point)
    self._updateCache()

  def addMessagePoints(self, points):
    self.messagePoints.extend(points)
    self._updateCache()

  def getMessagePointsLLE(self):
    return self.messagePointsLLE

  def getMessagePointCount(self):
    return len(self.messagePoints)

  def __str__(self):
    pCount = self.getPointCount()
    mpCount = self.getMessagePointCount()
    return "segment: %d points and %d message points" % (pCount, mpCount)
    

class Way:
  """a way consisting of one or more segments"""
  def __init__(self):
    self.segments = []

  def addSegment(self, segment):
    """add a segment"""
    self.segments.append(segment)

  def getSegmentByID(self, index):
    return self.segments[index]

  def getSegmentCount(self):
    return len(self.segments)

  def __str__(self):
    """textual state description"""
    count = 0
    for segment in self.segments:
      count+=segment.getPointCount()
    return "way: %d segments, %d points total" % (self.getSegmentCount(), count)

def fromGoogleDirectionsResult(gResult):
  steps = gResult['Directions']['Routes'][0]['Steps']
  points = _decodePolyline(gResult['Directions']['Polyline']['points'])
  way = Way()
  segment = Segment(points)
  messagePoints = []
  for step in steps:
    # TODO: abbreviation filtering
    message = step['descriptionHtml']
    # as you can see, for some reason,
    # the coordinates in Google Directions steps are reversed:
    # (lon,lat,0)
    lat = step['Point']['coordinates'][1]
    lon = step['Point']['coordinates'][0]
    point = Point(lat, lon, message=message)
    messagePoints.append(point)
  segment.addMessagePoints(messagePoints)
  way.addSegment(segment)
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