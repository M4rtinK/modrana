# -*- coding: utf-8 -*-
# Online geodata providers
import time
import re
from core import constants
from core.point import Point
from core import requirements

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

OSM_SCOUT_SERVER_POI_SEARCH_URL = "http://localhost:8553/v1/search?"
OSM_SCOUT_SERVER_LOCAL_SEARCH_URL = "http://localhost:8553/v1/guide?"

import logging
log = logging.getLogger("mod.onlineServices.providers")

class GeocodingOSMScoutServer(POIProvider):
    def __init__(self):
        POIProvider.__init__(self, threadName=constants.THREAD_ADDRESS_SEARCH)

    # offline geocoding doesn't need Internet access
    def search(self, term=None, around=None, controller=DummyController(), **kwargs):
        """Search for an address using the OSM Scout Server geocoding API"""
        if term is None:
            log.error("OSMScoutServerSearch: term is None")
            return []
        results = []
        controller.status = "starting OSM Scout Server place search"
        try:
            term = term.encode("utf-8")
            params = {
                'limit': 16,  # TODO: make this configurable
                'search': term
            }
            queryUrl = OSM_SCOUT_SERVER_POI_SEARCH_URL + urlencode(params)
            reply = urlopen(queryUrl)
            if reply:
                # json in Python 3 really needs it encoded like this
                replyData = reply.read().decode("utf-8")
                jsonReply = json.loads(replyData)
                for result in jsonReply:
                    name = result.get("title")

                    # Summary generation is based on how Poor Maps does this
                    items = []
                    try:
                        poi_type = result["type"]
                        poi_type = poi_type.replace("amenity", "")
                        poi_type = poi_type.replace("_", " ").strip()
                        items.append(poi_type.capitalize())
                    except:
                        pass
                    try:
                        items.append(result["admin_region"])
                    except:
                        pass
                    summary = ", ".join(items) or "–"
                    lat = float(result["lat"])
                    lon = float(result["lng"])
                    # create Point object instance
                    point = Point(lat, lon,
                                  name=name,
                                  summary=summary,
                                  message=summary)
                    results.append(point)
        except Exception:
            log.exception("OSMScoutServerPlaceSearch: failed with exception")

        controller.status = "offline place search done"
        return results








