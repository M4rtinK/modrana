# -*- coding: utf-8 -*-
# Online geodata providers
import time
import re
from core import constants
from core.point import Point
from core import requirements
from modules.mod_onlineServices import geonames

try:
    import json
except ImportError:
    import simplejson as json

from core.providers import POIProvider, DummyController

try:  # Python 2
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError, URLError
except ImportError:  # Python 3
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode
    from urllib.error import HTTPError, URLError

NOMINATIM_GEOCODING_URL = "http://nominatim.openstreetmap.org/search?"
NOMINATIM_REVERSE_GEOCODING_URL = "http://nominatim.openstreetmap.org/reverse?"


#local search result handling

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
        self._message = None
        self._phoneNumbers = phoneNumbers
        self.urls = urls
        self._addressLines = addressLines
        self.emails = emails

    @property
    def addressLines(self):
        return self._addressLines

    @property
    def phoneNumbers(self):
        return self._phoneNumbers

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
        message += "%s\n\n" % self._name
        if self.description != "":
            message += "%s\n" % self.description
        for item in self._addressLines:
            message += "%s\n" % item
        for item in self.phoneNumbers:
            message += "%s\n" % item[1]
        for item in self.emails:
            message += "%s\n" % item
        for item in self.urls:
            message += "%s\n" % item
        self.setMessage(message)

    def __unicode__(self):
        return self.getMessage()


class GoogleLocalSearchPoint(LocalSearchPoint):
    def __init__(self, GLSResult):
        # dig the data out of the GLS result
        # and load it to the LSPoint object
        addressLine = "%s, %s, %s" % (GLSResult['streetAddress'], GLSResult['city'], GLSResult['country'])
        phoneNumbers = []

        for number in GLSResult.get('phoneNumbers', []):
            # number types
            # "" -> normal phone number
            # "FAX" -> FAX phone number
            phoneNumbers.append((number['type'], number['number']))

        LocalSearchPoint.__init__(
            self,
            lat=float(GLSResult['lat']),
            lon=float(GLSResult['lng']),
            name=GLSResult['titleNoFormatting'],
            addressLines=[addressLine],
            phoneNumbers=phoneNumbers
        )


class GoogleAddressSearch(POIProvider):
    def __init__(self):
        POIProvider.__init__(self, threadName=constants.THREAD_ADDRESS_SEARCH)

    @requirements.internet
    def search(self, term=None, around=None, controller=DummyController(), **kwargs):
        """Search for an address using Google geocoding API"""
        if term is None:
            print("online_services: GoogleAddressSearch: term is None")
            return []
        controller.status = "starting online address search"
        controller.status = "online address search done"


class GoogleLocalSearch(POIProvider):
    def __init__(self):
        POIProvider.__init__(self, threadName=constants.THREAD_LOCAL_SEARCH_GOOGLE)


    def _constructGLSQuery(self, term, location):
        """get a correctly formatted GLS query"""
        # check if the location is a Point or a string
        if not isinstance(location, str):
            # convert a Point object to lat,lon string
            location = "%f,%f" % (location.lat, location.lon)

        query = "%s loc:%s" % (term, location)

        # Local Search doesn't like the geo: prefix so we remove it
        query = re.sub("loc:.*geo:", "loc:", query)

        return query

    def _processGLSResponse(self, response):
        """load GLS results to LocalSearchPoint objects"""
        results = response['responseData']['results']
        points = []
        for result in results:
            point = GoogleLocalSearchPoint(result)
            points.append(point)
        return points

    # local search might need a GPS fix and Internet access,
    # also check if around is provided and enable GPS if not
    @requirements.needsAround
    @requirements.gps
    @requirements.internet
    def search(self, term=None, around=None,
               controller=DummyController(), maxResults=8 ,**kwargs):
        """Search for POI using Google local search API"""
        if term is None and around is None:
            print("online_services: Google local search: term and location not set")
            return []
        elif term is None:
            print("online_services: Google local search: term not set")
            return []
        elif around is None:
            print("online_services: Google local search: location not set")
            return []
        controller.status = "online POI search"

        query = self._constructGLSQuery(term, around)

        print("local search query: %s" % query)
        gMap = _getGmapsInstance()
        if gMap:
            result = gMap.local_search(query, maxResults)
            controller.status = "processing POI from search"
            points = self._processGLSResponse(result)
            controller.status = "online POI search done"
            return points
        else:
            print("Google local search: no Google maps instance")


def _getGmapsInstance():
    """get a google maps wrapper instance"""
    key = constants.GOOGLE_API_KEY
    if key is None:
        print("online_providers:"
              " a google API key is needed for using the Google maps services")
        return None
        # only import when actually needed
    from modules import googlemaps
    gMap = googlemaps.GoogleMaps(key)
    return gMap


class GeocodingNominatim(POIProvider):
    def __init__(self):
        POIProvider.__init__(self, threadName=constants.THREAD_ADDRESS_SEARCH)

    # online geocoding needs internet access
    @requirements.internet
    def search(self, term=None, around=None, controller=DummyController(), **kwargs):
        """Search for an address using the Nominatim geocoding API"""
        if term is None:
            print("online_services: NominatimAddressSearch: term is None")
            return []
        results = []
        controller.status = "starting online address search"
        try:
            term = term.encode("utf-8")
            params = {
                'q': term,
                'format': 'json',
                'addressdetails': 0
            }
            queryUrl = NOMINATIM_GEOCODING_URL + urlencode(params)
            reply = urlopen(queryUrl)
            if reply:
                # json in Python 3 really needs it encoded like this
                replyData = reply.read().decode("utf-8")
                jsonReply = json.loads(replyData)
                for result in jsonReply:
                    # split a prefix from the display name
                    description = result.get("display_name")
                    # get the first element for name
                    name = description.split(", ")[0]
                    # and first three elements for summary
                    summary = description.split(", ")[0:3]
                    # recombined back to ", " delimited string
                    summary = ", ".join(summary)
                    lat = float(result["lat"])
                    lon = float(result["lon"])
                    # create Point object instance
                    point = Point(lat, lon,
                                  name=name, summary=summary, message=description)
                    results.append(point)
        except Exception:
            import sys

            e = sys.exc_info()[1]
            import traceback

            traceback.print_exc(file=sys.stdout)

            print("online_services: NominatimAddressSearch: failed with exception\n%s" % e)

        controller.status = "online address search done"
        return results


class ReverseGeocodingNominatim(POIProvider):
    def __init__(self):
        POIProvider.__init__(self, threadName=constants.THREAD_REVERSE_GEOCODING)

    # online geocoding needs internet access
    @requirements.internet
    def search(self, term=None, around=None, controller=DummyController(), **kwargs):
        """Search for an address for coordinates using the Nominatim
        reverse geocoding API
        """
        if term is None:
            print("online_services: Nominatim reverse geocoding: term is None")
            return []
        results = []
        controller.status = "starting online reverse geocoding"
        try:
            params = {
                'lat': term.lat,
                'lon': term.lon,
                'zoom' : 18,
                'format': 'json',
                'addressdetails': 0
            }
            queryUrl = NOMINATIM_REVERSE_GEOCODING_URL + urlencode(params)
            reply = urlopen(queryUrl)
            if reply:
                # json in Python 3 really needs it encoded like this
                replyData = reply.read().decode("utf-8")
                result = json.loads(replyData)
                # split a prefix from the display name
                description = result.get("display_name")
                # get the first 2 elements for name
                name = description.split(", ")[0:2]
                name = ", ".join(name)
                # and first three elements for summary
                summary = description.split(", ")[0:3]
                # recombined back to ", " delimited string
                summary = ", ".join(summary)
                lat = float(result["lat"])
                lon = float(result["lon"])
                # create Point object instance
                point = Point(lat, lon,
                              name=name, summary=summary, message=description)
                results.append(point)
        except Exception:
            import sys
            e = sys.exc_info()[1]
            import traceback
            traceback.print_exc(file=sys.stdout)
            print("online_services: Nominatim reverse geocoding:\nfailed with exception\n%s" % e)

        controller.status = "online reverse geocoding done"
        return results


class WikipediaSearchNominatim(POIProvider):
    def __init__(self):
        POIProvider.__init__(self,
            threadName=constants.THREAD_WIKIPEDIA_SEARCH_NOMINATIM
        )

    # online Wikipedia search needs Internet access
    @requirements.internet
    def search(self, term=None, around=None, controller=DummyController(), **kwargs):
        """Search for Wikipedia articles around the given location"""
        if term is None:
            print("online_services: Nominatim Wikipedia search: term not set")
            return []
        controller.status = "online Wikipedia search"
        results = geonames.wikipediaSearch(term)
        controller.status = "online Wikipedia search done"
        return results


class TestingProvider(POIProvider):
    def __init__(self):
        POIProvider.__init__(self, threadName=constants.THREAD_TESTING_PROVIDER)

    def search(self, term=None, around=None, controller=DummyController(), **kwargs):
        controller.status  = "starting provider test"
        print("starting provider test")
        for i in range(1,7,1):
            controller.status = "waiting %d seconds" % i
            print("waiting %d seconds" % i)
            time.sleep(1)
        controller.status = "provider test done"
        print("provider test done")
        return None

def _callbackTest(self, value):
    print("Callback test got:")
    print(value)










