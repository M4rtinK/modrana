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
import urllib
import threading
import time
import geocoding
import geonames

def getModule(m,d,i):
  return(onlineServices(m,d,i))

class onlineServices(ranaModule):
  """Module for communication with various online services."""
  
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
      
  def elevFromGeonames(self, lat, lon):
    """get elevation in meters for the specified latitude and longitude from geonames"""
    url = 'http://ws.geonames.org/srtm3?lat=%f&lng=%f' % (lat,lon)
    try:
      query = urllib.urlopen(url)
    except:
      "onlineServices: getting elevation from geonames returned an error"
      return 0
    return query.read()

  def elevFromGeonamesBatchAsync(self, latLonList, outputHandler, key, tracklog=None):
    self._addWorkerThread(self._elevFromGeonamesBatch, [latLonList, tracklog], outputHandler, key)

  def _elevFromGeonamesBatch(self, latLonList, tracklog):
    try:
      self._setWorkStatusText("online elevation lookup starting...")
      results = self.elevFromGeonamesBatch(latLonList)
      self._setWorkStatusText("online elevation lookup done   ")
      return (results, tracklog) 
    except Exception, e:
      print('onlineServices: exception suring elevation lookup:\n',e)
      return (None,tracklog)


  def elevFromGeonamesBatch(self, latLonList):
    """
    get elevation in meters for the specified latitude and longitude from geonames
    it is possible to ask for up to 20 coordinates at once
    """
    maxCoordinates = 20 #geonames only allows 20 coordinates per query
    latLonElevList = []
    tempList = []
    mL = len(latLonList)
    while len(latLonList) > 0:
      self._setWorkStatusText("%d of %d done" % (mL-len(latLonList),mL) )
      tempList = latLonList[0:maxCoordinates]
      latLonList = latLonList[maxCoordinates:len(latLonList)]

      lats = ""
      lons = ""
      for point in tempList:
        lats += "%f," % point[0]
        lons += "%f," % point[1]

# TODO: maybe add switching ?
#      url = 'http://ws.geonames.org/astergdem?lats=%s&lngs=%s' % (lats,lons)
      url = 'http://ws.geonames.org/srtm3?lats=%s&lngs=%s' % (lats,lons)
      try:
        query = urllib.urlopen(url)
      except:
        "onlineServices: getting elevation from geonames returned an error"
        results = "0"
        for i in range(1, len(tempList)):
          results = results + " 0"
      try:
        results = query.read().split('\r\n')
        query.close()
      except:
        "onlineServices: elevation string from geonames has a wrong format"
        results = "0"
        for i in range(1, len(tempList)):
          results = results + " 0"

      index = 0
      for point in tempList: # add the results to the new list with elevation
        latLonElevList.append((point[0],point[1],int(results[index])))
        index = index +1

    return latLonElevList

  def getGmapsInstance(self):
    """get a google maps wrapper instance"""
    key = self.get('googleAPIKey', None)
    if key == None:
      print "onlineServices: a google API key is needed for using the google maps services"
      return None
    # only import when actually needed
    import googlemaps
    gmap = googlemaps.GoogleMaps(key)
    return gmap

  def googleLocalQuery(self, query):
    print "local search query: %s" % query
    gmap = self.getGmapsInstance()
    numresults = int(self.get('GLSResults', 8))
    local = gmap.local_search(query, numresults)
    return local

  def googleLocalQueryLL(self, term, lat, lon):
    query = self.constructGoogleQueryLL(term, lat, lon)
    local = self.googleLocalQuery(query)
    return local

  def constructGoogleQueryLL(self, term, lat, lon):
    """get a correctly formated GLS query"""
    sufix = " loc:%f,%f" % (lat,lon)
    query = term + sufix
    return query

  def googleDirectionsAsync(self, start, destination, outputHandler, key):
    """a background running google directions query
       -> verbatim start and destination will be used in route description, no geocoding
       outputHandler will be provided with the results + the specified key string"""
    routeRequestSentTimestamp = time.time() # used for measuring how long the route lookup took
    self._addWorkerThread(self._onlineRouteLookup, [(start, destination, routeRequestSentTimestamp), "normal"], outputHandler, key)
    
  def googleDirectionsLLAsync(self, start, destination, outputHandler, key):
    """a background running googledirections query
    - Lat Lon pairsversion -> for geocoding the start/destination points (NOT first/last route points)
       outputHandler will be provided with the results + the specified key string"""
    routeRequestSentTimestamp = time.time() # used for measuring how long the route lookup took
    self._addWorkerThread(self._onlineRouteLookup, [(start, destination, routeRequestSentTimestamp), "LL"], outputHandler, key)

  def googleDirections(self ,start, destination):
    '''
    Get driving directions from Google.
    start and directions can be either coordinates tupples or address strings
    '''

    otherOptions=""
    if self.get('routingAvoidHighways', False): # optionally avoid highways
      otherOptions = otherOptions + 'h'
    if self.get('routingAvoidToll', False): # optionally avoid toll roads
      otherOptions = otherOptions + 't'

    # respect travel mode
    mode = self.get('mode', None)
    if mode == 'cycle':
      type = "b"
    elif mode == 'foot':
      type = "w"
    elif mode == 'train' or mode == 'bus':
      type = 'r'
    else:
      type = ""

     # combine type and aother parameters
    dir = {}
    # the google language code is the seccond part of this whitespace delimited string
    googleLanguageCode = self.get('directionsLanguage', 'en en').split(" ")[1]
    dir['hl'] = googleLanguageCode
    directions = self.tryToGetDirections(start, destination, dir, type, otherOptions)

    return directions

  def tryToGetDirections(self, start, destination, dir, travelMode, otherOptions, seccondTime=False):
    gmap = self.getGmapsInstance()
    parameters = travelMode + otherOptions
    dir['dirflg'] = parameters
    directions = ""
    # only import when actually needed
    import googlemaps
    try:
      directions = gmap.directions(start, destination, dir)
    except googlemaps.googlemaps.GoogleMapsError, e:
      if e.status == 602:
        print "onlineServices:Gdirections:routing failed -> address not found" % e
        self.sendMessage("ml:notification:m:Address(es) not found;5")
      elif e.status == 604:
        print "onlineServices:Gdirections:routing failed -> no route found" % e
        self.sendMessage("ml:notification:m:No route found;5")
      elif e.status == 400:
        if not seccondTime: # guard against potential infinite loop for consequent 400 errors
          print "onlineServices:Gdirections:bad response to travel mode, trying default travel mode"
          self.set('needRedraw', True)
          directions = self.tryToGetDirections(start, destination, dir, travelMode="",otherOptions=otherOptions ,seccondTime=True)
      else:
        print "onlineServices:Gdirections:routing failed with exception googlemaps status code:%d" % e.status
    except Exception, e:
      print "onlineServices:Gdirections:routing failed with non-googlemaps exception:\n%s" % e
    self.set('needRedraw', True)
    return directions

  def googleDirectionsLL(self ,lat1, lon1, lat2, lon2):
    start = (lat1, lon1)
    destination = (lat2, lon2)
    return self.googleDirections(start, destination)

  def googleReverseGeocode(self, lat, lon):
    gmap = self.getGmapsInstance()
    address = gmap.latlng_to_address(lat,lon)
    return address

  def _enableOverlay(self):
    """enable the "working" overlay + set timestamp"""
    self.sendMessage('ml:notification:workInProgressOverlay:enable')
    self.workStartTimestamp = time.time()

  def _disableOverlay(self):
    """disable the "working" overlay + disable the timestamp"""
    self.sendMessage('ml:notification:workInProgressOverlay:disable')
    self.workStartTimestamp = None

  def googleLocalQueryLLAsync(self, term, lat, lon,outputHandler, key):
    """asynchronous Google Local Search query for explicit lat, lon coordiantes"""
    query = self.constructGoogleQueryLL(term, lat, lon)
    self.googleLocalQueryAsync(query, outputHandler, key)
    
  def googleLocalQueryAsync(self,query,outputHandler, key):
    """asynchronous Google Local Search query for """
    print "onlineServices: GLS search"
    # TODO: we use a single thread for both routing and search for now, maybe have separate ones ?
    self._addWorkerThread(self._localGoogleSearch, [query], outputHandler, key)

  def _localGoogleSearch(self, query):
    """this method performs Google Local online-search and is called by the worker thread"""
    print "onlineServices: performing GLS"
    self._setWorkStatusText("online POI search in progress...")
    result = self.googleLocalQuery(query)
    self._setWorkStatusText("online POI search done   ")
    return result

  def _onlineRouteLookup(self, query, type):
    """this method online route lookup and is called by the worker thread"""
    (start, destination, routeRequestSentTimestamp) = query
    print "worker: routing from",start," to ",destination
    self._setWorkStatusText("online routing in progress...")
    # get the route
    directions = self.googleDirections(start, destination)

    if type == "LL":
      # reverse geocode the start and destination coordinates (for the info menu)
      (fromLat,fromLon) = start
      (toLat,toLon) = destination
      self._setWorkStatusText("geocoding start...")
      startAddress = self.googleReverseGeocode(fromLat,fromLon)
      self._setWorkStatusText("geocoding destination...")
      destinationAddress = self.googleReverseGeocode(toLat,toLon)
      # return the original start/dest coordinates
      startLL = start
      destinationLL = destination
    else:
      # signalize that the original start/dest coordinates are unknown
      startAddress = start
      destinationAddress = destination
      startLL = None
      destinationLL = None
    self._setWorkStatusText("online routing done   ")
    # return result to the thread to handle
    return (directions, startAddress, destinationAddress, startLL, destinationLL, routeRequestSentTimestamp)

  def geocode(self, address):
    return geocoding.geocode(address)

  def geocodeAsync(self, address, outputHandler, key):
    self._addWorkerThread(self._onlineGocoding, [address], outputHandler, key)

  def _onlineGocoding(self, address):
    self._setWorkStatusText("online geocoding in progress...")
    result = self.geocode(address)
    self._setWorkStatusText("online geocoding done   ")
    return result

  def wikipediaSearch(self, query):
    return geonames.wikipediaSearch(query)

  def wikipediaSearchAsync(self, query, outputHandler, key):
    self._addWorkerThread(self._onlineWikipediaSearch, [query], outputHandler, key)
    
  def _onlineWikipediaSearch(self, query):
    self._setWorkStatusText("online Wikipedia search in progress...")
    result = self.wikipediaSearch(query)
    self._setWorkStatusText("online Wikipedia search done   ")
    return result


  def _setWorkStatusText(self, text):
    notification = self.m.get('notification', None)
    if notification:
      notification.setWorkInProgressOverlayText(text)

  def _addWorkerThread(self, *args):
    """start the worker thread and provide it the specified arguments"""
    w = self.Worker(self,*args)
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
    def __init__(self,callback, call, args, outputHandler, key):
      threading.Thread.__init__(self)
      self.callback = callback # should be a onlineServicess module instance
      self.call = call
      self.args = args
      self.outputHandler = outputHandler
      self.key = key # a key for the output handler
      self.statusMessage = ""
      self.returnResult = True
    def run(self):
      print("onlineServices: worker starting")
      # enable the overlay
      self.callback._enableOverlay()
      # call the provided method asynchronously from modRana main thread
      result = self.call(*self.args) # with the provided arguments
      if self.returnResult: # check if our result is expected and should be returned to the oputpt handler
        self.outputHandler(self.key, result)
            
      # cleanup
      print("onlineServices: worker finished")
      self.callback._done(self)

    def dontReturnResult(self):
      self.returnResult = False

if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
