"""an universal class representing a point"""

class Point(object):
  """a point"""
  def __init__(self, lat, lon, elevation=None, message=None):
    self.lat = lat
    self.lon = lon
    self.elevation = elevation # should be in meters
    self.message = message

  def __unicode__(self):
    if self.getElevation() is None:
      elev = "unknown"
    else:
      elev = "%f m" % self.getElevation()

    return '%f,%f elevation: %s "%s"' % (self.lat, self.lon, elev, self.getMessage())

  def __str__(self):
    return unicode(self).encode('utf-8')

  def getLL(self):
    return self.lat,self.lon

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
    return self.lat,self.lon, self.elevation, self.message

  def getElevation(self):
    return self.elevation

  def setElevation(self, elevation):
    self.elevation = elevation

  def getMessage(self):
    return self.message

  def setMessage(self, message):
    self.message = message

  def getName(self):
    return self.message

  def getDescription(self):
    return self.message

  def getAbstract(self):
    """a short single line point description"""
    if self.message:
      return self.message.split('\n',1)[0]

  def getUrls(self):
    """get a list of (Url, Url description) tuples corresponding to the point"""
    return []