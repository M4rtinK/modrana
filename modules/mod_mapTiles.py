#!/usr/bin/python
#----------------------------------------------------------------------------
# Display map tile images (+ position cursor)
#----------------------------------------------------------------------------
# Copyright 2007-2008, Oliver White
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
from __future__ import with_statement # for python 2.5
from base_module import ranaModule
from threading import Thread
import threading
import Queue
import traceback
import cairo
import urllib2
import gtk
import time
from configobj import ConfigObj
from tilenames import *

import socket
timeout = 30 # this sets timeout for all sockets
socket.setdefaulttimeout(timeout)


#loadImage = None
#def setLoadimage(function):
#  loadImage = function
#  print function
#  return

def getModule(m,d,i):
  return(mapTiles(m,d,i))

maplayers = {}
configVariables = {
    'label':'label',
    'url':'tiles',
    'max_zoom':'maxZoom',
    'min_zoom':'minZoom',
    'type':'type',
    'folder_prefix':'folderPrefix',
    'coordinates':'coordinates',
                  }
mapConfigPath = 'map_config.conf'


def allNeededIn(needed, dict):
  for key in needed:
    if key in dict:
      continue
    else:
      return False
  return True  

try:
  config = ConfigObj(mapConfigPath)
  for layer in config:
    if allNeededIn(configVariables.keys(), config[layer].keys()): # check if all neded keys are available
      tempDict = {}
      for var in configVariables:
        tempDict[configVariables[var]] = config[layer][var]
      tempDict['minZoom'] = int(tempDict['minZoom']) # convert strings to integers
      tempDict['maxZoom'] = int(tempDict['maxZoom'])
    else:
      print "mapTiles: layer is badly defined/formated: %s" % layer


    maplayers[layer] = tempDict

except Exception, e:
  print "mapTiles: loading map_config.conf failed: %s" % e



  
class mapTiles(ranaModule):
  """Display map images"""
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.images = [{},{}] # the first dict contains normal image data, the seccond contains special tiles
    self.imagesLock = threading.Lock()
    self.threads = {}
    self.threadlListCondition = threading.Condition(threading.Lock())
    self.maxImagesInMemmory = 150 # to avoid a memmory leak
    self.imagesTrimmingAmmount = 30 # how many tiles to remove once the maximum is reached
    """so that trim does not run always run arter adding a tile"""
    self.tileSide = 256 # by default, the tiles are squares, side=256
    """ TODO: analyse memmory usage,
              set approrpiate value,
              platform dependendt value,
              user configurable
    """
    self.tileLoadRequestQueue = Queue.Queue()
    self.downloadRequestPool = []
    self.downloadRequestPoolLock = threading.Lock()
    self.downloadRequestTimeout = 30 # in seconds
    self.startTileDownloadManagementThread()
    self.startTileLoadingThread()

    self.shutdownAllThreads = False # notify the threads that shutdown is in progress
    
    specialTiles = [
                    ('tileDownloading' , 'themes/default/tile_downloading.png'),
                    ('tileDownloadFailed' , 'themes/default/tile_download_failed.png'),
                    ('tileLoading' , 'themes/default/tile_loading.png'),
                    ('tileWaitingForDownloadSlot' , 'themes/default/tile_waiting_for_download_slot.png'),
                    ('tileNetworkError' , 'themes/default/tile_network_error.png')
                   ]
    self.loadSpecialTiles(specialTiles) # load the special tiles to the special image cache
    self.loadingTile = self.images[1]['tileLoading']
    self.downloadingTile = self.images[1]['tileDownloading']
    self.waitingTile = self.images[1]['tileWaitingForDownloadSlot']
    self.lastThreadCleanupTimestamp=time.time()
    self.lastThreadCleanupInterval=2 # clean finished threads every 2 seconds
    self.set('maplayers', maplayers) # export the maplyers definition for use by other modules

    self.mapViewModule = None

  def firstTime(self):
    self.mapViewModule = self.m.get('mapView', None)
    
  def startTileDownloadManagementThread(self):
    """start the consumer thread for download requests"""
    t = Thread(target=self.tileDownloadManager, name='automatic tile download management thread')
    t.setDaemon(True) # we need that the worker dies with the program
    t.start()

  def tileDownloadManager(self):
    """this is a tile loading request consumer thread"""
    while True:
      with self.threadlListCondition:
        try:
          """
          wait for notification that there might be download requests or free download slots
          """
          self.threadlListCondition.wait()
          if self.shutdownAllThreads:
            print "\nmapTiles: automatic tile download management thread shutting down"
            break
          with self.downloadRequestPoolLock:
            activeThreads = len(self.threads)
            maxThreads = int(self.get("maxAutoDownloadThreads", 20))
            if activeThreads < maxThreads: # can we start new threads ?
              # ** there are free download slots **
              availableSlots = maxThreads-activeThreads
              #fill all available slots
              for i in range(0, availableSlots):
                if self.downloadRequestPool:
                  request = self.downloadRequestPool.pop()
                  (name,x,y,z,layer,layerPrefix,layerType, filename, folder, timestamp) = request
                  # start a new thread
                  self.threads[name] = self.tileDownloader(name,x,y,z,layer,layerPrefix,layerType, filename, folder, self)
                  self.threads[name].daemon = True
                  self.threads[name].start()
                  # chenge the status tile to "Downloading..."
                  with self.imagesLock:
                    self.images[0][name] = self.downloadingTile
            else:
              # ** all download slots are full **

              # remove old requests
              currentTime = time.time()
              cleanPool = []
              def notOld(currentTime,request):
                timestamp = request[9]
                dt = (currentTime - timestamp)
                return dt < self.downloadRequestTimeout

              for request in self.downloadRequestPool:
                if notOld(currentTime, request):
                  cleanPool.append(request)
                else:
                  """this request timed out,
                     remove its "Waiting..." tile from image cache,
                     so that is can be retried"""
                  name = request[0]
                  self.removeImageFromMemmory(name)
              self.downloadRequestPool = cleanPool
        except Exception, e:
          print "exception in tile download manager thread:\n%s" % e

  def startTileLoadingThread(self):
    """start the loading-request consumer thread"""
    t = Thread(target=self.tileLoader, name='tile loading thread')
    t.setDaemon(True) # we need that the worker dies with the program
    t.start()

  def tileLoader(self):
    """this is a tile loading request consumer thread"""
    while True:
      request = self.tileLoadRequestQueue.get(block=True) # consume from this queue
      (key,args) = request
      if key == 'loadRequest':
        (name, x, y, z, layer) = args
        self.loadImage(name, x, y, z, layer)
      elif key == 'shutdown':
        print "\nmapTiles: tile loading thread shutting down"
        break

  def loadSpecialTiles(self, specialTiles):
    """load special tiles from files to the special tiles cache"""
    for tile in specialTiles:
      (name,path) = tile
      self.loadImageFromFile(path, name, type="special", dictIndex=1)
      
  def update(self):
    """monitor if the automatic tile downalods finished and then remove them from the dictionary
    (also automagicaly refreshes the screen once new tiles are avalabale, even when not centered)"""

    currentTime = time.time()
    dt = currentTime - self.lastThreadCleanupTimestamp
    if dt > self.lastThreadCleanupInterval:
      self.lastThreadCleanupTimestamp = currentTime
#      with self.threadlListCondition:
#        if len(self.threads) > 0:
#  #        time.sleep(0.001) # without this  short (1ms ?) sleep, the threads wont get processing time to report results
#          for index in filter(lambda x: self.threads[x].finished == 1, self.threads):
#            self.set('needRedraw', True)
#            if index in self.threads.keys():
#              del self.threads[index]

      if self.get('reportTileCachStatus', False): # TODO: set to False by default
        print "** tile cache status report **"
        print "threads: %d, images: %d, special tiles: %d, downloadRequestPool:%d" % (len(self.threads), len(self.images[0]),len(self.images[1]),len(self.downloadRequestPool))


    """seems that some added error handling in the download thread class can replace this,
       but it left here for testing purposses"""
#    z = self.get('z', 15)
#    """when we change zoomlevel and the number of threads does not change,
#       we clear the threads set, this is usefull, because:
#       * failed downloads dont acumulate and will be tried again when we visit this zoomlevel again
#       * tile downloads that dont actualy exist (eq tiles from max+1 zoomlevel) dont acumulate
#       it is important to have the "self.threads" set empty when we are not downloading anything,
#       because othervise we are wasting time on the "refresh on finished tile download" logic and also
#       the set could theoreticaly cause a memmory leak if not periodicaly cleared from wrong items
#
#       this method was chosen instead of a timeout, because it would be hard to set a timeout,
#       that would work on gprs and a fast connection
#    """
#    if self.oldZ != z:
##      print "resetting z"
#      self.oldZ = z
#      if len(self.threads) == self.oldThreadCount:
#        print "clearing thread set"
#        self.threads = {}
#        self.oldThreadCount = len(self.threads)
#    self.oldThreadCount = len(self.threads)

  def beforeDraw(self):
    """we need to synchronize centering with map redraw,
    so we first check if we need to centre the map and then redraw"""
    mapViewModule = self.mapViewModule
    if mapViewModule:
      mapViewModule.handleCentring()


  def drawMap(self, cr):
    """Draw map tile images"""
    try: # this should get rid of a fair share of the infamous "black screens"
      proj = self.m.get('projection', None)
      if proj and proj.isValid():
        loadingTile = self.loadingTile
        (sx,sy,sw,sh) = self.get('viewport') # get screen parameters
        scale = int(self.get('mapScale', 1)) # get the current scale

        if scale == 1: # this will be most of the time, so it is first
          z = int(self.get('z', 15))
          (px1,px2,py1,py2) = (proj.px1,proj.px2,proj.py1,proj.py2) #use normal projection bbox
          cleanProjectionCoords = (px1,px2,py1,py2) # wee need the unmodified coords for later use
        else:
          if scale == 2: # tiles are scaled to 512*512 and represent tiles from zl-1
            z = int(self.get('z', 15)) - 1
          elif scale == 4: # tiles are scaled to 1024*1024 and represent tiles from zl-2
            z = int(self.get('z', 15)) - 2
          else:
            z = int(self.get('z', 15))

          # we use tiles from an upper zl and strech them over lower zl
          (px1,px2,py1,py2) = proj.findEdgesForZl(z, scale)
          cleanProjectionCoords = (px1,px2,py1,py2) # wee need the unmodified coords for later use

        if self.get("rotateMap", False) and (self.get("centred", False)):
          # due to the rotation, the map must be larger
          # we take the longest side and render tiles in a square
          longestSide = max(sw,sh)
          add = (longestSide/2.0)/(self.tileSide)
          # enlarge the bounding box
          (px1,px2,py1,py2) = (px1-add,px2+add,py1-add,py2+add)

        # get the range of tiles we need
        wTiles =  len(range(int(floor(px1)), int(ceil(px2)))) # how many tiles wide
        hTiles =  len(range(int(floor(py1)), int(ceil(py2)))) # how many tiles high

        # upper left tile
        cx = int(px1)
        cy = int(py1)
        # we need the "clean" cooridnates for the folowing conversion
        (px1,px2,py1,py2) = cleanProjectionCoords
        (pdx, pdy) = (px2 - px1,py2 - py1)
        # upper left tile coodinates to screen coordinates
        cx1,cy1 = (sw*(cx-px1)/pdx,sh*(cy-py1)/pdy) #this is basically the pxpy2xy function from mod_projection inlined
        cx1,cy1 = int(cx1),int(cy1)

        layer = self.get('layer','osma')
        # Cover the whole map view with tiles

        if self.get('overlay', False): # is the overlay on ?
          ratio = self.get('transpRatio', "0.5,1").split(',') # get the transparency ratio
          (alphaOver, alphaBack) = (float(ratio[0]),float(ratio[1])) # convert it to floats

          # get the background layer
          layer2 = self.get('layer2', 'mapnik')

          # draw the composited layer
          for ix in range(0, wTiles):
            for iy in range(0, hTiles):

              # get tile cooridnates by incrementing the upper left tile cooridnates
              x = cx+ix
              y = cy+iy

              # get screen coordinates by incrementing upper left tile screen coordinates
              x1 = cx1 + 256*ix*scale
              y1 = cy1 + 256*iy*scale

              # Try to load and display images
              nameBack = "%s_%d_%d_%d" % (layer2,z,x,y)
              nameOver = "%s_%d_%d_%d" % (layer,z,x,y)
              backImage = self.images[0].get(nameBack)
              overImage = self.images[0].get(nameOver)
              # check if the background tile is already cached
              if backImage == None: # background image not yet loaded
                if self.imagesLock.acquire(False):
                  self.images[0][nameBack] = loadingTile # set the loading tile as placeholder
                  self.tileLoadRequestQueue.put(('loadRequest',(nameBack, x, y, z, layer2)),block=False)
                  self.imagesLock.release()
                backImage = loadingTile # draw the loading tile this time
              # check if the overlay tile is already cached
              if overImage == None: # overlay image not yet loaded
                if self.imagesLock.acquire(False):
                  self.images[0][nameOver] = loadingTile # set the loading tile as placeholder
                  self.tileLoadRequestQueue.put(('loadRequest',(nameOver, x, y, z, layer)),block=False)
                  self.imagesLock.release()
                overImage = loadingTile # draw the loading tile this time

              """we do this inline to get rid of function calling overhead"""
              # Move the cairo projection onto the area where we want to draw the image
              cr.save()
              cr.translate(x1,y1)
              cr.scale(scale,scale) # scale te tile according to current scale settings

              # Display the image
              cr.set_source_surface(backImage[0],0,0) # draw the background
              cr.paint_with_alpha(alphaBack)
              cr.set_source_surface(overImage[0],0,0) # draw the overlay
              cr.paint_with_alpha(alphaOver)

              # Return the cairo projection to what it was
              cr.restore()

        else: # overlay is disabled
          # draw the normal layer
          for ix in range(0, wTiles):
            for iy in range(0, hTiles):

              # get tile cooridnates by incrementing the upper left tile cooridnates
              x = cx+ix
              y = cy+iy

              # get screen coordinates by incrementing upper left tile screen coordinates
              x1 = cx1 + 256*ix*scale
              y1 = cy1 + 256*iy*scale

              # Try to load and display images
              """we do this inline to get rid of function calling overhead"""
              name = "%s_%d_%d_%d" % (layer,z,x,y)
              tileImage = self.images[0].get(name)
              if tileImage:
                cr.save() # save the cairo projection context
                cr.translate(x1,y1)
                cr.scale(scale,scale)
                cr.set_source_surface(tileImage[0],0,0)
                cr.paint()
                cr.restore() # Return the cairo projection to what it was
              else:
                """we need this lock to store the "work in progresss" temporary tile,
                   which assures that there is only a single loading request queued for a tile

                   the lock is used quite often (trimming te image cache, storing new images),
                   but we can't block in this thread as it would lag the user interface

                   therefore if we need this lock, but it is unavailable,
                   we just skip loading the "in progress tile" and quing the loading request
                   and directly show a "loading..." tile instead
                   """
                if self.imagesLock.acquire(False):
                  self.images[0][name] = loadingTile
                  self.imagesLock.release()
                  self.tileLoadRequestQueue.put(('loadRequest',(name, x, y, z, layer)),block=False)
                cr.save() # save the cairo projection context
                cr.translate(x1,y1)
                cr.scale(scale,scale)
                cr.set_source_surface(loadingTile[0],0,0)
                cr.paint()
                cr.restore() # Return the cairo projection to what it was

    except Exception, e:
      print "mapTiles: expception while drawing the map layer:\n%s" % e


  def removeImageFromMemmory(self, name, dictIndex=0):
    # remove an image from memmory
    with self.imagesLock: #make sure no one fiddles with the cache while we are working with it
      if name in self.images:
        del self.images[dictIndex][name]
  
  def drawImage(self,cr, tileImage, x, y, scale):
    """Draw a tile image"""
    # move to the drawing coordinates
    cr.translate(x1,y1)
    cr.scale(scale,scale) # scale te tile accorind to current scale settings
    
    # Display the image
    cr.set_source_surface(tileImage,0,0)
    # paint the result
    cr.paint()

  def drawCompositeImage(self,cr, nameOver, nameBack, x,y, scale, alpha1=1, alpha2=1, dictIndex1=0,dictIndex2=0):
    """Draw a composited tile image"""

#    # If it's not in memory, then stop here
#    if not nameOver and nameBack in self.images.keys():
#      print "Not loaded"
#      return

    # Move the cairo projection onto the area where we want to draw the image
    cr.save()
    cr.translate(x,y)
    cr.scale(scale,scale) # scale te tile accorind to current scale settings

    # Display the image
    cr.set_source_surface(self.images[dictIndex1][nameBack][0],0,0) # draw the background
    cr.paint_with_alpha(alpha2)
    cr.set_source_surface(self.images[dictIndex2][nameOver][0],0,0) # draw the overlay
    cr.paint_with_alpha(alpha1)

    # Return the cairo projection to what it was
    cr.restore()
    
  def loadImage(self,name , x, y, z, layer):
    """Check that an image is loaded, and try to load it if not"""
    
    """at this point, there is only a placeholder image in the memmory cache"""

    # first, is it already in the process of being downloaded?
    with self.threadlListCondition:
      if name in self.threads.keys():
        if(not self.threads[name].finished):
          with self.imagesLock: # substitute the "loading" tile with a "downloading" tile
            downloadingTile = self.downloadingTile
            downloadingTile[1]['addedTimestamp'] = time.time()
            self.images[0][name] = downloadingTile
          return('OK')
    
    # seccond, is it in the disk cache?  (including ones recently-downloaded)
    layerInfo = maplayers.get(layer, None)
    if(layerInfo == None): # is the layer info valid
      return('NOK')

    layerPrefix = layerInfo.get('folderPrefix','OSM')
    layerType = layerInfo.get('type','png')

    storeTiles = self.m.get('storeTiles', None) # get the tile storage module
    if storeTiles:
      pixbuf = storeTiles.getTile(layerPrefix, z, x, y, layerType)
      """None from getTiles means the tile was not found
         False means loading the tile from file to pixbuf failed"""
      if pixbuf:
        self.storeInMemmory(self.pixbufToCairoImageSurface(pixbuf), name)
        return('OK')

    filename = self.getTileFolderPath() + (self.getImagePath(x,y,z,layerPrefix, layerType))
#
#    storageType = self.get('tileStorageType', 'files')
#    if storageType == 'sqlite': # use the sqlite based storage method
#      m = self.m.get('storeTiles', None) # get the tile storage module
#      if m:
#        try:
#          buffer = m.getTile(layerPrefix, z, x, y, layerType)
#          if buffer:
#            pl = gtk.gdk.PixbufLoader()
#            pl.write(buffer)
#            pl.close()
#            pixbuf = pl.get_pixbuf()
#            self.storeInMemmory(self.pixbufToCairoImageSurface(pixbuf), name)
#            return('OK')
#        except Exception, e:
#          print "loading tile from sqlite failed"
#          print "exception: ", e
#    else: #use the default method -> load from files
#      if (os.path.exists(filename)):
#        try:
#          pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
#          self.storeInMemmory(self.pixbufToCairoImageSurface(pixbuf), name)
#        except Exception, e:
#          print "the tile image is corrupted nad/or there are no tiles for this zoomlevel, exception:\n%s" % e
#        return('OK')

    # Image not found anywhere locally - resort to downloading it

    # Are we allowed to download it ? (network=='full')
    if(self.get('network','full')=='full'):
      # use threads
      """the thread list condition is used to signalize to the download manager,
      that here is a new download request"""
      with self.threadlListCondition:
        folder = self.getTileFolderPath() + self.getImageFolder(x, z, layerPrefix) # target folder
        timestamp = time.time()
        request = (name,x,y,z,layer,layerPrefix,layerType, filename, folder, timestamp)

        with self.imagesLock: # display the "Waiting for download slot..." status tile
          waitingTile = self.waitingTile
          waitingTile[1]['addedTimestamp'] = time.time()
          self.images[0][name] = waitingTile
          
        with self.downloadRequestPoolLock: # add a download request
          self.downloadRequestPool.append(request)

        self.threadlListCondition.notifyAll() # wake up the download manager

  def loadImageFromFile(self,path,name, type="normal", expireTimestamp=None, dictIndex=0):
    pixbuf = gtk.gdk.pixbuf_new_from_file(path)
    #x = pixbuf.get_width()
    #y = pixbuf.get_height()
    # Google sat images are 256 by 256 px, we dont need to check the size
    x = 256
    y = 256
    ''' create a new cairo surface to place the image on '''
    surface = cairo.ImageSurface(0,x,y)
    ''' create a context to the new surface '''
    ct = cairo.Context(surface)
    ''' create a GDK formatted Cairo context to the new Cairo native context '''
    ct2 = gtk.gdk.CairoContext(ct)
    ''' draw from the pixbuf to the new surface '''
    ct2.set_source_pixbuf(pixbuf,0,0)
    ct2.paint()
    ''' surface now contains the image in a Cairo surface '''
    self.storeInMemmory(surface, name, type, expireTimestamp, dictIndex)

  def filePath2Pixbuf(self, filePath):
    """return a pixbuf for a given filePath"""
    try:
      pixbuf = gtk.gdk.pixbuf_new_from_file(filePath)
      return(pixbuf)
    except Exception, e:
      print "the tile image is corrupted nad/or there are no tiles for this zoomlevel, exception:\n%s" % e
      return False


  def storeInMemmory(self, surface, name, type="normal", expireTimestamp=None, dictIndex=0):
    """store a given image surface in the memmory image cache
       dictIndex = 0 -> nromal map tiles + tile specific error tiles
       dictIndex = 1 -> speacial tiles that exist in only once in memmory and are drawn directly
       (like "Downloading...",Waiting for download slot..:", etc.) """
    metadata = {}
    metadata['addedTimestamp'] = time.time()
    metadata['type'] = type
    if expireTimestamp:
      metadata['expireTimestamp'] = expireTimestamp
    with self.imagesLock: #make sure no one fiddles with the cache while we are working with it
      self.images[dictIndex][name] = (surface, metadata) # store the image in memmory

      """ check cache size,
      if there are too many images, delete them """
      if len(self.images[0]) > self.maxImagesInMemmory:
        self.trimCache()

  def trimCache(self):
    """to avoid a memmory leak, the maximum size of the image cache is fixed
       when we reech the maximum size, we start removing images,
       starting from the oldes ones
       we an amount of images specified in imagesTrimmingAmmount,
       so that trim does not run every time an image is added to a full cache
       -> only the normal image cache needs trimming (images[0]),
       as the special image cache (images[1]) is just created once and not updated dynamically
       NOTE: the storeInMemmory method already locked images, so we don't have to
       """
    trimmingAmmount = self.imagesTrimmingAmmount
    imagesLength = len(self.images[0])
    if trimmingAmmount >= imagesLength:
      """
      this meaens that the trimming amount was set higher,
      than current length of the cahce
      the rusult is basically fluhing the cache every time it fills up
      well, I don't have an idea why would someone want to do that
      """
      self.images[0] = {}
    else:
      oldestKeys = sorted(self.images[0], key=lambda image: self.images[0][image][1]['addedTimestamp'])[0:trimmingAmmount]
      for key in oldestKeys:
        del self.images[0][key]

  def pixbufToCairoImageSurface(self, pixbuf):
      # this solution has been found on:
      # http://www.ossramblings.com/loading_jpg_into_cairo_surface_python

      """Using pixbufs in place of surface_from_png seems to be MUCH faster for jpegs and pngs alike.
         Therefore we use it as default."""

      # Tile images are mostly 256 by 256 px, we dont need to check the size
      x = 256
      y = 256
      ''' create a new cairo surface to place the image on '''
      surface = cairo.ImageSurface(0,x,y)
      ''' create a context to the new surface '''
      ct = cairo.Context(surface)
      ''' create a GDK formatted Cairo context to the new Cairo native context '''
      ct2 = gtk.gdk.CairoContext(ct)
      ''' draw from the pixbuf to the new surface '''
      ct2.set_source_pixbuf(pixbuf,0,0)
      ct2.paint()
      return surface

  def imageName(self,x,y,z,layer):
    """Get a unique name for a tile image 
    (suitable for use as part of filenames, dictionary keys, etc)"""
    return("%s_%d_%d_%d" % (layer,z,x,y))

  def getImagePath(self,x,y,z,prefix, extension):
    """Get a unique name for a tile image
    (suitable for use as part of filenames, dictionary keys, etc)"""
    return("%s/%d/%d/%d.%s" % (prefix,z,x,y,extension))
  
  def getImageFolder(self,x,z,prefix):
    """Get a unique name for a tile image
    (suitable for use as part of filenames, dictionary keys, etc)"""
    return("%s/%d/%d" % (prefix,z,x))

  def getTileFolderPath(self):
    """helper function that returns path to the tile folder"""
    return self.get('tileFolder', 'cache/images')

  def imageY(z,extension):
    return (('%d.%s') % (z, extension))

  def layers(self):
    return(maplayers)

  def getTileUrl(self, x, y, z, layer):
    """Wrapper, that makes it possible to use this function from other modules."""
    return getTileUrl(x, y, z, layer)

  def shutdown(self):
    # shutdown the worker/consumer threads
    self.shutdownAllThreads = True

    # shutdown the tile loading thread
    self.tileLoadRequestQueue.put(('shutdown', ()),block=False)
    # notify the automatic tile download manager thread about the shutdown
    with self.threadlListCondition:
      self.threadlListCondition.notifyAll()


  class tileDownloader(Thread):
    """Downloads an image (in a thread)"""
    def __init__(self,name, x,y,z,layer,layerName,layerType,filename, folder, callback):
      Thread.__init__(self)
      self.name = name
      self.x = x
      self.y = y
      self.z = z
      self.layer = layer
      self.layerName = layerName
      self.layerType = layerType
      self.folder = folder
      self.finished = 0
      self.filename = filename
      self.callback = callback

    def run(self):
      try:
        self.downloadTile( \
          self.name,
          self.x,
          self.y,
          self.z,
          self.layer,
          self.filename,
          self.folder)
        self.finished = 1

      # something is wrong with the server or url
      except urllib2.HTTPError, e:
        tileDownloadFailedSurface = self.callback.images[1]['tileDownloadFailed'][0]
        expireTimestamp = time.time() + 10
        self.callback.storeInMemmory(tileDownloadFailedSurface,self.name,'semiPermanentError',expireTimestamp)
        """
        like this, when tile download fails due to a http error,
        the error tile is loaded instead
        like this:
         - modRana does not immediately try to download a tile that errors out
         - the error tile is shown without modifieng the pipeline too much
         - modRana will eventually try to download the tile again,
           after it is flushed with old tiles from the memmory
        """
      except urllib2.URLError, e:
        tileNetworkErrorSurface = self.images[1]['tileNetworkError'][0]
        expireTimestamp = time.time() + 10
        self.callback.storeInMemmory(tileNetworkErrorSurface,self.name, 'error', expireTimestamp) # retry after 10 seconds
        """ as not to DOS the system when we temorarily loose internet connection or other such error occurs,
             we load a temporary error tile with expiration timestamp instead of the tile image
             TODO: actually remove tiles according to expiration timestamp :)
        """

      # something other is wrong (most probably a corrupted tile)
      except Exception, e:
        self.printErrorMessage(e)
        # remove the status tile
        self.callback.removeImageFromMemmory(self.name)

      finally: # make really sure we dont get any zombie threads
        self.finished = 1 # finished thread can be removed from the set and retried
        self.removeSelf()


    def removeSelf(self):
        with self.callback.threadlListCondition:
          # try to remove its own instance from the thread list, so taht the instance could be garbage collected
          if self.name in self.callback.threads.keys():
            del self.callback.threads[self.name]
            """notify the download manager that a download slot is now free"""
            self.callback.threadlListCondition.notifyAll()

    def printErrorMessage(self, e):
        url = getTileUrl(self.x,self.y,self.z,self.layer)
        print "mapTiles: download thread reports error"
        print "** we were doing this, when an exception occured:"
        print "** downloading tile: x:%d,y:%d,z:%d, layer:%s, filename:%s, url: %s" % ( \
                                                                            self.x,
                                                                            self.y,
                                                                            self.z,
                                                                            self.layer,
                                                                            self.filename,
                                                                            url)
        print "** this exception occured: %s\n" % e
        print "** traceback:\n"
        traceback.print_exc()

    def downloadTile(self,name,x,y,z,layer,filename, folder):
      """Downloads an image"""
#      layerDetails = maplayers.get(layer, None)
    #  if(layerDetails == None):
    #    return
    #  if(layerDetails.get('pyrender',False)):
    #    # Generate from local data
    #    renderer = RenderModule.RenderClass()
    #    renderer.RenderTile(z,x,y, 'default', filename) # TODO: pyrender layers
    #  else:
      url = getTileUrl(x,y,z,layer)

      request = urllib2.urlopen(url)
#      request = urllib.urlopen(url)
      content = request.read()
      request.close()
      pl = gtk.gdk.PixbufLoader()

      pl.write(content)

#      if pl.write(content) == False:
#        print "mapTiles:loading image failed"
#        return

      pl.close() # this  blocks until the image is completely loaded
      # http://www.ossramblings.com/loading_jpg_into_cairo_surface_python
      #x = pixbuf.get_width()
      #y = pixbuf.get_height()
      # Google sat images are 256 by 256 px, we dont need to check the size
      x = 256
      y = 256
      ''' create a new cairo surface to place the image on '''
      surface = cairo.ImageSurface(0,x,y)
      ''' create a context to the new surface '''
      ct = cairo.Context(surface)
      ''' create a GDK formatted Cairo context to the new Cairo native context '''
      ct2 = gtk.gdk.CairoContext(ct)
      ''' draw from the pixbuf to the new surface '''
      ct2.set_source_pixbuf(pl.get_pixbuf(),0,0)
      ct2.paint()
      ''' surface now contains the image in a Cairo surface '''
      self.callback.storeInMemmory(surface, name)

      # like this, currupted tiles should not get past the pixbuf loader and be stored
      m = self.callback.m.get('storeTiles', None)
      if m:
        m.automaticStoreTile(content, self.layerName, self.z, self.x, self.y, self.layerType, filename, folder, fromThread = True)

def getTileUrl(x,y,z,layer): #TODO: share this with mapData
    """Return url for given tile coorindates and layer"""
    layerDetails = maplayers.get(layer, None)
    coords = layerDetails['coordinates']
    if coords == 'google':
      url = '%s&x=%d&y=%d&z=%d' % (
        layerDetails['tiles'],
        x,y,z)
    elif coords == 'quadtree': # handle Virtual Earth maps and satelite
      quadKey = QuadTree(x, y, z)
      url = '%s%s?g=452' % ( #  dont know what the g argument is, maybe revision ? but its not optional
                                layerDetails['tiles'], # get the url
                                quadKey # get the tile identificator
                                #layerDetails['type'] # get the correct extension (also works with png for
                                )                    #  both maps and sat, but the original url is specific)
    elif coords == 'yahoo': # handle Yaho maps, sat, overlay
      y = ((2**(z-1) - 1) - y)
      z = z + 1
      url = '%s&x=%d&y=%d&z=%d&r=1' % ( # I have no idea what the r parameter is, r=0 or no r => grey square
                                layerDetails['tiles'],
                                x,y,z)
    else: # OSM, Open Cycle, T@H -> equivalent to coords == osm
      url = '%s%d/%d/%d.%s' % (
        layerDetails['tiles'],
        z,x,y,
        layerDetails.get('type','png'))
    return url

  
# modified from: http://www.maptiler.org/google-maps-coordinates-tile-bounds-projection/globalmaptiles.py (GPL)
def QuadTree(tx, ty, zoom ):
		"Converts OSM type tile coordinates to Microsoft QuadTree"

		quadKey = ""
#		ty = (2**zoom - 1) - ty
		for i in range(zoom, 0, -1):
			digit = 0
			mask = 1 << (i-1)
			if (tx & mask) != 0:
				digit += 1
			if (ty & mask) != 0:
				digit += 2
			quadKey += str(digit)

		return quadKey
