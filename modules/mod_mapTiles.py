import os.path
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
from base_module import ranaModule
from threading import Thread
import cairo
import os
import sys
import urllib
import urllib2
import gtk
import time
from configobj import ConfigObj
from tilenames import *
sys.path.append("modules/pyrender")
import renderer_default as RenderModule
from time import clock

import socket
timeout = 30 # this sets timeout for all sockets
socket.setdefaulttimeout(timeout)


#loadImage = None
#def setLoadimage(function):
#  loadImage = function
#  print function
#  return

def getModule(m,d):
  return(mapTiles(m,d))

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
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.images = {}
    self.imagesQueue = [] #a chronological list of loaded images
    self.threads = {}
    self.maxImagesInMemmory = 100 # to avoid a memmory leak
    """ TODO: analyse memmory usage,
              set approrpiate value,
              platform dependendt value,
              user configurable
    """
    self.specialTiles = {
                         'tileDownloading' : 'icons/bitmap/tile_downloading.png',
                         'tileDownloadFailed' : 'icons/bitmap/tile_download_failed.png',
                         'tileNetworkError' : 'icons/bitmap/tile_network_error.png'
                        }

#    self.oldZ = None
#    self.oldThreadCount = None
    self.set('maplayers', maplayers) # export the maplyers definition for use by other modules
#    setLoadimage(self.loadImage) # shortcut for the download thread


  def firstTime(self):
    # the config folder should set the tile folder path by now
    self.tileFolder = self.get('tileFolder', 'cache/images')


  def drawMap(self, cr):
    """Draw map tile images"""
    (sx,sy,sw,sh) = self.get('viewport')
    
    z = int(self.get('z', 15))

    proj = self.m.get('projection', None)
    if(proj == None):
      return
    if(not proj.isValid()):
      return

    (px1,px2,py1,py2) = (proj.px1,proj.px2,proj.py1,proj.py2)

    # upper left tile
    cx = int(px1)
    cy = int(py1)
    # upper left tile coodinates to screen coordinates
    cx1,cy1 = proj.pxpy2xy(cx,cy)
    cx1,cy1 = int(cx1),int(cy1)

    wTiles =  len(range(int(floor(px1)), int(ceil(px2)))) # how many tiles wide
    hTiles =  len(range(int(floor(py1)), int(ceil(py2)))) # how many tiles high

    layer = self.get('layer','osma')
    # Cover the whole map view with tiles

    if self.get('overlay', False): # is the overlay on ?
      ratio = self.get('transpRatio', "0.5,1").split(',') # get the transparency ratio
      (alpha1, alpha2) = (float(ratio[0]),float(ratio[1])) # convert it to floats

      layer2 = self.get('layer2', 'mapnik') # get the background layer

      # draw the composited layer
      for ix in range(0, wTiles):
        for iy in range(0, hTiles):

          # get tile cooridnates by incrementing the upper left tile cooridnates
          x = cx+ix
          y = cy+iy

          # get screen coordinates by incrementing upper left tile screen coordinates
          x1 = cx1 + 256*ix
          y1 = cy1 + 256*iy

          # Try to load and display images
          nameBack = self.loadImage(x,y,z,layer2)
          nameOver = self.loadImage(x,y,z,layer)
          if(nameBack and nameOver != None):
            self.drawCompositeImage(cr,nameOver,nameBack,x1,y1,alpha1,alpha2)
      return


    # draw the normal layer
    for ix in range(0, wTiles):
      for iy in range(0, hTiles):

        # get tile cooridnates by incrementing the upper left tile cooridnates
        x = cx+ix
        y = cy+iy

        # get screen coordinates by incrementing upper left tile screen coordinates
        x1 = cx1 + 256*ix
        y1 = cy1 + 256*iy

        # Try to load and display images
        name = self.loadImage(x,y,z,layer)
        if(name != None):
          self.drawImage(cr,name,x1,y1)






  def update(self):
    """monitor if the automatic tile downalods finished and then remove them from the dictionary
    (also automagicaly refreshes the screen once new tiles are avalabale, even when not centered)"""

#    print "nr images: %d" % len(self.images)
#    print "nr queue: %d" % len(self.imagesQueue)

    
    if len(self.threads) == 0:
      return

    time.sleep(0.001) # without this  short (1ms ?) sleep, the threads wont get processing time to report results
    for index in filter(lambda x: self.threads[x].finished == 1, self.threads):
      self.set('needRedraw', True)
      del self.threads[index]
    return


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

  def storeInMemmoryAndEnqueue(self, surface, name):
    self.images[name] = surface
    if name not in self.specialTiles:
      self.imagesQueue.append(name)
    # check cache size
    # if there are too many images, delete them
    if len(self.images) > self.maxImagesInMemmory:
      self.trimCache()



  def trimCache(self):
    """to avoid a memmory leak, the maximum size of the image cache is fixed
       when we reech the maximum size, we start removing images,
       starting from the oldes ones
       we remove one image at a time
       """
#    print "trimming"
    first = self.imagesQueue[0]
    del self.images[first]
    del self.imagesQueue[0]
    print "images queue length:%d" % len(self.imagesQueue)
    print "memmory cache length:%d" % len(self.imagesQueue)

  def removeNonexistingFromQueue(self):
    # remove nonexistant images from queue
    self.imagesQueue = filter(lambda x: x in self.images.keys(), self.imagesQueue)

  def removeImageFromMemmory(self, name):
    # remove an image from memmory
    if name in self.images:
      del self.images[name]
    # make sure its removed from the queue
    self.removeNonexistingFromQueue()
  
  def drawImage(self,cr, name, x,y):
    """Draw a tile image"""
    
    # If it's not in memory, then stop here
    if not name in self.images.keys():
      print "Not loaded"
      return
    
    # Move the cairo projection onto the area where we want to draw the image
    cr.save()
    cr.translate(x,y)
    
    # Display the image
    cr.set_source_surface(self.images[name],0,0)
    cr.paint()


    # Return the cairo projection to what it was
    cr.restore()

  def drawCompositeImage(self,cr, nameOver, nameBack, x,y, alpha1=1, alpha2=1):
    """Draw a composited tile image"""

    # If it's not in memory, then stop here
    if not nameOver and nameBack in self.images.keys():
      print "Not loaded"
      return

    # Move the cairo projection onto the area where we want to draw the image
    cr.save()
    cr.translate(x,y)

    # Display the image
    cr.set_source_surface(self.images[nameBack],0,0) # draw the background
    cr.paint_with_alpha(alpha2)
    cr.set_source_surface(self.images[nameOver],0,0) # draw the overlay
    cr.paint_with_alpha(alpha1)
#    cr.paint()

    # Return the cairo projection to what it was
    cr.restore()
    
  def loadImage(self,x,y,z, layer, ):
    """Check that an image is loaded, and try to load it if not"""
    
    # First: is the image already in memory?
    """
    TODO: test, if a smpler name is more efficinet
    at least we dont need to look to the layer properties dictionary like this
    """
#    name = self.imageName(x,y,z,layer) # make this inline
    name = "%s_%d_%d_%d" % (layer,z,x,y)
    if name in self.images.keys():
      return(name)

    # Second, is it already in the process of being downloaded?
    if name in self.threads.keys():
      if(not self.threads[name].finished):
        dlTileName = 'tileDownloading'
        dlTilePath = self.specialTiles[dlTileName]
        self.loadImageFromFile(dlTilePath, dlTileName)
        return(dlTileName)
    
    # Third, is it in the disk cache?  (including ones recently-downloaded)
    layerInfo = maplayers.get(layer, None)
    if(layerInfo == None):
      return

    layerType = layerInfo.get('type','png')
    layerPrefix = layerInfo.get('folderPrefix','OSM')

    filename = self.tileFolder + (self.imagePath(x,y,z,layerPrefix, layerType))

    if(os.path.exists(filename)):
#      if(layerType == 'jpg'):
      """The method using pixbufs seems to be MUCH faster for jpegs and pngs alike.
         Therefore we use it as default."""
      #self.images[name]  = cairo.ImageSurface.create_from_jpeg(filename)
      # looks like there is no create_from_jpeg() in cairo
      # this solution has been found on:
      # http://www.ossramblings.com/loading_jpg_into_cairo_surface_python
      try:
        pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
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
        self.storeInMemmoryAndEnqueue(surface, name)




      except:
        print "the tile image is corrupted nad/or there are no tiles for this zoomlevel"

#      else:
#        #print(filename)
#        try:
#          self.images[name]  = cairo.ImageSurface.create_from_png(filename)
#        except:
#          print "corrupted tile image detected: %s" % name
      return(name)

    # Image not found anywhere - resort to downloading it

    # Are we allowed to download it ? (network=='full')
    if(self.get('network','full')=='full'):
      # use threads
#      if(self.get('threadedDownload',True)):
      folder = self.tileFolder + self.imageFolder(x, z, layerPrefix) # target folder
      if not os.path.exists(folder): # does it exist ?
        try:
          os.makedirs(folder) # create the folder
        except:
          print "mapTiles: cant crate folder %s for %s" % (folder,filename)
      self.threads[name] = self.tileLoader(x,y,z,layer,filename, self)
      self.threads[name].start()
      return(None)
      # serial download
#      else:
#        print filenam
#        downloadTile(x,y,z,layer,filename)
#        return(name)

  def loadImageFromFile(self,path,name):
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
    self.storeInMemmoryAndEnqueue(surface, name)


  def imageName(self,x,y,z,layer):
    """Get a unique name for a tile image 
    (suitable for use as part of filenames, dictionary keys, etc)"""
    return("%s_%d_%d_%d" % (layer,z,x,y))

  def imagePath(self,x,y,z,prefix, extension):
    """Get a unique name for a tile image
    (suitable for use as part of filenames, dictionary keys, etc)"""
    return("%s/%d/%d/%d.%s" % (prefix,z,x,y,extension))

  def imageFolder(self,x,z,prefix):
    """Get a unique name for a tile image
    (suitable for use as part of filenames, dictionary keys, etc)"""
    return("%s/%d/%d" % (prefix,z,x))

  def imageY(z,extension):
    return (('%d.%s') % (z, extension))

  def layers(self):
    return(maplayers)

  def getTileUrl(self, x, y, z, layer):
    """Wrapper, that makes it possible to use this function from other modules."""
    return getTileUrl(x, y, z, layer)

  class tileLoader(Thread):
    """Downloads an image (in a thread)"""
    def __init__(self, x,y,z,layer,filename, callback):
      self.x = x
      self.y = y
      self.z = z
      self.layer = layer
      self.finished = 0
      self.filename = filename
      self.callback = callback
      Thread.__init__(self)

    def run(self):
      try:
        self.downloadTile( \
          self.x,
          self.y,
          self.z,
          self.layer,
          self.filename)
        self.finished = 1

      # something is wrong with the server or url
      except urllib2.HTTPError, e:
        callback = self.callback
        name = "%s_%d_%d_%d" % (self.layer,self.z,self.x,self.y)
        errorTilePath = callback.specialTiles['tileDownloadFailed']
        callback.loadImageFromFile(errorTilePath,name)
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
        callback = self.callback
        name = "%s_%d_%d_%d" % (self.layer,self.z,self.x,self.y)
        errorTilePath = callback.specialTiles['tileNetworkError']
        callback.loadImageFromFile(errorTilePath,name)
        time.sleep(10) # dont DOS the system, when we temorarily loose internet connection or other error occurs
        # remove the image from memmory so it can be retried
        callback.removeImageFromMemmory(name)
        self.finished = 1 # finished thread can be removed from the set and retried


      # something other is wrong (most probably a corrupted tile)
      except Exception, e:
        self.printErrorMessage(e)



        time.sleep(10) # dont DOS the system, when we temorarily loose internet connection or other error occurs
        self.finished = 1 # finished thread can be removed from the set and retried

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
        print "** this exception occured: %s" % e

    def downloadTile(self,x,y,z,layer,filename):
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
      name = "%s_%d_%d_%d" % (layer,z,x,y)
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
      self.callback.storeInMemmoryAndEnqueue(surface, name)

      # like this, currupted tiles should not get past the pixbuf loader and be stored
      f = open(filename, 'w') # write the tile to file
      f.write(content)
      f.close()

      del content

      
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


