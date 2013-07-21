"""multi source geocoding"""
import sys
#import traceback
try:  # Python 2
    from urllib import urlencode
    from urllib2 import urlopen, Request, build_opener, HTTPError, URLError
except ImportError:  # Python 3
    from urllib.request import urlopen, Request, build_opener
    from urllib.parse import urlencode
    from urllib.error import HTTPError, URLError
# handle simplejson import
try:
    try:
        import json
    except ImportError:
        import simplejson as json
except Exception:
    import sys

    e = sys.exc_info()[1]
    import sys

    sys.path.append("modules/local_simplejson")
    print(e)
    print("onlineServices: using integrated non-binary simplejson, install proper simplejson package for better speed")
    import simplejson as json

from core.point import Point


class GeonamesWikipediaPoint(Point):
    """
    * a Point subclass suitable for representing the search result from
    a Geonames wikipedia search
    """

    def __init__(self, gnWikipediaResult):
        lat = gnWikipediaResult['lat']
        lon = gnWikipediaResult['lng']
        # for storage, we remember both name and summary in the message variable
        message = "%s\n%s" % (gnWikipediaResult['title'], gnWikipediaResult['summary'])
        Point.__init__(self, lat, lon, gnWikipediaResult.get('elevation', None), message)
        self.abstract = "%s..." % gnWikipediaResult['summary'][0:50] # chop a part of the summary
        self.result = gnWikipediaResult

    def getName(self):
        return self.result['title']

    def getDescription(self):
        return self.result['summary']

    def getAbstract(self):
        return self.abstract

    def getUrls(self):
        fullUrl = "http://%s" % self.result['wikipediaUrl']
        return [(fullUrl, "full article")]


def _wikipediaResults2points(results):
    """convert wikipedia search results from Geonames to modRana points"""
    points = []
    for result in results:
        points.append(GeonamesWikipediaPoint(result))
    return points

# from the googlemaps module
def fetchJson(query_url, params=None, headers=None):
    """Retrieve a JSON object from a (parametrized) URL.

    :param query_url: The base URL to query
    :type query_url: string
    :param params: Dictionary mapping (string) query parameters to values
    :type params: dict
    :param headers: Dictionary giving (string) HTTP headers and values
    :type headers: dict
    :return: A `(url, json_obj)` tuple, where `url` is the final,
    parametrized, encoded URL fetched, and `json_obj` is the data
    fetched from that URL as a JSON-format object.
    :rtype: (string, dict or array)

    """
    if not headers: headers = {}
    if not params: params = {}
    encoded_params = urlencode(params)
    url = query_url + encoded_params
    print(url)
    request = Request(url, headers=headers)
    response = urlopen(request)
    return url, json.load(response)


def wikipediaSearch(query):
    url = 'http://ws.geonames.org/wikipediaSearchJSON?'
    #  params = {'q':query,
    #            'maxRows':10,
    #            'lang':'en'
    #           }
    params = {'lang': 'en',
              'q': query
    }
    try:
        url, results = fetchJson(url, params)
        return _wikipediaResults2points(results['geonames'])
    except Exception:
        import sys

        e = sys.exc_info()[1]
        #    traceback.print_exc(file=sys.stdout) # find what went wrong
        print("online: wiki search exception")
        print(e)
        return []


def elevSRTM(lat, lon):
    """get elevation in meters for the specified latitude and longitude from geonames"""
    url = 'http://ws.geonames.org/srtm3?lat=%f&lng=%f' % (lat, lon)
    try:
        query = urlopen(url)
    except Exception:
        import sys

        e = sys.exc_info()[1]
        print("onlineServices: getting elevation from geonames returned an error")
        print(e)
        return 0
    return query.read()


def elevBatchSRTM(latLonList, threadCB=None, userAgent=None):
    """ get elevation in meters for the specified latitude and longitude from
     geonames synchronously, it is possible to ask for up to 20 coordinates
     at once
    """
    maxCoordinates = 20 #geonames only allows 20 coordinates per query
    latLonElevList = []
    mL = len(latLonList)
    while len(latLonList) > 0:
    #    print("elevation: %d of %d done" % (mL - len(latLonList), mL))
        if threadCB: # report progress to the worker thread
            progress = len(latLonList) / float(mL)
            threadCB(progress)
        tempList = latLonList[0:maxCoordinates]
        latLonList = latLonList[maxCoordinates:]
        #      latLonList = latLonList[maxCoordinates:len(latLonList)]

        lats = ""
        lons = ""
        for point in tempList:
            lats += "%f," % point[0]
            lons += "%f," % point[1]

            # TODO: maybe add switching ?
            #      url = 'http://ws.geonames.org/astergdem?lats=%s&lngs=%s' % (lats,lons)
        url = 'http://ws.geonames.org/srtm3?lats=%s&lngs=%s' % (lats, lons)
        query = None
        results = []
        try:
            request = Request(url)
            opener = build_opener()
            if userAgent:
                request.add_header('User-Agent', userAgent)
            query = opener.open(request)

        except Exception:

            import sys

            e = sys.exc_info()[1]
            print("online: getting elevation from geonames returned an error")
            print(e)
            results = "0"
            for i in range(1, len(tempList)):
                results += " 0"
        try:
            if query:
                results = query.read().split('\r\n')
                query.close()
        except Exception:
            import sys

            e = sys.exc_info()[1]
            print("online: elevation string from geonames has a wrong format")
            print(e)
            results = "0"
            for i in range(1, len(tempList)):
                results += " 0"

        index = 0
        for point in tempList: # add the results to the new list with elevation
            latLonElevList.append((point[0], point[1], int(results[index])))
            index += 1

    return latLonElevList



