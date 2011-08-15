"""multi source geocoding"""
from point import Point

def _places2points(places):
  """convert place tupples to modRana points"""
  points = []
  for place in places:
    text, (lat,lon) = place
    points.append(Point(lat,lon, message=text))
  return points

def geocode(address):
  from geopy import geocoders
  g = geocoders.Google()
  try:
    places = list(g.geocode(address, exactly_one=False))
    return _places2points(places)
  except Exception, e:
    print("geocoding exception:\n", e)
    return []
  
#def wikipediaSearch(query):
#  from geopy import geocoders
##  wiki = geocoders.MediaWiki("http://wikipedia.org/wiki/%s")
##  wiki = geocoders.MediaWiki("http://en.wikipedia.org/wiki/%s")
##  wiki = geocoders.MediaWiki("http://en.wikipedia.org/wiki/Special:Search/%s")
#  wiki = geocoders.MediaWiki("http://wiki.case.edu/%s")
#  places = list(wiki.geocode(query))
#  return _places2points(places)
##  try:
##    places = list(wiki.geocode(query))
##    return _places2points(places)
##  except Exception, e:
##    print("wiki search exception:\n", e)
##    return []


