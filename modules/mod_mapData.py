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
from Queue import Queue
import os
import geo
import string
import urllib, threading



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
    self.sizeThreadingStatus = 0 # used for reporting status of the size computation threads
    self.currentTilesToGet = [] # used for reporting the (actual) size of the tiles for download
    self.set("sizeStatus", 'unknown') # this informs about the state of the size computation

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
#    #print tilesToDownload
#    for tile in tilesToDownload:
#      #print tile
#      (x,y,z) = tile
#      # for now, just get them without updating screen
#      tiledata.GetOsmTileData(z,x,y)
#      print xy2latlon(x, y, z)

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
    self.set("stopDl", False)
#    t = threading.Thread(target=self.getFiles, args=(urlsAndFilenames,))
#    t.start()

    self.currentDownloadList = urlsAndFilenames


#    self.stopThreading = True

  def addToQueue(self, tilesToDownload):
    return

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

  class SizeGetter(threading.Thread):
      def __init__(self, url):
          self.url = url
          self.size = 0
          threading.Thread.__init__(self)

      def getSize(self):
          return self.size

      def run(self):
          try:
              url = self.url
              urlInfo = urllib.urlopen(url).info() # open url and get mime info
              self.size = int(urlInfo['Content-Length']) # size in bytes
  #            print "file has %s bytes" % self.size
          except IOError:
              print "Could not open document: %s" % url

  def getFilesSize(self, urlsAndFilenames):
    self.totalSize = 0
    self.sizeThreadingStatus = 0
    urls = map(lambda x: x[0], urlsAndFilenames)
    self.set("sizeStatus", 'inProgress')

    def producer(q, urls):
      for url in urls:
          thread = self.SizeGetter(url)
          thread.start()
          q.put(thread, True)
      print "producer quiting"
      return

    def consumer(q, total_files):
      """get data from threads when they finish"""
      totalSize = 0 # initialize
      count = 0
      while count < total_files:
          thread = q.get(True)
          thread.join()
          count = count + 1 # count how many threads have been processed
          totalSize = totalSize + thread.getSize()
          self.sizeThreadingStatus = count
          print "%d od %d" % (count, total_files)
#          if (count == total_files):
#            print "consumer quiting"
#            self.totalSize = totalSize
#            return
      print "consumer quiting"
      self.totalSize = totalSize
      self.set('sizeStatus', 'known')
      return
    # we respect a multiple of the limit as for batch dl
    # (because we actually dont download anything and it is faster)
    maxThreads = self.get('maxBatchThreads', 5) * 10
    q = Queue(maxThreads)
    prod_thread = threading.Thread(target=producer, args=(q, urls))
    cons_thread = threading.Thread(target=consumer, args=(q, len(urls)))
    prod_thread.start()
    cons_thread.start()
    prod_thread.join()
    cons_thread.join()
#    print ("total size is %1.2f MB") % (self.totalSize/(1024.0*1024.0))
    return (self.totalSize/(1024.0*1024.0))



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


  def getFiles(self, urlsAndFilenames):
        def producer(q, urlsAndFilenames):
            for urlFilename in urlsAndFilenames:
                url = urlFilename[0]
                filename = urlFilename[1]
                thread = self.FileGetter(url, filename)
                thread.start()
                q.put(thread, True)
                if self.get("stopDl", None) == True:
                  print "producer: stopping Threads"
                  break

        finished = []
        def consumer(q, total_files):
            results = []
            count = 0
            while len(finished) < total_files:
                thread = q.get(True)
                thread.join()
                count = count + 1
                print "%d tiles finished downloading" % count
                results.append(thread.getResult())
#                print "%d tiles remaining" % (len(finished) - total_files)
                if self.get("stopDl", None) == True:
                  print "consumer: stopping Threads"
                  print results
                  break
        maxThreads = self.get('maxBatchThreads', 5)
        q = Queue(maxThreads)
        prod_thread = threading.Thread(target=producer, args=(q, urlsAndFilenames))
        cons_thread = threading.Thread(target=consumer, args=(q, len(urlsAndFilenames)))
        prod_thread.start()
        cons_thread.start()
        prod_thread.join()
        cons_thread.join()

  def handleMessage(self, message):
    if(message == "refreshTilecount"):
      size = int(self.get("downloadSize", 4))
      type = self.get("downloadType")
      if(type != "data"):
        print "Error: mod_mapData can't download %s" % type
        return
      
      location = self.get("downloadArea", "here") # here or route

      # Which zoom level are map tiles stored at
      z = tiledata.DownloadLevel()

      if(location == "here"):  
        # Find which tile we're on
        pos = self.get("pos",None)
        if(pos != None):
          (lat,lon) = pos
          # be advised: the xy in this case are not screen coordinates but tile coordinates
          (x,y) = latlon2xy(lat,lon,z)
          tilesAroundHere = (self.spiral(x,y,z,size)) # get tiles around our position
          self.addToQueue(tilesAroundHere) # get them downloaded

      if(location == "route"):
        loadTl = self.m.get('loadTracklog', None) # get the tracklog module
        loadedTracklogs = loadTl.tracklogs # get list of all tracklogs
        activeTracklogIndex = int(self.get('activeTracklog', 0))
        GPXTracklog = loadedTracklogs[activeTracklogIndex]
        """because we dont need all the information in the original list and
        also might need to add interpolated points, we make a local copy of
        the original list"""
        #latLonOnly = filter(lambda x: [x.latitude,x.longitude])
        trackpointsListCopy = map(lambda x: {'latitude': x.latitude,'longitude': x.longitude}, GPXTracklog.trackpointsList[0])[:]
        tilesToDownload = self.getTilesForRoute(trackpointsListCopy, size, z)
        self.checkTiles(tilesToDownload) # the tiles to be checked

    if(message == "getSize"):
      """will now ask the server and find the combined size if tiles in the batch"""
      self.set("sizeStatus", 'unknown') # first we set the size as unknown
      urlsAndFilenames = self.currentDownloadList
      print "getting size"
      if len(urlsAndFilenames) == 0:
        print "cant get combined size, the list is empty"
        return
      t = threading.Thread(target=self.getFilesSize, args=(urlsAndFilenames,))
      t.start()


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
    elif menuName == 'batchTileDl':
      (x1,y1,w,h) = self.get('viewport', None)
      self.set('dataMenu', 'edit')
      menus = self.m.get("menu",None)
#      if self.get('setUpEditMenu', True) == True:
#        menus.setupEditBatchMenu()
#        self.set('setUpEditMenu', False)

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
      boxY = y1+dx
      menus.drawButton(cr, boxX, boxY, w, h-dy, "", "3h", "mapData:getSize")

      sizeText = self.getSizeText()
      print self.get('sizeStatus', None)
      sizeTextX = boxX + dx/6
      sizeTextY = boxY + dx/4
      self.showText(cr, sizeText, sizeTextX, sizeTextY, w-40, fontsize=40)

#    elif menuName == 'editBatch':
#      return
  def getSizeText(self):
    status = self.get("sizeStatus", 'unknown')
    if status == 'unknown':
      return ("total size is unknown (click to compute)")
    elif status == 'inProgress':
      totalTileCount = len(self.currentDownloadList)
      currentTileCount = self.sizeThreadingStatus
      text = "Checking: %d of %d tiles complete" % (currentTileCount, totalTileCount)
      return text
    elif status == 'known':
      sizeInMB = self.totalSize/(1024*1024)
      text = "Total size for download: %1.2f MB" % (sizeInMB)
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
