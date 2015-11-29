# -*- coding: utf-8 -*-
# Geographic information providers

from core import threads, constants

class DummyController(object):
    """A default dummy object that implements the
    task controller interface that modRanaThreads have"""

    def __init__(self):
        self.status = None
        self.progress = None
        self.callback = None


class POIProvider(object):
    def __init__(self, threadName=constants.THREAD_POI_SEARCH):
        self._threadName = threadName

    def search(self, term=None, around=None, controller=DummyController(), **kwargs):
        """Search for POI using a textual search query
        :param term: search term
        :type term: str
        :param around: optional location bias
        :type around: Point instance
        :param controller: task controller
        :returns: a list of points, None if search failed
        :rtype: list
        """
        pass

    def searchAsync(self, callback, term=None, around=None, **kwargs):
        """Perform asynchronous search
        :param callback: result handler
        :type term: a callable
        :param term: search term
        :type term: str
        :param around: optional location bias
        :type around: Point instance
        """
        # lambda is used to pass all needed arguments to the search function
        # and passing the result to the callback,
        # but not actually executing it until the thread is started
        thread = threads.ModRanaThread(name=self._threadName)
        thread.target = lambda: self.search(
            term=term,
            around=around,
            controller=thread,
            **kwargs
        )
        thread.callback = callback

        # and yet, this really works :)
        # - we need to set the target, and it seems this can only be done in init
        # - passing the thread itself as controller seems to work or at least does
        # not raise any outright exception

        # register the thread by the thread manager
        # (this also starts the thread)
        threads.threadMgr.add(thread)

    @property
    def threadName(self):
        """Return name of the thread used for asynchronous search"""
        return self._threadName

class RoutingProvider(object):
    def __init__(self, threadName=constants.THREAD_POI_SEARCH):
        self._threadName = threadName

    def search(self, waypoints, route_params=None, controller=DummyController()):
        """Search for a route given by a list of points
        :param waypoints: 2 or more waypoints for route search
        -> the first point is the start, the last one is the destination
        -> any point in between are regarded as waypoints the route has to go through
        NOTE: not all providers might support waypoints
        :type waypoints: list
        :param route_params: further parameters for the route search
        :type route_params: RouteParameters instance
        :param controller: task controller
        :returns: a list of routes (Way objects), None if search failed
        :rtype: list
        """
        pass

    def searchAsync(self, callback, waypoints, route_params=None):
        """Search for a route given by a list of points asynchronously
        :param waypoints: 2 or more waypoints for route search
        -> the first point is the start, the last one is the destination
        -> any point in between are regarded as waypoints the route has to go through
        NOTE: not all providers might support waypoints
        :type waypoints: list
        :param route_params: further parameters for the route search
        :type route_params: RouteParameters instance
        :param controller: task controller
        :returns: a list of routes (Way objects), None if search failed
        :rtype: list
        """
        # lambda is used to pass all needed arguments to the search function
        # and passing the result to the callback,
        # but not actually executing it until the thread is started
        thread = threads.ModRanaThread(name=self._threadName)
        thread.target = lambda: self.search(
            waypoints=waypoints,
            route_params=route_params,
            controller=thread
        )
        thread.callback = callback

        # and yet, this really works :)
        # - we need to set the target, and it seems this can only be done in init
        # - passing the thread itself as controller seems to work or at least does
        # not raise any outright exception

        # register the thread by the thread manager
        # (this also starts the thread)
        threads.threadMgr.add(thread)

    @property
    def threadName(self):
        """Return name of the thread used for asynchronous search"""
        return self._threadName

class RouteParameters(object):
    def __init__(self,
                 routeMode=constants.ROUTE_CAR,
                 avoidTollRoads=False,
                 avoidHighways=False,
                 language=constants.ROUTE_DEFAULT_LANGUAGE,
                 addressRoute=False):
        self._avoidTollRoads = avoidTollRoads
        self._avoidHighways = avoidHighways
        self._routeMode = routeMode
        self._language = language
        self._addressRoute = addressRoute

    @property
    def avoidTollRoads(self):
        return self._avoidTollRoads

    @property
    def avoidHighways(self):
        return self._avoidHighways

    @property
    def routeMode(self):
        return self._routeMode

    @property
    def language(self):
        return self._language

    @property
    def language(self):
        return self._language

    @property
    def addressRoute(self):
        """When addressRoute is True, the start and destination of the route
        is described using textual point descriptions
        Example: start=London, destination=Berlin

        Additional waypoints can be either textual descriptions or ordinary Point objects
        """
        return self._addressRoute

    @addressRoute.setter
    def addressRoute(self, value):
        self._addressRoute = value

    def __str__(self):
        description = "Route parameters\n"
        description+= "route mode: %s, language: %s\n" % (self.routeMode, self.language)
        description+= "avoid major highways: %s, avoid toll roads: %s\n" % (self.avoidHighways, self.avoidTollRoads)
        description+= "address route: %s" % self.addressRoute
        return description

class RoutingResult(object):
    """This class acts as a wrapper for the results of a routing lookup,
    the main "payload" is the route object, but it also wraps other
    fields mainly used for error reporting in case that the route lookup is
    not successful
    """

    def __init__(self, route, routeParameters, returnCode=None,
                 errorMessage=None, lookupDuration=0):
        """
        :param route: The route for the road lookup
        :type route: a Way instance or None
        :param routeParameters: routing parameters for the rout lookup
        :type routeParameters: RouteParameters instance
        :param returnCode: return code for the road lookup
        :param errorMessage: an error message string (if any)
        :type errorMessage: a string or None
        """
        self._route = route
        self._routeParameters = routeParameters
        self._returnCode = returnCode
        self._errorMessage = errorMessage
        self._lookupDuration = lookupDuration # in milliseconds

    @property
    def route(self):
        return self._route

    @property
    def routeParameters(self):
        return self._routeParameters

    @property
    def returnCode(self):
        return self._returnCode

    @property
    def errorMessage(self):
        return self._errorMessage

    @property
    def lookupDuration(self):
        return self._lookupDuration


