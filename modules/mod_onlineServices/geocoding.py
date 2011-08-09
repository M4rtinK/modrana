"""multi source geocoding"""

def geocode(address):
  from geopy import geocoders
  g = geocoders.Google()
  try:
    return (g.geocode(address, exactly_one=False))
  except Exception, e:
    print("geocoding exception:\n", e)
    return []
  
def wikipediaSearch(query):
  from geopy import geocoders
  wiki = geocoders.MediaWiki("http://wikipedia.org/wiki/%s", exactly_one=False)
#  wiki = geocoders.MediaWiki("http://en.wikipedia.org/wiki/%s", exactly_one=False)
#  wiki = geocoders.MediaWiki("http://en.wikipedia.org/wiki/Special:Search/%s", exactly_one=False)
  return(wiki.geocode(query) )
