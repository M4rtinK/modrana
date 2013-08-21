# -*- coding: utf-8 -*-
# Offline routing providers
import time
from core import constants
from core import way
from core.backports import six

try:
    import json
except ImportError:
    import simplejson as json

from core.providers import RoutingProvider, DummyController, RouteParameters

class MonavRouting(RoutingProvider):
    """An online provider that does online
    point to point routing using Google API"""
    def __init__(self):
        threadName = constants.THREAD_ROUTING_ONLINE_GOOGLE
        RoutingProvider.__init__(self, threadName=threadName)


class GoogleRouting(RoutingProvider):
    """An online provider that does online
    point to point routing using Google API"""
    def __init__(self):
        threadName = constants.THREAD_ROUTING_ONLINE_GOOGLE
        RoutingProvider.__init__(self, threadName=threadName)

    def search(self, waypoints, routeParams=None, controller=DummyController()):
        # check if we have at least 2 points
        routingStart = time.time()
        if len(waypoints) < 2:
            print("GoogleRouting provider: ERROR, need at least 2 points for routing")
            return None
        start = waypoints[0]
        destination = waypoints[-1]
        inBetweenPoints = waypoints[1:-1]
        if routeParams is None:
            routeParams = RouteParameters()
        print("GoogleRouting: routing from %s to %s" % (start, destination))
        controller.status = "online routing in progress"
        route, errorMessage = _googleDirections(start, destination, inBetweenPoints, routeParams)
        controller.status = "online routing done"
        # return the route, errorMessage and elapsed time in seconds
        return route, errorMessage, time.time() - routingStart

def _getGmapsInstance():
    """get a google maps wrapper instance"""
    key = constants.GOOGLE_API_KEY
    if key is None:
        print("onlineServices: online providers:"
              " a google API key is needed for using the google maps services")
        return None
        # only import when actually needed
    from modules import googlemaps
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

        otherOptions = ""
        if params.avoidHighways: # optionally avoid highways
            otherOptions += 'h'
        if params.avoidTollRoads: # optionally avoid toll roads
            otherOptions += 't'
        waypointOption = None
        if waypoints: # waypoints are a list of Point objects
            firstWayPoint = waypoints[0]
            waypointOption = "%f,%f" % (firstWayPoint.lat, firstWayPoint.lon)
            for waypoint in waypoints[1:]:
                waypointOption += "|%f,%f" % (waypoint.lat, waypoint.lon)

        # respect travel mode
        directionsType = ""
        if params.routeMode == constants.ROUTE_BIKE:
            directionsType = "b"
        elif params.routeMode == constants.ROUTE_PEDESTRIAN:
            directionsType = "w"
        # TODO: check if/how public transport routing works
        #elif mode == 'train' or mode == 'bus':
        #    directionsType = 'r'
        #else:
        #    directionsType = ""

        # combine mode and other parameters
        flagDir = {'language': params.language}
        # the google language code is the second part of this whitespace delimited string
        #googleLanguageCode = self.get('directionsLanguage', 'en en').split(" ")[1]

        gMap = _getGmapsInstance()
        parameters = directionsType + otherOptions
        flagDir['dirflg'] = parameters
        if waypointOption:
            flagDir['waypoints'] = waypointOption
        flagDir['sensor'] = 'false'
        directions = ""
        # only import the googlemaps module when actually needed
        from modules import googlemaps

        errorMessage = ""

        try:
            directions = gMap.directions(start, destination, flagDir)
        except googlemaps.GoogleMapsError:
            import sys
            e = sys.exc_info()[1]

            if e.status == 602:
                print("online providers: Google routing failed -> address not found")
                print(e)
                errorMessage = "Address(es) not found"
            elif e.status == 604:
                print("online providers: Google routing failed -> no route found")
                print(e)
                errorMessage = "No route found"
            elif e.status == 400:
                print("online providers: Google routing failed with googlemaps exception,"
                      " googlemaps status code:%d" % e.status)
        except Exception:
            import sys
            import traceback
            e = sys.exc_info()[1]
            print("onlineServices:GDirections:routing failed with non-googlemaps exception")
            print(e)
            traceback.print_exc(file=sys.stdout) # find what went wrong

        # convert the directions datastructure returned by Google
        # to modRana Way object
        route = way.fromGoogleDirectionsResult(directions)
        return route, errorMessage


















