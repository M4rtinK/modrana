"""multi source geocoding"""

def geocode(address):
  from geopy import geocoders
  g = geocoders.Google()
  try:
    return (g.geocode(address, exactly_one=False))
  except Exception, e:
    print("geocoding exception:\n", e)
    return []