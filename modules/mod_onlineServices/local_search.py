#local search result handling

from core.point import Point

class LocalSearchPoint(Point):
  """a local search result point"""
  def __init__(self, lat, lon, name="", description="", phoneNumbers=None, urls=None, addressLines=None, emails=None):
    if not emails: emails = []
    if not addressLines: addressLines = []
    if not urls: urls = []
    if not phoneNumbers: phoneNumbers = []
    Point.__init__(self, lat, lon, message=name)
    self._name = name
    self.description = description
    self._message=None
    self.phoneNumbers = phoneNumbers
    self.urls = urls
    self.addressLines = addressLines
    self.emails = emails

  def getName(self):
    return self._name

  def getDescription(self):
    return self.description

  def getMessage(self):
    # lazy message generation
    # = only generate the message once it is requested for the first time
    if self._message is None:
      self.updateMessage()
      return self._message
    else:
      return self._message

  def updateMessage(self):
    """call this if you change the properties of an existing point"""
    message = ""
    message+="%s\n\n" % self._name
    if self.description != "":
      message+="%s\n" % self.description
    for item in self.addressLines:
      message+="%s\n" % item
    for item in self.phoneNumbers:
      message+="%s\n" % item[1]
    for item in self.emails:
      message+="%s\n" % item
    for item in self.urls:
      message+="%s\n" % item
    self.setMessage(message)

  def __unicode__(self):
    return self.getMessage()

class GoogleLocalSearchPoint(LocalSearchPoint):
  def __init__(self, GLSResult):
    # dig the data out of the GLS result
    # and load it to the LSPoint object
    addressLine = "%s, %s, %s" % (GLSResult['streetAddress'], GLSResult['city'], GLSResult['country'])
    phoneNumbers = []
    for number in GLSResult['phoneNumbers']:
      # number types
      # "" -> normal phone number
      # "FAX" -> FAX phone number
      phoneNumbers.append((number['type'],number['number']))

    LocalSearchPoint.__init__(
      self,
      lat = float(GLSResult['lat']),
      lon = float(GLSResult['lng']),
      name = GLSResult['titleNoFormatting'],
      addressLines = [addressLine],
      phoneNumbers=phoneNumbers
    )