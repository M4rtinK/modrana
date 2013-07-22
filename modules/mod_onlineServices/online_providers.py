# -*- coding: utf-8 -*-
# Online geodata providers
import time

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

NOMINATIM_GEOCODING_URL = API_URL = "http://nominatim.openstreetmap.org/search?"


class GoogleAddressSearch(POIProvider):
    def __init__(self):
        POIProvider.__init__(self)

    def search(self, term=None, around=None, controller=DummyController()):
        """Search for an address using Google geocoding API"""
        if term is None:
            print("online_services: GoogleAddressSearch: term is None")
            return []
        controller.status = "starting online address search"
        controller.status = "online address search done"


class GeocodingNominatim(POIProvider):
    def __init__(self):
        POIProvider.__init__(self)

    def search(self, term=None, around=None, controller=DummyController()):
        """Search for an address using Google geocoding API"""
        if term is None:
            print("online_services: NominatimAddressSearch: term is None")
            return []
        results = []
        controller.status = "starting online address search"
        try:
            params = {
                'q': term,
                'format': 'json',
                'addressdetails': 0
            }
            queryUrl = NOMINATIM_GEOCODING_URL + urlencode(params)
            reply = urlopen(queryUrl)
            if reply:
                jsonReply = json.load(reply)
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

class TestingProvider(POIProvider):
    def __init__(self):
        POIProvider.__init__(self)

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
    print("Callback test got got:")
    print(value)










