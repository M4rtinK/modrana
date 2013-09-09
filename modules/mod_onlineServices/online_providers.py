# -*- coding: utf-8 -*-
# Online geodata providers
import time
from core import constants

try:
    import json
except ImportError:
    import simplejson as json

from core.providers import POIProvider, DummyController
from core.point import Point

try:  # Python 2
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError, URLError
except ImportError:  # Python 3
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode
    from urllib.error import HTTPError, URLError

NOMINATIM_GEOCODING_URL = "http://nominatim.openstreetmap.org/search?"
NOMINATIM_REVERSE_GEOCODING_URL = "http://nominatim.openstreetmap.org/reverse?"

class GoogleAddressSearch(POIProvider):
    def __init__(self):
        POIProvider.__init__(self, threadName=constants.THREAD_ADDRESS_SEARCH)

    def search(self, term=None, around=None, controller=DummyController()):
        """Search for an address using Google geocoding API"""
        if term is None:
            print("online_services: GoogleAddressSearch: term is None")
            return []
        controller.status = "starting online address search"
        controller.status = "online address search done"


class GeocodingNominatim(POIProvider):
    def __init__(self):
        POIProvider.__init__(self, threadName=constants.THREAD_ADDRESS_SEARCH)

    def search(self, term=None, around=None, controller=DummyController()):
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

    def search(self, term=None, around=None, controller=DummyController()):
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


class TestingProvider(POIProvider):
    def __init__(self):
        POIProvider.__init__(self, threadName=constants.THREAD_TESTING_PROVIDER)

    def search(self, term=None, around=None, controller=DummyController()):
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










