#!/usr/bin/python
#----------------------------------------------------------------------------
# Handles downloading of map data
#----------------------------------------------------------------------------
# Copyright 2008, Oliver White
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
from time import sleep
from tilenames import *
from time import clock
import time
import os
import statvfs
import sys
import geo
import string
import urllib, urllib2, threading
from threadpool import threadpool
from threading import Thread
#import socket
#timeout = 30 # this sets timeout for all sockets
#socket.setdefaulttimeout(timeout)



#from modules.pyrender.tilenames import xy2latlon
import sys
if(__name__ == '__main__'):
  sys.path.append('pyroutelib2')
else:
  sys.path.append('modules/pyroutelib2')

import tiledata

def getModule(m,d):
  return(mapData(m,d))

class mapData(ranaModule):
  """Handle downloading of map data"""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.stopThreading = True
    self.currentDownloadList = [] # list of files and urls for the current download batch
    self.currentTilesToGet = [] # used for reporting the (actual) size of the tiles for download
    self.sizeThread = None
    self.getFilesThread = None
    self.aliasForSet = self.set
    self.lastMenuRedraw = 0
    self.notificateOnce = True

  def listTiles(self, route):
    """List all tiles touched by a polyline"""
    tiles = {}
    for pos in route:
      (lat,lon) = pos
      (tx,ty) = tileXY(lat, lon, 15)
      tile = "%d,%d" % (tx,ty)
      if(not tiles.has_key(tile)):
        tiles[tile] = True
    return(tiles.keys())

  def checkTiles(self, tilesToDownload):
    """
    Get tiles that need to be downloaded and look if we dont already have some of these tiles,
    then generate a set of ('url','filename') touples and send them to the threaded downloader
    """

    self.currentTilesToGet = tilesToDownload # this is for displaying the tiles for debugging reasons
    layer = self.get('layer', None) # TODO: manual layer setting
    maplayers = self.get('maplayers', None) # a distionary describing supported maplayers
    extension = maplayers[layer]['type'] # what is the extension for the current layer ?
    alreadyDownloadedTiles = set(os.listdir('cache/images')) # already dowloaded tiles
    tileFolderPath = self.get('tileFolder', None) # where should we store the downloaded tiles

    namingLambda = lambda x: "%s_%d_%d_%d.%s" % (layer,x[2],x[0],x[1],extension) # tile filenames

    tilesToDownload = [x for x in tilesToDownload if namingLambda(x) not in alreadyDownloadedTiles]
    print "Downloading %d new tiles." % len(tilesToDownload)

    # lambda for making tile filenames with path
    namingLambdaWithPath = lambda x: "%s%s_%d_%d_%d.%s" % (tileFolderPath,layer,x[2],x[0],x[1],extension)
    """
    Now we generate a list for the threaded downloader,
    the list is formated like this: ('url', 'folder+filename')
    the downloader downloads url to the specified folder and filename using multiple threads,
    default number of threads i 5 and can be modified in mod_config
    """
    urlsAndFilenames = map(lambda x:(
                                    self.getTileUrl(x[0], x[1], x[2], layer),
                                    namingLambdaWithPath(x)),
                                    tilesToDownload)
#    self.stopThreading = False
#    t = threading.Thread(target=self.getFiles, args=(urlsAndFilenames,))
#    t.start()
    return urlsAndFilenames

  def addToQueue(self, urlsAndFilenames):
    """load urls and filenames to download que"""
    self.currentDownloadList = urlsAndFilenames

  def getTileUrl(self,x,y,z,layer): #TODO: share this with mapTiles
      """Return url for given tile coorindates and layer"""
      maplayers = self.get('maplayers', None)
      extension = maplayers.get('type', 'png')
      layerDetails = maplayers.get(layer, None)
      if layer == 'gmap' or layer == 'gsat':
        url = '%s&x=%d&y=%d&z=%d' % (
          layerDetails['tiles'],
          x,y,z)
      else:
        url = '%s%d/%d/%d.%s' % (
          layerDetails['tiles'],
          z,x,y,
          extension)
      return url

# adapted from: http://www.artfulcode.net/articles/multi-threading-python/
  class FileGetter(threading.Thread):
    def __init__(self, url, filename):
        self.url = url
        self.filename = filename
#        self.result = None
        threading.Thread.__init__(self)

    def getResult(self):
        return self.result

    def run(self):
        try:
            url = self.url
            filename = self.filename
            urllib.urlretrieve(url, filename)
            self.result = filename
            print "download of %s finished" % filename
        except IOError:
            print "Could not open document: %s" % url

  def handleMessage(self, message):
    if(message == "refreshTilecount"):
      size = int(self.get("downloadSize", 4))
      type = self.get("downloadType")
      if(type != "data"):
        print "Error: mod_mapData can't download %s" % type
        return
      
      location = self.get("downloadArea", "here") # here or route

      z = self.get('z', 15) # this is the currewnt zoomlevel as show on the map screen
      minZ = z - int(self.get('zoomUpSize', 0)) # how many zoomlevels up (from current zoomelevel) should we download ?
      if minZ < 0:
        minZ = 0
      maxZ = z + int(self.get('zoomDownSize', 0)) # how many zoomlevels down (from current zoomlevel) should we download ?

      layer = self.get('layer', None)
      maplayers = self.get('maplayers', None)
      if maplayers == None:
        maxZoomLimit == 17
      else:
        maxZoomLimit = maplayers[layer]['maxZoom']

      if maxZ > maxZoomLimit:
        maxZ = 17 #TODO: make layer specific
#      z = currentZ # current Zoomlevel
      diffZ = maxZ - minZ
      midZ = int(minZ + (diffZ/2.0))

      """well, its not exactly middle, its jut a value that decides, if we split down or just round up
         splitting from a zoomlevel too high can lead to much more tiles than requested
         for example, we want tiles for a 10 km radius but we choose to split from a zoomlevel, where a tile is
         20km*20km and our radius intersects four of these tiles, when we split these tiles, we get tiles for an
         are of 40km*40km, instead of the requested 10km
         therefore, zoom level 15 is used as the minimum number for splitting tiles down
         when the maximum zoomlevel from the range requested is less than 15, we dont split at all"""
      if midZ < 15 and maxZ < 15:
        midZ = maxZ
      else:
        midZ = 15
      print "max: %d, min: %d, diff: %d, middle:%d" % (maxZ, minZ, diffZ, midZ)

      if(location == "here"):  
        # Find which tile we're on
        pos = self.get("pos",None)
        if(pos != None):
          (lat,lon) = pos
          # be advised: the xy in this case are not screen coordinates but tile coordinates
          (x,y) = latlon2xy(lat,lon,midZ)
          tilesAroundHere = set(self.spiral(x,y,midZ,size)) # get tiles around our position as a set
          # now get the tiles from other zoomlevels as specified
          zoomlevelExtendedTiles = self.addOtherZoomlevels(tilesAroundHere, midZ, maxZ, minZ)
          # check which tiles we already have
          # this method also return a (url,filename) list of tiles we dont have
          urlsAndFilenames = self.checkTiles(zoomlevelExtendedTiles)
          self.addToQueue(urlsAndFilenames) # load the files to the download que variable

      if(location == "route"):
        loadTl = self.m.get('loadTracklogs', None) # get the tracklog module
        loadedTracklogs = loadTl.tracklogs # get list of all tracklogs
        if loadedTracklogs == None or len(loadedTracklogs) == 0:
          return
        activeTracklogIndex = int(self.get('activeTracklog', 0))
        GPXTracklog = loadedTracklogs[activeTracklogIndex]
        """because we dont need all the information in the original list and
        also might need to add interpolated points, we make a local copy of
        the original list"""
        #latLonOnly = filter(lambda x: [x.latitude,x.longitude])
        trackpointsListCopy = map(lambda x: {'latitude': x.latitude,'longitude': x.longitude}, GPXTracklog.trackpointsList[0])[:]
        tilesToDownload = self.getTilesForRoute(trackpointsListCopy, size, midZ)
        zoomlevelExtendedTiles = self.addOtherZoomlevels(tilesToDownload, midZ, maxZ, minZ)
        # check which tiles we already have
        # this method also return a (url,filename) list of tiles we dont have
        urlsAndFilenames = self.checkTiles(zoomlevelExtendedTiles)
        self.addToQueue(urlsAndFilenames) # load the files to the download que variable

      if(location == "view"):
        proj = self.m.get('projection', None)
        (screenCenterX,screenCenterY) = proj.screenPos(0.5, 0.5) # get pixel coordinates for the screen center
        (lat,lon) = proj.xy2ll(screenCenterX,screenCenterY) # convert to geographic coordinates
        (x,y) = latlon2xy(lat,lon,midZ) # convert to tile coordinates
        tilesAroundView = set(self.spiral(x,y,midZ,size)) # get tiles around these coordinates
        # now get the tiles from other zoomlevels as specified
        zoomlevelExtendedTiles = self.addOtherZoomlevels(tilesAroundView, midZ, maxZ, minZ)
        # check which tiles we already have
        # this method also return a (url,filename) list of tiles we dont have
        urlsAndFilenames = self.checkTiles(zoomlevelExtendedTiles)
        self.addToQueue(urlsAndFilenames) # load the files to the download que variable
        

    if(message == "getSize"):
      """will now ask the server and find the combined size if tiles in the batch"""
      self.set("sizeStatus", 'unknown') # first we set the size as unknown
      urlsAndFilenames = self.currentDownloadList
      print "getting size"
      if len(urlsAndFilenames) == 0:
        print "cant get combined size, the list is empty"
        return
      urls = map(lambda x: x[0], urlsAndFilenames)

      self.totalSize = 0
      maxThreads = self.get('maxSizeThreads', 5)
      sizeThread = self.GetSize(urls, maxThreads) # the seccond parameter is the max number of threads TODO: tweak this
      print  "getSize received, starting sizeThread"
      sizeThread.start()
      self.sizeThread = sizeThread

    if(message == "download"):
      """get tilelist and download the tiles using threads"""
      urlsAndFilenames = self.currentDownloadList
      urlsFilenamesInString = map(lambda x: (x[0]+"*"+x[1]), urlsAndFilenames)
      print "starting download"
      if len(urlsAndFilenames) == 0:
        print "cant download an empty list"
        return
      maxThreads = self.get('maxDlThreads', 5)
      getFilesThread = self.GetFiles(urlsFilenamesInString, maxThreads)
      getFilesThread.start()
      self.getFilesThread = getFilesThread

  def addOtherZoomlevels(self, tiles, tilesZ, maxZ, minZ):
    """expand the tile coverage to other zoomlevels
    maxZ = maximum NUMERICAL zoom, 17 for eaxmple
    minZ = minimum NUMERICAL zoom, 0 for example
    we use two different methods to get the needed tiles:
    * spliting the tiles from one zoomlevel down to the other
    * rounding the tiles cooridnates to get tiles from one zoomlevel up
    we choose a zoomlevel (tilesZ) and then split down and round down from it
    * tilesZ is determined in the handle message method,
    it is the zoomlevel on which we compute which tiles are in our download radius
    -> if tilesZ is too low, this initial tile finding can take too long
    -> if tilesZ is too high, the tiles could be much larger than our dl. radius and we would
    be downloading much more tiles than needed
    => for now, if we get tilesZ (called midZ in handle message) that is lower than 15,
    we set it to the lowest zoomlevel, so we get dont get too much unneeded tiles when splitting
    """
    start = clock()
    extendedTiles = tiles.copy()

    """start of the tile splitting code"""
    previousZoomlevelTiles = None # we will splitt the tiles from the previous zoomlevel
    print "splitting down"
    print range(tilesZ,maxZ)
    for z in range(tilesZ, maxZ): # to max zoom (fo each z we split one zoomlevel down)
      newTilesFromSplit = set() # tiles from the splitting go there
      if previousZoomlevelTiles == None: # this is the first iteration
        previousZoomlevelTiles = tiles.copy()
      for tile in previousZoomlevelTiles:
        x = tile[0]
        y = tile[1]
        """
        now we split each tile to 4 tiles on a higher zoomlevel nr
        see: http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Subtiles
        for a tile with cooridnates x,y:
        2x,2y  |2x+1,2y
        2x,2y+1|2x+1,2y+1
        """
        leftUpperTile = (2*x, 2*y, z+1)
        rightUpperTile = (2*x+1, 2*y, z+1)
        leftLowerTile = (2*x, 2*y+1, z+1)
        rightLowerTile = (2*x+1, 2*y+1, z+1)
        newTilesFromSplit.add(leftUpperTile)
        newTilesFromSplit.add(rightUpperTile)
        newTilesFromSplit.add(leftLowerTile)
        newTilesFromSplit.add(rightLowerTile)
      extendedTiles.update(newTilesFromSplit) # add the new tiles to the main set
      print "we are at z=%d, %d new tiles from %d" % (z, len(newTilesFromSplit), (z+1))
      previousZoomlevelTiles = newTilesFromSplit # set the new tiles s as prev. tiles for next iteration

    """start of the tile cooridnates rounding code"""
    previousZoomlevelTiles = None # we will the tile cooridnates to get tiles for the upper level
    print "rounding up"
    for z in range(tilesZ, minZ, -1):
      newTilesFromRounding = set() # tiles from the rounding go there
      if previousZoomlevelTiles == None: # this is the first iteration
        previousZoomlevelTiles = tiles.copy()
      for tile in previousZoomlevelTiles:
        x = tile[0]
        y = tile[1]
        """as per: http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Subtiles
        we divide each cooridnate with 2 to get the upper tile
        some upper tiles can be found up to four times, so this could be most probably
        optimized if need be (for charting the Jupiter, Sun or a Dyson sphere ? :)"""
        upperTileX = int(x/2.0)
        upperTileY = int(y/2.0)
        upperTile = (upperTileX,upperTileY, z)
        newTilesFromRounding.add(upperTile)
      extendedTiles.update(newTilesFromRounding) # add the new tiles to the main set
      print "we are at z=%d, %d new tiles" % (z, len(newTilesFromRounding))
      previousZoomlevelTiles = newTilesFromRounding # set the new tiles s as prev. tiles for next iteration

      print "nr of tiles after extend: %d" % len(extendedTiles)
    print "Extend took %1.2f ms" % (1000 * (clock() - start))
    return extendedTiles   

  class GetSize(Thread):
    """a class for getting size of files on and url list"""
    def __init__(self, urls, maxThreads=11):
      Thread.__init__(self)
      self.urls=urls
      self.maxThreads=maxThreads
      self.processed = 0
      self.urlCount = len(urls)
      self.totalSize = 0
      self.finished = False
#      self.set("sizeStatus", 'inProgress') # the size is being processed

    def getSizeForURL(self, url):
      """NOTE: getting size info for a sigle tile seems to take from 30 to 130ms on fast connection"""
#      start = clock()
      try:
        url = urllib.urlopen(url) # open url and get mime info
        urlInfo = url.info()
        size = int(urlInfo['Content-Length']) # size in bytes
        url.close()
      except IOError:
        print "Could not open document: %s" % url
        size = 0 # the url errored out, so we just say it  has zero size
#      print "Size lookup took %1.2f ms" % (1000 * (clock() - start))
      return size

    def processURLSize(self, request, result):
      """process the ruseult from the getSize threads"""
      self.processed = self.processed + 1
#      print "**** Size from request #%s: %r b" % (request.requestID, result)
      self.totalSize+=result
#      print "**** Total size: %r B, %d/%d done" % (self.totalSize, self.processed, self.urlCount)

    def run(self):
      start = clock()
      urls=self.urls
      maxThreads=self.maxThreads
      requests = threadpool.makeRequests(self.getSizeForURL, urls, self.processURLSize)
      mainPool = threadpool.ThreadPool(maxThreads)
      print "GetSize: mainPool created"
#      for req in requests:
#          mainPool.putRequest(req)
      map(lambda x: mainPool.putRequest(x) ,requests)
      print "Added %d URLS to check for size." % self.urlCount
      while True:
          try:
              time.sleep(0.5) # this governs how often we check status of the worker threads
              mainPool.poll()
              print "Main thread working...",
              print "(active worker threads: %i)" % (threading.activeCount()-1, )
          except threadpool.NoResultsPending:
              print "**** No pending results."
              print "Total size lookup took %1.2f ms" % (1000 * (clock() - start))
              self.finished = True
              break
#      if mainPool.dismissedWorkers:
#          print "Joining all dismissed worker threads..."
#          mainPool.joinAllDismissedWorkers()


  class GetFiles(Thread):
    def __init__(self, urlsAndFilenames, maxThreads):
      Thread.__init__(self)
      self.urlsAndFilenames = urlsAndFilenames
      self.maxThreads = maxThreads
      self.processed = 0
      self.urlCount = len(urlsAndFilenames)
      self.finished = False

    def saveTileForURL(self, urlAndFilename):
      (url, filename) = urlAndFilename.split('*')
      try:
        urllib.urlretrieve(url,filename) # open url and get mime info
      except IOError:
        print "Could not open document: %s" % url
        return "nok"
      return "ok"

    def processSaveTile(self, request, result):
      #TODO: redownload failed tiles
      self.processed = self.processed + 1
      self.tileThreadingStatus = self.processed
#      print "**** Downloading: %d of %d tiles done. Status:%r" % (self.processed, self.urlCount, result)

    def run(self):
      urlsAndFilenames = self.urlsAndFilenames
      maxThreads = self.maxThreads
      requests = threadpool.makeRequests(self.saveTileForURL, urlsAndFilenames, self.processSaveTile)
      mainPool = threadpool.ThreadPool(maxThreads)
      print "GetFiles: mainPool created"
#      for req in requests:
#          mainPool.putRequest(req)
      map(lambda x: mainPool.putRequest(x) ,requests)
      print "Added %d URLS to check for size." % self.urlCount
      while True:
          try:
              time.sleep(0.5)
              mainPool.poll()
              print "Main thread working...",
              print "(active worker threads: %i)" % (threading.activeCount()-1, )
          except threadpool.NoResultsPending:
              print "**** No pending results."
              self.finished = True
              break
#      if mainPool.dismissedWorkers:
#          print "Joining all dismissed worker threads..."
#          mainPool.joinAllDismissedWorkers()

#  def handleThreExc(self, request, exc_info):
#        if not isinstance(exc_info, tuple):
#            # Something is seriously wrong...
#            print request
#            print exc_info
#            raise SystemExit
#        print "**** Exception occured in request #%s: %s" % \
#          (request.requestID, exc_info)

  def expand(self, tileset, amount=1):
    """Given a list of tiles, expand the coverage around those tiles"""
    tiles = {}
    tileset = [[int(b) for b in a.split(",")] for a in tileset]
    for tile in tileset:
      (x,y) = tile
      for dx in range(-amount, amount+1):
        for dy in range(-amount, amount+1):
          tiles["%d,%d" % (x+dx,y+dy)] = True
    return(tiles.keys())

  def spiral(self, x, y, z, distance):
    (x,y) = (int(round(x)),int(round(y)))
    """for now we are downloading just tiles,
    so I modified this to round the coordinates right after we get them"""
    class spiraller:
      def __init__(self,x,y,z):
        self.x = x
        self.y = y
        self.z = z
        self.tiles = [(x,y,z)]
      def moveX(self,dx, direction):
        for i in range(dx):
          self.x += direction
          self.touch(self.x, self.y, self.z)
      def moveY(self,dy, direction):
        for i in range(dy):
          self.y += direction
          self.touch(self.x, self.y, self.z)
      def touch(self,x,y,z):
        self.tiles.append((x,y,z))
        
    s =spiraller(x,y,z)
    for d in range(1,distance+1):
      s.moveX(1, 1) # 1 right
      s.moveY(d*2-1, -1) # d*2-1 up
      s.moveX(d*2, -1)   # d*2 left
      s.moveY(d*2, 1)    # d*2 down
      s.moveX(d*2, 1)    # d*2 right
    return(s.tiles)

  def update(self):
#    """because it seems, that unless we force redraw the window
#    the threads will be stuck, we poke them while they are running
#    TODO: maybe the this could be done more elegantly ?"""
#    if self.sizeThread != None and self.sizeThread.finished == False:
#      self.set('needRedraw', True)
#      print "refreshing the GetSize thread"
#    if self.getFilesThread != None and self.getFilesThread.finished == False:
#      self.set('needRedraw', True)
##      print "refreshing the GetFiles thread"
    pass

  def getTilesForRoute(self, route, radius, z):
    """get tilenamames for tiles around the route for given radius and zoom"""
    """ now we look whats the distance between each two trackpoints,
    if it is larger than the tracklog radius, we add aditioanl interpolated points,
    so we get continuous coverage for the tracklog """
    first = True
    interpolatedPoints = []
    for point in route:
      if first: # the first point has no previous point
        (lastLat, lastLon) = (point['latitude'], point['longitude'])
        first = False
        continue
      (thisLat, thisLon) = (point['latitude'], point['longitude'])
      distBtwPoints = geo.distance(lastLat, lastLon, thisLat, thisLon)
      """if the distance between points was greater than the given radius for tiles,
      there would be no continuous coverage for the route"""
      if distBtwPoints > radius:
        """so we call this recursive function to interpolate points between
        points that are too far apart"""
        interpolatedPoints.extend(self.addPointsToLine(lastLat, lastLon, thisLat, thisLon, radius))
      (lastLat, lastLon) = (thisLat, thisLon)
    """because we dont care about what order are the points in this case,
    we just add the interpolated points to the end"""
    route.extend(interpolatedPoints)
    start = clock()
    tilesToDownload = set()
    for point in route: #now we iterate over all points of the route
      (lat,lon) = (point['latitude'], point['longitude'])
      # be advised: the xy in this case are not screen coordinates but tile coordinates
      (x,y) = latlon2xy(lat,lon,z)
      # the spiral gives us tiles around coordinates for a given radius
      currentPointTiles = self.spiral(x,y,z,radius)
      """now we take the resulting list  and process it in suach a way,
      that the tiles coordinates can be stored in a set,
      so we will save only unique tiles"""
      outputSet = set(map(lambda x: tuple(x), currentPointTiles))
      tilesToDownload.update(outputSet)
    print "Listing tiles took %1.2f ms" % (1000 * (clock() - start))
    print "unique tiles %d" % len(tilesToDownload)
    return tilesToDownload

  def addPointsToLine(self, lat1, lon1, lat2, lon2, maxDistance):
    """experimental (recursive) function for adding aditional points between two coordinates,
    until their distance is less or or equal to maxDistance
    (this is actually a wrapper for a local recursive function)"""
    pointsBetween = []
    def localAddPointsToLine(lat1, lon1, lat2, lon2, maxDistance):
      distance = geo.distance(lat1, lon1, lat2, lon2)
      if distance <= maxDistance: # the termination criterium
        return
      else:
        middleLat = (lat1 + lat2)/2.0 # fin the midpoint between the two points
        middleLon = (lon1 + lon2)/2.0
        pointsBetween.extend([{'latitude': middleLat,'longitude': middleLon}])
        # process the 2 new line segments
        localAddPointsToLine(lat1, lon1, middleLat, middleLon, maxDistance)
        localAddPointsToLine(middleLat, middleLon, lat2, lon2, maxDistance)

    localAddPointsToLine(lat1, lon1, lat2, lon2, maxDistance) # call the local function
    return pointsBetween

  def drawMenu(self, cr, menuName):
    # is this menu the correct menu ?
    if menuName != ('batchTileDl'):
      return # we arent the active menu so we dont do anything

#    if self.getFilesThread != None and self.getFilesThread.finished == False:
#      self.set('needRedraw', True)

    """in order for the threeds to work normally, it is needed to pause the main loop for a while
    * this works only for this menu, in other menus (even the edit  menu) the threads will be slow to start
    * when looking at map, the threads behave as expected :)
    * so, when downloading:
    -> look at the map OR the batch progress :)**"""
    time.sleep(0.5)
    self.set('needRedraw', True)
    (x1,y1,w,h) = self.get('viewport', None)
    self.set('dataMenu', 'edit')
    menus = self.m.get("menu",None)
    sizeThread = self.sizeThread
    getFilesThread = self.getFilesThread
    self.set("batchMenuEntered", True)

    if w > h:
      cols = 4
      rows = 3
    elif w < h:
      cols = 3
      rows = 4
    elif w == h:
      cols = 4
      rows = 4

    dx = w / cols
    dy = h / rows
    # * draw "escape" button
    menus.drawButton(cr, x1, y1, dx, dy, "", "up", "menu:rebootDataMenu|set:menu:main")
    # * draw "edit" button
    menus.drawButton(cr, (x1+w)-2*dx, y1, dx, dy, "edit", "edit", "menu:setupEditBatchMenu|set:menu:editBatch")
    # * draw "start" button
    menus.drawButton(cr, (x1+w)-1*dx, y1, dx, dy, "start", "start", "mapData:download")
    # * draw the combined info area and size button (aka "box")
    boxX = x1
    boxY = y1+dy
    boxW = w
    boxH = h-dy
    menus.drawButton(cr, boxX, boxY, boxW, boxH, "", "3h", "mapData:getSize")

    # * display information about download status
    getFilesText = self.getFilesText(getFilesThread)
    getFilesTextX = boxX + dx/8
    getFilesTextY = boxY + boxH*1/4
    self.showText(cr, getFilesText, getFilesTextX, getFilesTextY, w-dx/4, 40)

    # * display information about size of the tiles
    sizeText = self.getSizeText(sizeThread)
    sizeTextX = boxX + dx/8
    sizeTextY = boxY + boxH*2/4
    self.showText(cr, sizeText, sizeTextX, sizeTextY, w-dx/4, 40)

    # * display information about free space available (for the filesystem with the tilefolder)
    freeSpaceText = self.getFreeSpaceText()
    freeSpaceTextX = boxX + dx/8
    freeSpaceTextY = boxY + boxH * 3/4
    self.showText(cr, freeSpaceText, freeSpaceTextX, freeSpaceTextY, w-dx/4, 40)

#    elif menuName == 'editBatch':
#      return
  def getFilesText(self, getFilesThread):
    """return a string describing status of the download threads"""
    tileCount = len(self.currentDownloadList)
    if tileCount == 0:
      return "All tiles for this area are available."
    elif getFilesThread == None:
      return ( "Press Start to download %d tiles." % tileCount)
    elif getFilesThread.isAlive() == True:
      totalTileCount = getFilesThread.urlCount
      currentTileCount = getFilesThread.processed
      text = "Downloading: %d of %d tiles complete" % (currentTileCount, totalTileCount)
      self.notificateOnce = True
      return text
    elif getFilesThread.isAlive() == False: #TODO: send an alert that download is complete
      text = "Download complete."
      if self.notificateOnce == True:
        self.sendMessage('notification:Download complete.#10')
      self.notificateOnce = False
      return text

  def getSizeText(self, sizeThread):
    """return a string describing status of the size counting threads"""
    tileCount = len(self.currentDownloadList)
    if tileCount == 0:
      return ""
    if sizeThread == None:
      return ("Total size of tiles is unknown (click to compute).")
    elif sizeThread.isAlive() == True:
      totalTileCount = sizeThread.urlCount
      currentTileCount = sizeThread.processed
      text = "Checking: %d of %d tiles complete" % (currentTileCount, totalTileCount)
      return text
    elif sizeThread.isAlive() == False:
      sizeInMB = sizeThread.totalSize/(1024.0*1024.0)
      text = "Total size for download: %1.2f MB" % (sizeInMB)
      return text

  def getFreeSpaceText(self):
    """return a string describing the space available on the filesystem where the tilefolder is"""
    path = self.get('tileFolder', None)
    f = os.statvfs(path)
    freeSpaceInBytes = (f.f_bsize * f.f_bavail)
    freeSpaceInMB = freeSpaceInBytes/(1024.0*1024.0)
    text = "Free space available: %1.1f MB" % freeSpaceInMB
    return text




  def showText(self,cr,text,x,y,widthLimit=None,fontsize=40):
    if(text):
      cr.set_font_size(fontsize)
      stats = cr.text_extents(text)
      (textwidth, textheight) = stats[2:4]

      if(widthLimit and textwidth > widthLimit):
        cr.set_font_size(fontsize * widthLimit / textwidth)
        stats = cr.text_extents(text)
        (textwidth, textheight) = stats[2:4]

      cr.move_to(x, y+textheight)
      cr.show_text(text)

  def sendMessage(self,message):
    m = self.m.get("messages", None)
    if(m != None):
      print "mapData: Sending message: " + message
      m.routeMessage(message)
    else:
      print "mapData: No message handler, cant send message."

  def tilesetSvgSnippet(self, f, tileset, colour):
    for tile in tileset:
      (x,y) = [int(a) for a in tile.split(",")]
      f.write("<rect width=\"1\" height=\"1\" x=\"%d\" y=\"%d\" style=\"fill:%s;stroke:#000000;stroke-width:0.05;\" id=\"rect2160\" />\n" % (x,y, colour))
  
  def routeSvgSnippet(self, f, route):
    path = None
    for pos in route:
      (lat,lon) = pos
      (x,y) = latlon2xy(lat, lon, 15)
      if(path == None):
        path = "M %f,%f" % (x,y)
      else:
        path += " L %f,%f" % (x,y)

    f.write("<path       style=\"fill:none; stroke:white; stroke-width:0.12px;\" d=\"%s\"        id=\"inner\" />\n" % path)

    f.write("<path       style=\"fill:none; stroke:yellow; stroke-width:0.06px;\" d=\"%s\"        id=\"outer\" />\n" % path)
      

  def tilesetToSvg(self, tilesets, route, filename):
    f = open(filename, "w")
    f.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n")
    f.write("<svg\n   xmlns:svg=\"http://www.w3.org/2000/svg\"\n   xmlns=\"http://www.w3.org/2000/svg\"\n   version=\"1.0\"\n   width=\"1000\"\n   height=\"1000\"   id=\"svg2\">\n")

    print "Creating SVG"
    f.write("  <g id=\"layer1\">\n")
    colours = ['red','#FF8000','yellow','green','blue','#808080','black']
    for tileset in tilesets:
      colour = colours.pop(0)
      print " - tileset %s"% colour
      self.tilesetSvgSnippet(f,tileset, colour)
    f.write("</g>\n")
    
    if(route):
      f.write("  <g id=\"route\">\n")
      print " - route"
      self.routeSvgSnippet(f, route)
      f.write("</g>\n")
     
    f.write("</svg>\n")



if(__name__ == "__main__"):
  from sample_route import *
  route = getSampleRoute()
  a = mapData({}, {})

  if(0): # spirals
    for d in range(1,10):
      # Create a spiral of tiles, radius d
      tileset = a.spiral(100,100,0, d)
      print "Spiral of width %d = %d locations" %(d,len(tileset))

      # Convert array to dictionary
      keys = {}
      count = 0
      for tile in tileset:
        (x,y,z) = tile
        key = "%d,%d" % (x,y)
        keys[key] = " " * (5-len(str(count))) + str(count)
        count += 1

      # Print grid of values to a textfile
      f = open("tiles_%d.txt" % d, "w")
      for y in range(100 - d - 2, 100 + d + 2):
        for x in range(100 - d - 2, 100 + d + 2):
          key = "%d,%d" % (x,y)
          val = keys.get(key, " ")
          f.write("%s\t" % val)
        f.write("\n")
      f.close()
          
  # Load a sample route, and try expanding it
  if(1):
    tileset = a.listTiles(route)
    from time import time
    print "Route covers %d tiles" % len(tileset)


    a.tilesetToSvg([tileset], route, "route.svg")
       
    if(1):
      tilesets = []
      for i in range(0,14,2):
        start = time()
        result = a.expand(tileset,i)
        dt = time() - start
        print " expand by %d to get %d tiles (took %1.3f sec)" % (i,len(result), dt)
        tilesets.insert(0,result)

      a.tilesetToSvg(tilesets, route, "expand.svg" )
