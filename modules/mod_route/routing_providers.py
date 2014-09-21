# -*- coding: utf-8 -*-
# Offline routing providers
import os
import time
import traceback
from core import constants
from core import way
from core.backports import six

try:
    import json
except ImportError:
    import simplejson as json

import logging
log = logging.getLogger("mod.routing.providers")

from core.providers import RoutingProvider, DummyController, RouteParameters, RoutingResult

class MonavRouting(RoutingProvider):
    """An online provider that does online
    point to point routing using Google API"""
    def __init__(self, monav):
        threadName = constants.THREAD_ROUTING_ONLINE_GOOGLE
        RoutingProvider.__init__(self, threadName=threadName)
        self.monav = monav

    def search(self, waypoints, routeParams=None, controller=DummyController()):
        # get mode based sub-folder
        routingStart = time.time()
        if self.monav.dataPath is not None:
            result = None
            try:
                if self.monav.monavServer is None:
                    controller.status = "starting Monav routing server"
                    self.monav.startServer()
                controller.status = "Monav offline routing in progress"
                result = self.monav.monavDirections(waypoints)
                controller.status = "Monav offline routing done"
            except Exception:
                log.exception('Monav route lookup failed')

            if result is None: # routing failed for unknown reasons
                return RoutingResult(None, routeParams)
            if result.type == result.SUCCESS:
                # convert the Monav result to a Way object usable
                # for turn-by-turn navigation using the instruction
                # generator set in the Monav wrapper
                route = way.fromMonavResult(result, self.monav.result2turns)
                return RoutingResult(route,
                                     routeParams,
                                     constants.ROUTING_SUCCESS,
                                     lookupDuration=time.time() - routingStart)
            elif result.type == result.LOAD_FAILED:
                return RoutingResult(None, routeParams, constants.ROUTING_LOAD_FAILED)
            elif result.type == result.LOOKUP_FAILED:
                return RoutingResult(None, routeParams, constants.ROUTING_LOOKUP_FAILED)
            elif result.type == result.ROUTE_FAILED:
                RoutingResult(None, routeParams, constants.ROUTING_ROUTE_FAILED)
            else:
                return RoutingResult(None, routeParams)
        else:
            log.error("no Monav routing data - can't route")
            RoutingResult(None, routeParams, constants.ROUTING_NO_DATA)

class GoogleRouting(RoutingProvider):
    """An online provider that does online
    point to point routing using Google API"""
    def __init__(self):
        threadName = constants.THREAD_ROUTING_ONLINE_GOOGLE
        RoutingProvider.__init__(self, threadName=threadName)

    def search(self, waypoints, routeParams=RouteParameters(), controller=DummyController()):
        # check if we have at least 2 points
        routingStart = time.time()
        if len(waypoints) < 2:
            log.error("GoogleRouting provider: ERROR, need at least 2 points for routing")
            return RoutingResult(None, routeParams)
        start = waypoints[0]
        destination = waypoints[-1]
        inBetweenPoints = waypoints[1:-1]
        log.info("GoogleRouting: routing from %s to %s", start, destination)
        controller.status = "online routing in progress"
        route, returnCode, errorMessage = _googleDirections(start, destination, inBetweenPoints, routeParams)
        controller.status = "online routing done"
        # return the data from the routing function and add elapsed time in ms
        return RoutingResult(route,
                             routeParams,
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
        if not isinstance(start, six.string_types):
            start = "%f,%f" % (start.lat, start.lon)
        if not isinstance(destination, six.string_types):
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
            route = way.fromGoogleDirectionsResult(directions)
        else:
            route = None
        return route, returnCode, errorMessage


















