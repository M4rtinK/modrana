"""a modRana class representing an unified tracklog or route"""
class Point:
  """a point on the way"""
  def __init__(self, lat, lon, elevation=None, message=None):
    self.lat = lat
    self.lon = lon
    self.elevation = elevation
    self.message = message

  def getLL(self):
    return (self.lat,self.lon)

  def setLL(self, lat, lon):
    self.lat = lat
    self.lon = lon

  def getLLE(self):
    return (self.lat,self.lon, self.elevation)

  def setLLE(self, lat, lon, elevation):
    self.lat = lat
    self.lon = lon
    self.elevation = elevation

  def getElevation(self):
    return (self.elevation)

  def setElevation(self, elevation):
    self.elevation = elevation

  def getMessage(self):
    return self.message

  def setMessage(self, message):
    self.message = message

class Segment:
  """a segment of the way"""
  def __init__(self, points=[]):
    self.points = points
    # caching
    self.dirty = False # signalizes that cached data needs to be updated
    self.messagePoints = []
    # now update the cache
    self._updateCache()

  def getPointByID(self, index):
    return self.points[index]

  def getPointCount(self):
    return len(self.points)

    # * message points

  def _updateCache(self):
    messagePoints = []
    for point in self.points:
      if point.getMessage() != None:
        messagePoints.append(point)

  def getMessagePointByID(self, index):
    return self.messagePoints[index]

  def getMessagePointCount(self):
    return len(self.messagePoints)
    

class Way:
  """a way consisting of one or more segments"""
  def __init__(self):
    self.segments = []

def fromGoogleResult(gResult):
  pass

def fromMonavResult(mResult):
  pass

def fromGPX(GPX):
  pass

