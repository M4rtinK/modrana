# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Module for communication with various online services.
#----------------------------------------------------------------------------
# Copyright 2010, Martin Kolman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#---------------------------------------------------------------------------
from core import constants
from core import point
from core import threads
from modules.base_module import RanaModule
import traceback
import sys
import re
import threading
import time
from . import geocoding
from . import geonames
from . import local_search
from . import online_providers
from . import offline_providers

import logging
log = logging.getLogger("mod.onlineServices")

def getModule(*args, **kwargs):
    return OnlineServices(*args, **kwargs)


class OnlineServices(RanaModule):
    """A module for talking to various online services"""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self.workerThreads = []
        self.drawOverlay = False
        self.workStartTimestamp = None
        self._connectingCondition = threading.Condition()
        # TODO: move to location ?
        self._initGPSCondition = threading.Condition()


    #  # testing
    #  def firstTime(self):
    #    self._enableOverlay()

    def handleMessage(self, message, messageType, args):
        if message == "cancelOperation":
            # this message is sent when the user presses the "cancel search" button
            # it should:
            # * make sure there are no results returned after the button is pressed
            # * remove the cancel button and the "working" overlay
            self.stop()

    def _disableOverlay(self):
        """disable the "working" overlay + disable the timestamp"""
        self.sendMessage('ml:notification:workInProgressOverlay:disable')
        self.workStartTimestamp = None

    def geocode(self, address):
        """Synchronous geocoding"""
        # TODO: provider switching
        return online_providers.GeocodingNominatim().search(term=address)

    def geocodeAsync(self, address, callback):
        """Asynchronous geocoding"""
        # get appropriate provider
        if self.get("placeSearchNominatimEnabled"):
            provider = online_providers.GeocodingNominatim()
        elif self.get("placeSearchOSMScoutServerEnabled"):
            provider = offline_providers.GeocodingOSMScoutServer()
        else:
            provider = online_providers.GeocodingNominatim()
        #provider = online_providers.TestingProvider()

        provider.searchAsync(callback, term=address)
        return provider.threadName

    def reverseGeocoding(self, searchPoint, callback):
        """Synchronous reverse geocoding"""
        return online_providers.ReverseGeocodingNominatim().search(term=searchPoint)

    def reverseGeocodeAsync(self, searchPoint, callback):
        """Asynchronous reverse geocoding"""
        provider = online_providers.ReverseGeocodingNominatim()
        provider.searchAsync(callback, term=searchPoint)
        return provider.threadName

    def localSearch(self, term, around=None, maxResults=8):
        """Synchronous generic local search query
        * if around is not specified, current position is used
        """
        # we use the Google Local Search backend at the moment
        provider = online_providers.GoogleLocalSearch()
        radius = int(self.get("localSearchRadius", constants.DEFAULT_LOCAL_SEARCH_RADIUS))
        return provider.search(term=term, around=around, maxResults=maxResults,
                               radius=radius)

    def localSearchAsync(self, term, callback, around=None, maxResults=32, sensor='false'):
        radius = int(self.get("localSearchRadius", constants.DEFAULT_LOCAL_SEARCH_RADIUS))
        if self.get("localSearchGoogleEnabled"):
            provider = online_providers.GoogleLocalSearch()
        elif self.get("localSearchOSMScoutServerEnabled"):
            provider = offline_providers.OSMScoutServerLocalSearch()
            # OSM Scout Server currently has some issues with returning nearby
            # results if a big search radius is specified:
            # https://github.com/rinigus/osmscout-server/issues/161
            # so use a smaller radius until the issues fixed or until
            # separate local search radius can be set for OSM Scout Server (ideally both)
            radius = 2000
        else:
            provider = online_providers.GoogleLocalSearch()

        provider.searchAsync(callback, term=term, around=around, maxResults=maxResults,
                             sensor=sensor, radius=radius)
        return provider.threadName

    # ** OSM static map URL **

    def getOSMStaticMapUrl(self, centerLat, centerLon, zl, w=350, h=350, defaultMarker="ol-marker", markerList=None):
        """construct & return OSM static map URL"""
        if not markerList: markerList = []
        prefix = "http://staticmap.openstreetmap.de/staticmap.php"
        center = "?center=%f,%f" % (centerLat, centerLon)
        zoom = "&zoom=%d" % zl
        size = "&size=%dx%d" % (w, h)
        if markerList:
            markers = "&markers="
            for marker in markerList:
                if len(marker) == 2:
                    lat, lon = marker
                    markerName = defaultMarker
                else:
                    lat, lon, markerName = marker
                markers += "%f,%f,%s|" % (lat, lon, markerName)
        else:
            markers = ""

        url = "%s%s%s%s%s" % (prefix, center, zoom, size, markers)
        # remove trailing | if present
        if url[-1] == "|":
            url = url[:-1]
        return url

    # ** Geonames **

    def elevFromGeonamesBatchAsync(self, latLonList, outputHandler, key, tracklog=None):
        flags = {'net': True}
        self._addWorkerThread(Worker._elevFromGeonamesBatch, [latLonList, tracklog], outputHandler, key, flags)


    # ** Google Maps **

    def getGmapsInstance(self):
        """get a google maps wrapper instance"""
        key = constants.GOOGLE_API_KEY
        if not key:
            print("onlineServices: a google API key is needed for using the google maps services")
            return None
            # only import when actually needed
        import googlemaps
        gMap = googlemaps.GoogleMaps(key)
        return gMap

    def _googleReverseGeocode(self, lat, lon):
        gMap = self.getGmapsInstance()
        address = gMap.latlng_to_address(lat, lon)
        return address

    # ** Wikipedia search (through  Geonames) **

    def wikipediaSearch(self, query):
        """Synchronous Wikipedia search - search for georeferenced Wikipedia
        articles for the given query

        :param query: Wikipedia search query
        :type query: str
        :return: a list of Point instances
        :rtype: list
        """
        return online_providers.WikipediaSearchNominatim().search(term=query)

    def wikipediaSearchAsync(self, query, callback):
        """Asynchronous Wikipedia search - search for georeferenced Wikipedia
        articles for the given query

        :param query: Wikipedia search query
        :type query: str
        :return: a list of Point instances
        :rtype: list
        """
        provider = online_providers.WikipediaSearchNominatim()
        provider.searchAsync(callback, term=query)
        return provider.threadName

    # ** Background processing **

    def _addWorkerThread(self, *args):
        """start the worker thread and provide it the specified arguments"""
        w = Worker(self, *args)
        w.daemon = True
        w.start()
        self.workerThreads.append(w)

    def _done(self, thread):
        """a thread reporting it is done"""
        # un-register the thread
        self._unregisterWorkerThread(thread)
        # if no other threads are working, disable the overlay
        if not self.workerThreads:
            self._disableOverlay()

    def stop(self):
        """called after pressing the cancel button"""
        # disable the overlay
        self._disableOverlay()
        # tell all threads not to return results TODO: per thread cancelling
        if self.workerThreads:
            for thread in self.workerThreads:
                thread.dontReturnResult()

    def _unregisterWorkerThread(self, thread):
        if thread in self.workerThreads:
            self.workerThreads.remove(thread)


class Worker(threading.Thread):
    """a worker thread for asynchronous online services access"""

    def __init__(self, callback, call, args, outputHandler, key, flags=None):
        threading.Thread.__init__(self)
        self.online = callback # should be a onlineServices module instance
        self.call = call
        self.args = args
        self.outputHandler = outputHandler
        self.key = key # a key for the output handler
        if not flags: flags = {}
        self.flags = flags
        self.statusMessage = ""
        self.returnResult = True
        self.progress = 0.0

    def run(self):
        log.info("worker starting")
        # check for flags that the method might need
        # before it can be started
        start = True

        if self.flags.get('GPS', False):
            pos = self._locateCurrentPosition()
            if not pos:
                pos = self.online.get('pos', None)
                if pos:
                    self._notify('using last known position', 3000)
                else:
                    self._notify('failed to get GPS fix', 5000)
                    start = False

        if self.flags.get('net', False):
            status = self._checkConnectivity()
            # None - connectivity state unknown
            # False - disconnected
            # True - connected

            if not ((status is None) or (status == True)):
                # don't need to run a job that needs Internet connectivity
                # if no connectivity is available
                self._notify('failed: no Internet connectivity', 5000)
                start = False

        if start: # are we ready to start the main processing ?
            # call the provided method asynchronously from modRana main thread
            result = self.call(self, *self.args) # with the provided arguments
            if self.returnResult: # check if our result is expected and should be returned to the output handler
                self.outputHandler(self.key, result)

        # cleanup
        log.info("worker finished")
        self.online._done(self)

    def dontReturnResult(self):
        self.returnResult = False

    def _notify(self, message, msTimeout):
        if self.flags.get('notify', True):
            self.online.notify(message, msTimeout)

    def _setWorkStatusText(self, text):
        self.statusMessage = text
        #notification = self.online.m.get('notification', None)
        #if notification:
        #    notification.setTaskStatus(self.name, text)

    def _workDone(self):
        notification = self.online.m.get('notification', None)
        if notification:
            notification.removeTask(self.name)

    def _updateProgress(self, progress):
        """progress is a floating point number indicating progress on the current task
        0.0 -> 0%
        0.5 -> 50%
        1.0 -> 100%
        """
        self.progress = progress

    # Geonames

    def _elevFromGeonamesBatch(self, latLonList, tracklog):
        try:
            self._setWorkStatusText("online elevation lookup starting...")
            userAgent = self.online.modrana.configs.user_agent
            results = geonames.elevBatchSRTM(latLonList, self._geonamesCallback, userAgent)
            self._setWorkStatusText("online elevation lookup done   ")
            return results, tracklog
        except Exception:
            log.exception('exception during elevation lookup')
            return None, tracklog

    def _geonamesCallback(self, progress):
        percentDone = 100 - int(100 * progress)
        self._setWorkStatusText("online elevation lookup %d %% done" % percentDone)