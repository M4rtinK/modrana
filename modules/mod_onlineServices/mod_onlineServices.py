#!/usr/bin/python
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
from base_module import ranaModule
import re
import urllib
import threading
import time
import geocoding
import geonames
import local_search

DEFAULT_GOOGLE_API_KEY = "ABQIAAAAv84YYgTIjdezewgb8xl5_xTKlax5G-CAZlpGqFgXfh-jq3S0yRS6XLrXE9CkHPS6KDCig4gHvHK3lw"

def getModule(m, d, i):
  return(onlineServices(m, d, i))


class onlineServices(ranaModule):
  """A module for talking to various online services"""

  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.workerThreads = []
    self.drawOverlay = False

  #  # testing
  #  def firstTime(self):
  #    self._enableOverlay()

  def handleMessage(self, message, type, args):
    if message == "cancelOperation":
      """this message is sent when the user presses the "cancel search" button
         it should:
         * make sure there are no results returned after the button is pressed
         * remove the cancel button and the "working" overlay """
      self.stop()

  def _disableOverlay(self):
    """disable the "working" overlay + disable the timestamp"""
    self.sendMessage('ml:notification:workInProgressOverlay:disable')
    self.workStartTimestamp = None

  def geocode(self, address):
    """synchronous geocoding"""
    return geocoding.geocode(address)

  def geocodeAsync(self, address, outputHandler, key):
    """asynchronous geocoding"""
    flags = {'net': True}
    self._addWorkerThread(Worker._onlineGeocoding, [address], outputHandler, key, flags)

  def localSearch(self, term, where=None, maxResults=8):
    """Synchronous generic local search query
    * if where is not specified, current position is used
    * returns False if the search failed for some reason
    """
    # we use the Google Local Search backend at the moment

    if where is None: # use current position coordinates
      pos = self.get("pos", None)
      if pos is None:
        print("onlineServices: can't do local search - current location unknown")
        return False
      else:
        lat, lon = pos
        local = self.googleLocalQueryLL(term, lat, lon)
        if local:
          points = self._processGLSResponse(local)
          return points
        else:
          return []
    else: # use location description provided in where
      queryString = "%s loc:%s" % (term, where)
      local = self.googleLocalQuery(queryString, maxResults)
      if local:
        points = self._processGLSResponse(local)
        return points
      else:
        return []

  def localSearchLL(self, term, lat, lon):
    """Synchronous generic local search query
    * around a point specified by latitude and longitude"""

    # we use the Google Local Search backend at the moment
    local = self.googleLocalQueryLL(term, lat, lon)
    if local:
      points = self._processGLSResponse(local)
      return points
    else:
      return []

  def _processGLSResponse(self, response):
    """load GLS results to LocalSearchPoint objects"""
    results = response['responseData']['results']
    points = []
    for result in results:
      point = local_search.GoogleLocalSearchPoint(result)
      points.append(point)
    return points

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

  def elevFromGeonames(self, lat, lon):
    """get elevation in meters for the specified latitude and longitude from geonames"""
    url = 'http://ws.geonames.org/srtm3?lat=%f&lng=%f' % (lat, lon)
    try:
      query = urllib.urlopen(url)
    except Exception, e:
      "onlineServices: getting elevation from geonames returned an error"
      return 0
    return query.read()

  def elevFromGeonamesBatchAsync(self, latLonList, outputHandler, key, tracklog=None):
    flags = {'net': True}
    self._addWorkerThread(Worker._elevFromGeonamesBatch, [latLonList, tracklog], outputHandler, key, flags)

  def elevFromGeonamesBatch(self, latLonList, threadCB):
    """ get elevation in meters for the specified latitude and longitude from
     geonames synchronously, it is possible to ask for up to 20 coordinates
     at once
    """
    maxCoordinates = 20 #geonames only allows 20 coordinates per query
    latLonElevList = []
    mL = len(latLonList)
    while len(latLonList) > 0:
      if threadCB: # report progress to running thread
        threadCB._setWorkStatusText("%d of %d done" % (mL - len(latLonList), mL))
      tempList = latLonList[0:maxCoordinates]
      #      latLonList = latLonList[maxCoordinates:len(latLonList)]

      lats = ""
      lons = ""
      for point in tempList:
        lats += "%f," % point[0]
        lons += "%f," % point[1]

        # TODO: maybe add switching ?
        #      url = 'http://ws.geonames.org/astergdem?lats=%s&lngs=%s' % (lats,lons)
      url = 'http://ws.geonames.org/srtm3?lats=%s&lngs=%s' % (lats, lons)
      query = None
      try:
        query = urllib.urlopen(url)
      except Exception, e:
        print("online: getting elevation from geonames returned an error")
        results = "0"
        for i in range(1, len(tempList)):
          results += " 0"
      try:
        if query:
          results = query.read().split('\r\n')
          query.close()
      except Exception, e:
        print("online: elevation string from geonames has a wrong format")
        results = "0"
        for i in range(1, len(tempList)):
          results += " 0"

      index = 0
      for point in tempList: # add the results to the new list with elevation
        latLonElevList.append((point[0], point[1], int(results[index])))
        index += 1

    return latLonElevList

  # ** Google Maps **

  def getGmapsInstance(self):
    """get a google maps wrapper instance"""
    key = self.get('googleAPIKey', DEFAULT_GOOGLE_API_KEY)
    if key is None:
      print "onlineServices: a google API key is needed for using the google maps services"
      return None
      # only import when actually needed
    import googlemaps

    gMap = googlemaps.GoogleMaps(key)
    return gMap

  def googleLocalQuery(self, query, maxResults=0):
    print "local search query: %s" % query
    gMap = self.getGmapsInstance()
    if not maxResults:
      maxResults = int(self.get('GLSResults', 8))
    local = gMap.local_search(query, maxResults)
    return local

  def googleLocalQueryLL(self, term, lat, lon):
    query = self.constructGoogleQueryLL(term, lat, lon)
    local = self.googleLocalQuery(query)
    return local

  def constructGoogleQuery(self, term, location):
    """get a correctly formatted GLS query"""
    query = "%s loc:%s" % (term, location)
    return query

  def googleDirectionsAsync(self, start, destination, outputHandler, key):
    """a background running google directions query
       -> verbatim start and destination will be used in route description, no geocoding
       outputHandler will be provided with the results + the specified key string"""
    routeRequestSentTimestamp = time.time() # used for measuring how long the route lookup took

    args = [(start, destination, routeRequestSentTimestamp)]
    flags = {'net': True}
    self._addWorkerThread(Worker._onlineRouteLookup, args, outputHandler, key, flags)

  def googleDirectionsLLAsync(self, start, destination, outputHandler, key):
    """a background running Google Directions query
    - Lat Lon pairs version -> for geocoding the start/destination points (NOT first/last route points)
       outputHandler will be provided with the results + the specified key string"""
    routeRequestSentTimestamp = time.time() # used for measuring how long the route lookup took
    args = [(start, destination, routeRequestSentTimestamp)]
    flags = {'net': True}
    self._addWorkerThread(Worker._onlineRouteLookup, args, outputHandler, key, flags)

  def googleDirections(self, start, destination):
    """ Get driving directions from Google.
    start and directions can be either coordinates tuples or address strings
    """

    otherOptions = ""
    if self.get('routingAvoidHighways', False): # optionally avoid highways
      otherOptions += 'h'
    if self.get('routingAvoidToll', False): # optionally avoid toll roads
      otherOptions += 't'

    # respect travel mode
    mode = self.get('mode', None)
    if mode == 'cycle':
      type = "b"
    elif mode == 'walk':
      type = "w"
    elif mode == 'train' or mode == 'bus':
      type = 'r'
    else:
      type = ""

      # combine type and other parameters
    dir = {}
    # the google language code is the second part of this whitespace delimited string
    googleLanguageCode = self.get('directionsLanguage', 'en en').split(" ")[1]
    dir['hl'] = googleLanguageCode
    directions = self.tryToGetDirections(start, destination, dir, type, otherOptions)

    return directions

  def tryToGetDirections(self, start, destination, dir, travelMode, otherOptions, secondTime=False):
    gMap = self.getGmapsInstance()
    parameters = travelMode + otherOptions
    dir['dirflg'] = parameters
    directions = ""
    # only import when actually needed
    import googlemaps

    try:
      directions = gMap.directions(start, destination, dir)
    except googlemaps.googlemaps.GoogleMapsError, e:
      if e.status == 602:
        print("onlineServices:Gdirections:routing failed -> address not found" % e)
        self.sendMessage("ml:notification:m:Address(es) not found;5")
      elif e.status == 604:
        print("onlineServices:Gdirections:routing failed -> no route found" % e)
        self.sendMessage("ml:notification:m:No route found;5")
      elif e.status == 400:
        if not secondTime: # guard against potential infinite loop for consequent 400 errors
          print("onlineServices:Gdirections:bad response to travel mode, trying default travel mode")
          self.set('needRedraw', True)
          directions = self.tryToGetDirections(start, destination, dir, travelMode="", otherOptions=otherOptions,
            secondTime=True)
      else:
        print("onlineServices:Gdirections:routing failed with exception googlemaps status code:%d" % e.status)
    except Exception, e:
      print("onlineServices:Gdirections:routing failed with non-googlemaps exception:\n%s" % e)
    self.set('needRedraw', True)
    return directions

  def googleDirectionsLL(self, lat1, lon1, lat2, lon2):
    start = (lat1, lon1)
    destination = (lat2, lon2)
    return self.googleDirections(start, destination)

  def _googleReverseGeocode(self, lat, lon):
    gMap = self.getGmapsInstance()
    address = gMap.latlng_to_address(lat, lon)
    return address

  def reverseGeocodeAsync(self, lat, lon, outputHandler, key, message="geocoding"):
    """asynchronous reverse geocoding"""
    flags = {'net': True}
    self._addWorkerThread(Worker._reverseGeocode, [lat, lon, message], outputHandler, key, flags)

  def googleLocalQueryLLAsync(self, term, lat, lon, outputHandler, key):
    """asynchronous Google Local Search query for explicit lat, lon coordinates"""
    location = "%f,%f" % (lat, lon)
    self.googleLocalQueryAsync(term, location, outputHandler, key)

  def googleLocalQueryPosAsync(self, term, outputHandler, key):
    """asynchronous Google Local Search query around current position,
    if current position is unknown, wait for locationTimeout seconds before failing"""
    flags = {
      'GPS': True,
      'net': True
    }
    self._addWorkerThread(Worker._localGoogleSearch, [term], outputHandler, key, flags)

  def googleLocalQueryAsync(self, term, location, outputHandler, key):
    """asynchronous Google Local Search query for """
    print("online: GLS search")
    # TODO: we use a single thread for both routing and search for now, maybe have separate ones ?
    flags = {'net': True}
    self._addWorkerThread(Worker._localGoogleSearch, [term, location], outputHandler, key, flags)

  # ** Wikipedia search (through  Geonames) **

  def wikipediaSearch(self, query):
    return geonames.wikipediaSearch(query)

  def wikipediaSearchAsync(self, query, outputHandler, key):
    flags = {'net': True}
    self._addWorkerThread(Worker._onlineWikipediaSearch, [query], outputHandler, key, flags)

  # ** Background processing **

  def _enableOverlay(self):
    """enable the "working" overlay + set timestamp"""
    self.sendMessage('ml:notification:workInProgressOverlay:enable')
    self.workStartTimestamp = time.time()

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

  def run(self):
    print("onlineServices: worker starting")
    # enable the overlay
    self.online._enableOverlay()
    # check for flags that the method might need
    # before it can bwe started
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
    print("onlineServices: worker finished")
    self.online._done(self)

  def dontReturnResult(self):
    self.returnResult = False

  def _locateCurrentPosition(self, locationTimeout=30):
    """try to locate current position and run search when done or time out"""
    self._setWorkStatusText("GPS fix in progress...")
    sleepTime = 0.5 # in seconds
    pos = None
    fix = 0
    startTimestamp = time.time()
    elapsed = 0
    while elapsed < locationTimeout and self.returnResult:
      pos = self.online.get('pos', None)
      fix = self.online.get('fix', 1)
      if fix > 1 and pos:
        break
      time.sleep(sleepTime)
      elapsed = time.time() - startTimestamp
    if fix > 1 and pos: # got GPS fix ?
      return pos
    else: # no GPS lock
      self._notify("failed to get GPS fix", 5000)
      return None

  def _checkConnectivity(self):
    """check Internet connectivity - if no Internet connectivity is available, wait for up to 30 seconds
    and then fail (this is used to handle cases where the device was offline and the Internet connection is
    just being established)"""
    status = self.online.modrana.dmod.getInternetConnectivityStatus()
    if status is None: # Connectivity status monitoring not supported
      return status # skip
    elif status == True:
      return status # Internet connectivity is most probably available
    elif status == False:
      startTimestamp = time.time()
      self._setWorkStatusText("waiting for Internet connectivity...")
      elapsed = 0
      while elapsed < 30 and self.returnResult:
        status = self.online.modrana.dmod.getInternetConnectivityStatus()
        print('online: waiting for internet connectivity')
        print(status)
        if status == True or status is None:
          break
        time.sleep(1)
        elapsed = time.time() - startTimestamp
      return status
    else:
      print('online: warning, unknown connection status:')
      print(status)
      return status

  def _notify(self, message, msTimeout):
    if self.flags.get('notify', True):
      self.online.notify(message, msTimeout)

  def _setWorkStatusText(self, text):
    self.statusMessage = text
    notification = self.online.m.get('notification', None)
    if notification:
      notification.setWorkInProgressOverlayText(text)

  # Google
  def _onlineRouteLookup(self, query):
    """this method online route lookup and is called by the worker thread"""
    (start, destination, routeRequestSentTimestamp) = query
    print("worker: routing from %s to %s" % (start, destination))
    self._setWorkStatusText("online routing in progress...")
    # get the route
    directions = self.online.googleDirections(start, destination)
    self._setWorkStatusText("online routing done   ")
    # return result to the thread to handle
    return directions, start, destination, routeRequestSentTimestamp

  def _localGoogleSearch(self, term, location=None):
    if location:
      query = self.online.constructGoogleQuery(term, location)
    else:
      # use current position:
      pos = self.online.get('pos', None)
      if pos:
        location = "%f,%f" % pos
        query = self.online.constructGoogleQuery(term, location)
      else:
        print('online: local search: search location unknown')
        return None

    # Local Search doesn't like the geo: prefix so we remove it
    query = re.sub("loc:.*geo:", "loc:", query)

    """this method performs Google Local online-search and is called in the worker thread"""
    print("onlineServices: performing GLS")
    self._setWorkStatusText("online POI search in progress...")
    result = self.online.googleLocalQuery(query)
    self._setWorkStatusText("online POI search done   ")
    return result

  def _onlineGeocoding(self, address):
    self._setWorkStatusText("online geocoding in progress...")
    result = self.online.geocode(address)
    self._setWorkStatusText("online geocoding done   ")
    return result

  def _reverseGeocode(self, lat, lon, message):
    """do blocking reverse geocoding using one of the available methods
    -> this method is run from the worker thread"""
    print("onlineServices: reverse geocoding")
    self._setWorkStatusText("%s..." % message)
    #TODO: support other reverse geocoding methods than Google
    address = self.online._googleReverseGeocode(lat, lon)
    self._setWorkStatusText("geocoding done.")
    return address

  # Geonames

  def _elevFromGeonamesBatch(self, latLonList, tracklog):
    try:
      self._setWorkStatusText("online elevation lookup starting...")
      results = self.online.elevFromGeonamesBatch(latLonList)
      self._setWorkStatusText("online elevation lookup done   ")
      return results, tracklog
    except Exception, e:
      print('onlineServices: exception during elevation lookup:\n', e)
      return None, tracklog

  def _onlineWikipediaSearch(self, query):
    self._setWorkStatusText("online Wikipedia search in progress...")
    result = self.online.wikipediaSearch(query)
    self._setWorkStatusText("online Wikipedia search done   ")
    return result
