"""multi source geocoding"""
import sys
#import traceback
import urllib
import urllib2
# handle simplejson import
try:
  try:
    import json
  except ImportError:
    import simplejson as json       # pylint: disable-msg=F0401
except:
  import sys
  sys.path.append("modules/local_simplejson")
  print("onlineServices: using integrated non-binary simplejson, install proper simplejson package for better speed")
  import simplejson as json

from point import Point


class GeonamesWikipediaPoint(Point):
  """
  * a Point subclass suitable for representing the search result from
  a Geonames wkipedia search
  """
  def __init__(self, gnWikipediaResult):
    lat = gnWikipediaResult['lat']
    lon = gnWikipediaResult['lng']
    # for storage, we remember both name and summary in the message variable
    message = "%s\n%s" % (gnWikipediaResult['title'],gnWikipediaResult['summary'])
    Point.__init__(self, lat, lon, gnWikipediaResult['elevation'], message)
    self.abstract="%s..." % gnWikipediaResult['summary'][0:50] # chop a part of the summary
    self.description = gnWikipediaResult['summary']

  def getDescription(self):
    return self.description

  def getAbstract(self):
    return self.abstract

def _wikipediaResults2points(results):
  """convert wikipedia search results from Geonames to modRana points"""
  points = []
  for result in results:
    points.append(GeonamesWikipediaPoint(result))
  return points

# from the googlemaps module
def fetchJson(query_url, params={}, headers={}):
    """Retrieve a JSON object from a (parameterized) URL.

    :param query_url: The base URL to query
    :type query_url: string
    :param params: Dictionary mapping (string) query parameters to values
    :type params: dict
    :param headers: Dictionary giving (string) HTTP headers and values
    :type headers: dict
    :return: A `(url, json_obj)` tuple, where `url` is the final,
    parameterized, encoded URL fetched, and `json_obj` is the data
    fetched from that URL as a JSON-format object.
    :rtype: (string, dict or array)

    """
    encoded_params = urllib.urlencode(params)
    url = query_url + encoded_params
    print url
    request = urllib2.Request(url, headers=headers)
    response = urllib2.urlopen(request)
    return (url, json.load(response))
  
def wikipediaSearch(query):
  url = 'http://ws.geonames.org/wikipediaSearchJSON?'
#  params = {'q':query,
#            'maxRows':10,
#            'lang':'en'
#           }
  params = {'lang':'en',
            'q':query
           }
  try:
    url, results = fetchJson(url, params)
    return _wikipediaResults2points(results['geonames'])
  except Exception, e:
#    traceback.print_exc(file=sys.stdout) # find what went wrong
    print("wiki search exception:\n", e)
    return []


