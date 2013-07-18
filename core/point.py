"""an universal class representing a point"""

class Point(object):
  """a point"""
  def __init__(self, lat, lon, elevation=None, name=None, summary=None, message=None):
    self.lat = lat
    self.lon = lon
    self.elevation = elevation # should be in meters
    self._name = name
    self._summary = summary
    self._message = message

  def __unicode__(self):
    if self.getElevation() is None:
      elev = "unknown"
    else:
      elev = "%f m" % self.getElevation()

    return '%f,%f elev: %s "%s:%s"' % (self.lat, self.lon, elev, self.name, self.summary)

  def __str__(self):
    return unicode(self).encode('utf-8')

  @property
  def name(self):
    if self._name is not None:
      return self._name
    elif self._message:
      return self._message.split('\n',1)[0]
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
      return self._message.split('\n',1)[0]
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
    return self.lat,self.lon, self.elevation, self._message

  def getElevation(self):
    return self.elevation

  def setElevation(self, elevation):
    self.elevation = elevation

  def getMessage(self):
    return self._message

  def setMessage(self, message):
    self._message = message

  def getName(self):
    return self._message

  def getDescription(self):
    return self._message

  def getAbstract(self):
    """a short single line point description"""
    if self._message:
      return self._message.split('\n',1)[0]

  def getUrls(self):
    """get a list of (Url, Url description) tuples corresponding to the point"""
    return []