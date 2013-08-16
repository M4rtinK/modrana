# -*- coding: utf-8 -*-
# Geographic information providers

from core import threads, constants


class DummyController(object):
    """A default dummy object that implements the
    task controller interface that modRanaThreads have"""

    def __init__(self):
        self.status = None
        self.progress = None


class POIProvider(object):
    def __init__(self, threadName=constants.THREAD_POI_SEARCH):
        self._threadName = threadName

    def search(self, term=None, around=None, controller=DummyController()):
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

    def searchAsync(self, callback, term=None, around=None):
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

class RoutingProvider(object):
    def __init__(self, threadName=constants.THREAD_POI_SEARCH):
        self._threadName = threadName

    def search(self, waypoints, routeParams=None, controller=DummyController()):
        """Search for a route given by a list of points
        :param waypoints: 2 or more waypoints for route search
        -> the first point is the start, the last one is the destination
        -> any point in between are regarded as waypoints the route has to go through
        NOTE: not all providers might support waypoints
        :type waypoints: list
        :param routeParams: further parameters for the route search
        :type routeParams: RouteParameters instance
        :param controller: task controller
        :returns: a list of routes (Way objects), None if search failed
        :rtype: list
        """
        pass

    def searchAsync(self, callback, waypoints, routeParams=None):
        """Search for a route given by a list of points asynchronously
        :param waypoints: 2 or more waypoints for route search
        -> the first point is the start, the last one is the destination
        -> any point in between are regarded as waypoints the route has to go through
        NOTE: not all providers might support waypoints
        :type waypoints: list
        :param routeParams: further parameters for the route search
        :type routeParams: RouteParameters instance
        :param controller: task controller
        :returns: a list of routes (Way objects), None if search failed
        :rtype: list
        """
        pass
        # lambda is used to pass all needed arguments to the search function
        # and passing the result to the callback,
        # but not actually executing it until the thread is started
        thread = threads.ModRanaThread(name=self._threadName)
        thread.target = lambda: self.search(
            waypoints=waypoints,
            routeParams=routeParams,
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
                 avoidTollRoads=False,
                 avoidHighways=False,
                 routeMode=constants.ROUTE_CAR,
                 language=constants.ROUTE_DEFAULT_LANGUAGE ):
        self._avoidTollRoads = avoidTollRoads
        self._avoidHighways = avoidHighways
        self._routeMode = routeMode
        self._language = language

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

