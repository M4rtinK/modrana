# -*- coding: utf-8 -*-
# Offline routing providers
import time
from core import constants
from core.way import Way

from urllib.request import urlopen
from urllib.parse import quote

try:
    import json
except ImportError:
    import simplejson as json

import logging
log = logging.getLogger("mod.routing.providers")

from core.providers import RoutingProvider, DummyController, RouteParameters, RoutingResult

OSM_SCOUT_SERVER_ROUTING_URL = "http://localhost:8553/v2/route?"

class MonavServerRouting(RoutingProvider):
    """Provider that does offline point to point routing
       using the Monav offline routing server API.
    """

    def __init__(self, monav_server_executable_path, monav_data_path):
        threadName = constants.THREAD_ROUTING_OFFLINE_MONAV
        RoutingProvider.__init__(self, threadName=threadName)
        from core import monav_support
        self._monav = monav_support.MonavServer(
            monav_data_path=monav_data_path,
            monav_server_executable_path=monav_server_executable_path
        )

    @property
    def data_path(self):
        return self._monav.data_path

    @data_path.setter
    def data_path(self, new_data_path):
        self._monav.data_path = new_data_path

    def search(self, waypoints, route_params=None, controller=DummyController()):
        routingStart = time.time()
        if self._monav.data_path is not None:
            result = None
            try:
                if not self._monav.server_running:
                    controller.status = "starting Monav routing server"
                    self._monav.start_server()
                controller.status = "Monav offline routing in progress"
                log.info(route_params)
                result = self._monav.get_monav_directions(waypoints, route_params)
                controller.status = "Monav offline routing done"
            except Exception:
                log.exception('Monav route lookup failed')

            if result is None: # routing failed for unknown reasons
                return RoutingResult(None, route_params)
            if result.type == result.SUCCESS:
                # convert the Monav result to a Way object usable
                # for turn-by-turn navigation using the instruction
                # generator set in the Monav wrapper
                route = Way.from_monav_result(result)
                return RoutingResult(route,
                                     route_params,
                                     constants.ROUTING_SUCCESS,
                                     lookupDuration=time.time() - routingStart)
            elif result.type == result.LOAD_FAILED:
                return RoutingResult(None, route_params, constants.ROUTING_LOAD_FAILED)
            elif result.type == result.LOOKUP_FAILED:
                return RoutingResult(None, route_params, constants.ROUTING_LOOKUP_FAILED)
            elif result.type == result.ROUTE_FAILED:
                return RoutingResult(None, route_params, constants.ROUTING_ROUTE_FAILED)
            else:
                return RoutingResult(None, route_params)
        else:
            log.error("no Monav routing data - can't route")
            return RoutingResult(None, route_params, constants.ROUTING_NO_DATA)


class MonavLightRouting(RoutingProvider):
    """Provider that does offline point to point routing
       using the Monav Light routing utility.
    """

    def __init__(self, monav_light_executable_path, monav_data_path):
        threadName = constants.THREAD_ROUTING_OFFLINE_MONAV
        RoutingProvider.__init__(self, threadName=threadName)
        self._utility_path = monav_light_executable_path
        self._data_path = monav_data_path

        from core import monav_support
        self._monav = monav_support.MonavLight(
            monav_light_executable_path=monav_light_executable_path,
            monav_data_path=monav_data_path,
        )

    @property
    def data_path(self):
        return self._monav.data_path

    @data_path.setter
    def data_path(self, new_data_path):
        self._monav.data_path = new_data_path

    def search(self, waypoints, route_params=None, controller=DummyController()):
        routingStart = time.time()
        if self._data_path is not None:
            result = None
            try:
                controller.status = "Monav offline routing in progress"
                log.info(route_params)
                result = self._monav.get_monav_directions(waypoints, route_params)
                controller.status = "Monav offline routing done"
            except Exception:
                log.exception('Monav route lookup failed')

            if result is None: # routing failed for unknown reasons
                return RoutingResult(None, route_params)
            if result.type == result.SUCCESS:
                # convert the Monav result to a Way object usable
                # for turn-by-turn navigation using the instruction
                # generator set in the Monav wrapper
                route = Way.from_monav_result(result)
                return RoutingResult(route,
                                     route_params,
                                     constants.ROUTING_SUCCESS,
                                     lookupDuration=time.time() - routingStart)
            elif result.type == result.LOAD_FAILED:
                return RoutingResult(None, route_params, constants.ROUTING_LOAD_FAILED)
            elif result.type == result.SOURCE_LOOKUP_FAILED:
                return RoutingResult(None, route_params, constants.ROUTING_SOURCE_LOOKUP_FAILED)
            elif result.type == result.TARGET_LOOKUP_FAILED:
                return RoutingResult(None, route_params, constants.ROUTING_TARGET_LOOKUP_FAILED)
            elif result.type == result.ROUTE_FAILED:
                return RoutingResult(None, route_params, constants.ROUTING_ROUTE_FAILED)
            else:
                return RoutingResult(None, route_params)
        else:
            log.error("no Monav routing data - can't route")
            return RoutingResult(None, route_params, constants.ROUTING_NO_DATA)


class GoogleRouting(RoutingProvider):
    """An online provider that does online
    point to point routing using Google API"""
    def __init__(self):
        threadName = constants.THREAD_ROUTING_ONLINE_GOOGLE
        RoutingProvider.__init__(self, threadName=threadName)

    def search(self, waypoints, route_params=RouteParameters(), controller=DummyController()):
        # check if we have at least 2 points
        routingStart = time.time()
        if len(waypoints) < 2:
            log.error("GoogleRouting provider: ERROR, need at least 2 points for routing")
            return RoutingResult(None, route_params)
        start = waypoints[0]
        destination = waypoints[-1]
        inBetweenPoints = waypoints[1:-1]
        log.info("GoogleRouting: routing from %s to %s", start, destination)
        log.info(route_params)
        controller.status = "online routing in progress"
        route, returnCode, errorMessage = _googleDirections(start, destination, inBetweenPoints, route_params)
        controller.status = "online routing done"
        # return the data from the routing function and add elapsed time in ms
        return RoutingResult(route,
                             route_params,
                             returnCode=returnCode,
                             errorMessage=errorMessage,
                             lookupDuration=time.time() - routingStart)


def _getGmapsInstance():
    """get a google maps wrapper instance"""
    key = constants.GOOGLE_API_KEY
    if key is None:
        log.error("onlineServices: online providers:"
              " a google API key is needed for using the google maps services")
        return None
    # only import when actually needed
    import googlemaps
    gMap = googlemaps.GoogleMaps(key)
    return gMap

def _googleDirections(start, destination, waypoints, params):
        """ Get driving directions using Google API
        start and directions can be either point objects or address strings
        :param start: start of the route
        :type start: Point object or string
        :param destination: destination of the route
        :type destination: Point object or string
        :param waypoints: points the route should go through
        :type waypoints: a list of Point objects
        :param params: requested route parameters
        :type params: RouteParameters instance
        """

        # check if start and destination are string,
        # otherwise convert to lat,lon strings from Points
        if not isinstance(start, str):
            start = "%f,%f" % (start.lat, start.lon)
        if not isinstance(destination, str):
            destination = "%f,%f" % (destination.lat, destination.lon)

        if not waypoints: waypoints = []

        flagDir = {'language': params.language}

        # toll and highway avoidance options
        if params.avoidHighways and params.avoidTollRoads:
            flagDir['avoid'] = 'tolls|highways'
        elif params.avoidHighways: # optionally avoid highways
            flagDir['avoid'] = 'highways'
        elif params.avoidTollRoads: # optionally avoid toll roads
            flagDir['avoid'] = 'tolls'

        # waypoints
        waypointOption = None
        if waypoints: # waypoints are a list of Point objects
            firstWayPoint = waypoints[0]
            waypointOption = "%f,%f" % (firstWayPoint.lat, firstWayPoint.lon)
            for waypoint in waypoints[1:]:
                waypointOption += "|%f,%f" % (waypoint.lat, waypoint.lon)

        # respect travel mode
        routeMode = "driving" # car directions are the default
        if params.routeMode == constants.ROUTE_BIKE:
            routeMode = "bicycling "
        elif params.routeMode == constants.ROUTE_PEDESTRIAN:
            routeMode = "walking"
        flagDir['mode'] = routeMode

        # TODO: check if/how public transport routing works
        #elif mode == 'train' or mode == 'bus':
        #    directionsType = 'r'
        #else:
        #    directionsType = ""

        # the google language code is the second part of this whitespace delimited string
        #googleLanguageCode = self.get('directionsLanguage', 'en en').split(" ")[1]

        gMap = _getGmapsInstance()
        if waypointOption:
            flagDir['waypoints'] = waypointOption
        flagDir['sensor'] = 'false'
        # only import the googlemaps module when actually needed
        import googlemaps

        directions = None
        returnCode = None
        errorMessage = ""

        try:
            directions = gMap.directions(start, destination, flagDir)
        except googlemaps.GoogleMapsError:
            import sys
            e = sys.exc_info()[1]
            if e.status == 602:
                log.error("Google routing failed -> address not found")
                log.error(e)
                errorMessage = "Address(es) not found"
                returnCode = constants.ROUTING_ADDRESS_NOT_FOUND
            elif e.status == 604:
                log.error("Google routing failed -> no route found")
                log.error(e)
                errorMessage = "No route found"
                returnCode = constants.ROUTING_ROUTE_FAILED
            elif e.status == 400:
                log.error("Google routing failed with googlemaps exception,"
                          " googlemaps status code:%d", e.status)
        except Exception:
            log.exception("onlineServices:GDirections:routing failed with non-googlemaps exception")

        # convert the directions datastructure returned by Google
        # to modRana Way object
        if directions is not None:
            returnCode = constants.ROUTING_SUCCESS
            route = Way.from_google_directions_result(directions)
        else:
            route = None
        return route, returnCode, errorMessage

class OSMScoutServerRouting(RoutingProvider):
    """Provider that does offline point to point routing
       using the Monav offline routing server API.
    """

    def __init__(self):
        threadName = constants.THREAD_ROUTING_OFFLINE_OSM_SCOUT_SERVER
        RoutingProvider.__init__(self, threadName=threadName)

    def search(self, waypoints, route_params=None, controller=DummyController()):
        routingStart = time.time()
        controller.status = "OSM Scout Server routing"
        try:
            route_type = "auto" # car directions are the default
            if route_params.routeMode == constants.ROUTE_BIKE:
                route_type = "bicycle"
            elif route_params.routeMode == constants.ROUTE_PEDESTRIAN:
                route_type = "pedestrian"

            locations = []
            for waypoint in waypoints:
                location_dict = {'lat': waypoint.lat, 'lon': waypoint.lon}
                # include heading when available
                if waypoint.heading is not None:
                    location_dict["heading"] = waypoint.heading
                locations.append(location_dict)

            params = {
                'costing': route_type,
                'directions_options': { 'language': route_params.language },
                'locations': locations
            }
            queryUrl = OSM_SCOUT_SERVER_ROUTING_URL + "json=" + quote(json.dumps(params))
            reply = urlopen(queryUrl)
            
            if reply:
                # json in Python 3 really needs it encoded like this
                replyData = reply.read().decode("utf-8")
                jsonReply = json.loads(replyData)
                if "API version" in jsonReply and jsonReply['API version'] == "libosmscout V1":
                    route = Way.from_osm_scout_json(jsonReply)
                else:
                    route = Way.from_valhalla(jsonReply)
                return RoutingResult(route,
                                     route_params,
                                     constants.ROUTING_SUCCESS,
                                     lookupDuration=time.time() - routingStart)
        except Exception:
            log.exception("OSM Scout Server routing: failed with exception")



