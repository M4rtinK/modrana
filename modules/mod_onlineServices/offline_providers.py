# -*- coding: utf-8 -*-
# Online geodata providers
from core import constants
from core.point import Point
from core import requirements

try:
    import json
except ImportError:
    import simplejson as json

from core.providers import POIProvider, DummyController

from urllib.request import urlopen
from urllib.parse import urlencode

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
        controller.status = "OSM Scout Server place search"
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



class OSMScoutServerLocalSearch(POIProvider):
    def __init__(self):
        POIProvider.__init__(self, threadName=constants.THREAD_LOCAL_SEARCH_OSM_SCOUT)

    # first check if around is provided and enable GPS if not
    # as current position "becomes" around
    @requirements.needsAround
    # then start Internet and conditionally GPS,
    # so that they both can be initialized in parallel
    @requirements.startGPS(conditional=True)
    # now run the GPS check
    @requirements.gps(conditional=True)
    def search(self, term=None, around=None,
               controller=DummyController(), maxResults=8 ,
               radius=constants.DEFAULT_LOCAL_SEARCH_RADIUS, **kwargs):
        """Search for POI using OSM Scout Server"""
        if term is None and around is None:
            log.error("OSM Scout Server local search: term and location not set")
            return []
        elif term is None:
            log.error("OSM Scout Server local search: term not set")
            return []
        elif around is None:
            log.error("OSM Scout Server local search: location not set")
            return []
        controller.status = "OSM Scout Server local search"

        results = []
        controller.status = "OSM Scout Server local search"
        try:
            point_type = "amenity"
            # check if type override has been specified by prefix
            term_split =  term.split(":", 1)
            if len(term_split) > 1:
                point_type = term_split[0]
                term = term_split[1]

            term = term.encode("utf-8")
            params = {
                'limit': maxResults,
                'poitype': term,
                'radius': radius,
                'lat' : around.lat,
                'lng' : around.lon
            }
            query_url = OSM_SCOUT_SERVER_LOCAL_SEARCH_URL + urlencode(params)
            log.debug("OSM Scout Server local search query URL:")
            log.debug(query_url)
            reply = urlopen(query_url)
            if reply:
                # json in Python 3 really needs it encoded like this
                replyData = reply.read().decode("utf-8")
                jsonReply = json.loads(replyData)
                for result in jsonReply.get("results"):
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




