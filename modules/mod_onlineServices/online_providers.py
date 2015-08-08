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

import logging
log = logging.getLogger("mod.onlineServices.providers")

NOMINATIM_GEOCODING_URL = "http://nominatim.openstreetmap.org/search?"
NOMINATIM_REVERSE_GEOCODING_URL = "http://nominatim.openstreetmap.org/reverse?"


#local search result handling

class LocalSearchPoint(Point):
    """a local search result point"""

    def __init__(self, lat, lon, name="", phoneNumbers=None,
                 urls=None, addressLines=None, emails=None, openingHours=None,
                 priceLevel=None, rating=None):
        if not emails: emails = []
        if not addressLines: addressLines = []
        if not urls: urls = []
        if not phoneNumbers: phoneNumbers = []
        if not openingHours: openingHours = {}
        Point.__init__(self, lat, lon, name=name)
        self._message_loaded = False
        self._phoneNumbers = phoneNumbers
        self._urls = urls
        self._addressLines = addressLines
        self._emails = emails
        self._openingHours = openingHours
        self._priceLevel = priceLevel
        self._rating = rating

    @Point.name.setter
    def name(self, value):
        self._name = value
        # we now need to update the generated message
        # as the point name is a part of it
        self._update_message()

    @property
    def addressLines(self):
        return self._addressLines

    @property
    def phoneNumbers(self):
        return self._phoneNumbers

    @property
    def rating(self):
        return self._rating

    @property
    def priceLevel(self):
        return self._priceLevel

    @property
    def description(self):
        # Lazy description generation
        # * only generate the message once it is requested for the first time
        if self._message_loaded is False:
            self._update_message()
            return self._message
        else:
            return self._message

    def _update_message(self):
        """Regenerates the local search point description."""
        message = ""
        message += "%s\n\n" % self._name
        for item in self._addressLines:
            message += "%s\n" % item
        newline = ''
        if self._priceLevel:
            message += "%s " % '$$$$'[:self._priceLevel]
            newline = '\n'
        if self._rating:
            message += "Rating %.1f" % self._rating
            newline = '\n'
        message += newline
        for item in self.phoneNumbers:
            message += "%s\n" % item[1]
        for item in self._emails:
            message += "%s\n" % item
        for item in self._urls:
            message += "%s\n" % item
        if 'open_now' in self._openingHours and self._openingHours['open_now']:
            message += 'Open now\n'
        self._message = message
        self._message_loaded = True

    def __unicode__(self):
        return self.description


class GoogleLocalSearchPoint(LocalSearchPoint):
    def __init__(self, GLSResult):
        # dig the data out of the GLS result
        # and load it to the LSPoint object
        if 'address' in GLSResult:
            addressLine = GLSResult['address']
        else:
            addressLine = GLSResult['vicinity']

        if 'geometry' in GLSResult and 'location' in GLSResult['geometry']:
            lat = float(GLSResult['geometry']['location']['lat'])
            lng = float(GLSResult['geometry']['location']['lng'])
        else:
            lat = lng = None

        LocalSearchPoint.__init__(
            self,
            lat=lat,
            lon=lng,
            name=GLSResult['name'],
            addressLines=[addressLine],
            openingHours=self.fieldOrNone('opening_hours', GLSResult),
            priceLevel=self.fieldOrNone('price_level', GLSResult),
            rating=self.fieldOrNone('rating', GLSResult)
        )

    def fieldOrNone(self, field, GLSResult):
        if field in GLSResult:
            return GLSResult[field]
        else:
            return None


class GoogleAddressSearch(POIProvider):
    def __init__(self):
        POIProvider.__init__(self, threadName=constants.THREAD_ADDRESS_SEARCH)

    # online geocoding needs Internet access
    @requirements.internet
    def search(self, term=None, around=None, controller=DummyController(), **kwargs):
        """Search for an address using Google geocoding API"""
        if term is None:
            log.error("GoogleAddressSearch: term is None")
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

        return term, location

    def _processGLSResponse(self, response):
        """load GLS results to LocalSearchPoint objects"""
        points = []
        for result in response['results']:
            point = GoogleLocalSearchPoint(result)
            points.append(point)
        return points

    # first check if around is provided and enable GPS if not
    # as current position "becomes" around
    @requirements.needsAround
    # then start Internet and conditionally GPS,
    # so that they both can be initialized in parallel
    @requirements.startGPS(conditional=True)
    @requirements.startInternet
    # now run the GPS na Internet checks
    @requirements.gps(conditional=True)
    @requirements.internet
    def search(self, term=None, around=None,
               controller=DummyController(), maxResults=8 ,
               radius=constants.DEFAULT_LOCAL_SEARCH_RADIUS, **kwargs):
        """Search for POI using Google local search API"""
        if term is None and around is None:
            log.error("Google local search: term and location not set")
            return []
        elif term is None:
            log.error("Google local search: term not set")
            return []
        elif around is None:
            log.error("Google local search: location not set")
            return []
        controller.status = "online POI search"

        (query, location) = self._constructGLSQuery(term, around)

        sensor = 'false'
        if 'sensor' in kwargs:
            sensor = kwargs['sensor']
        log.info("Google local search query: %s" % query)
        gMap = _getGmapsInstance()
        if gMap:
            response = gMap.local_search(query, maxResults, location = location,
                                         sensor = sensor, radius=radius)
            controller.status = "processing POI from search"
            points = self._processGLSResponse(response)
            controller.status = "online POI search done"
            return points
        else:
            log.error("Google local search: no Google maps instance")


def _getGmapsInstance():
    """get a google maps wrapper instance"""
    key = constants.GOOGLE_PLACES_API_KEY
    if key is None:
        log.error("a google API key is needed for using the Google maps services")
        return None
        # only import when actually needed
    import googlemaps
    gMap = googlemaps.GoogleMaps(key)
    return gMap


class GeocodingNominatim(POIProvider):
    def __init__(self):
        POIProvider.__init__(self, threadName=constants.THREAD_ADDRESS_SEARCH)

    # online geocoding needs Internet access
    @requirements.internet
    def search(self, term=None, around=None, controller=DummyController(), **kwargs):
        """Search for an address using the Nominatim geocoding API"""
        if term is None:
            log.error("NominatimAddressSearch: term is None")
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
            log.exception("NominatimAddressSearch: failed with exception")

        controller.status = "online address search done"
        return results


class ReverseGeocodingNominatim(POIProvider):
    def __init__(self):
        POIProvider.__init__(self, threadName=constants.THREAD_REVERSE_GEOCODING)

    # online geocoding needs Internet access
    @requirements.internet
    def search(self, term=None, around=None, controller=DummyController(), **kwargs):
        """Search for an address for coordinates using the Nominatim
        reverse geocoding API
        """
        if term is None:
            log.error("Nominatim reverse geocoding: term is None")
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
            log.exception("Nominatim reverse geocoding: failed with exception")

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
            log.error("Nominatim Wikipedia search: term not set")
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
        log.debug("starting provider test")
        for i in range(1,7,1):
            controller.status = "waiting %d seconds" % i
            log.debug("waiting %d seconds" % i)
            time.sleep(1)
        controller.status = "provider test done"
        log.debug("provider test done")
        return None

def _callbackTest(self, value):
    log.debug("Callback test got:")
    log.debug(value)










