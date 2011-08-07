"""a modRana class representing an unified tracklog or route"""
from point import Point

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

