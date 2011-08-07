"""an universal class representing a point"""

class Point:
  """a point"""
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