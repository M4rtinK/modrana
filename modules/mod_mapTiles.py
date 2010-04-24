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
import gtk
import time
from configobj import ConfigObj
from tilenames import *
sys.path.append("modules/pyrender")
import renderer_default as RenderModule

import socket
timeout = 30 # this sets timeout for all sockets
socket.setdefaulttimeout(timeout)

def getModule(m,d):
  return(mapTiles(m,d))



#maplayers = {
##  'pyrender':
##    {
##    'label':'pyrender',
##    'pyrender':True,
##    'type':'png'
##    },
#  'osma':
#    {
#    'label':'OSM T@h',
#    'tiles':'http://tah.openstreetmap.org/Tiles/tile/',
#    'type':'png',
#    'maxZoom': 17
#    },
#  'mapnik':
#    {
#    'label':'Mapnik',
#    'tiles':'http://tile.openstreetmap.org/',
#    'type':'png',
#    'maxZoom': 18
#    },
#  'gmap':
#    {
#    'label':'Google maps',
#    'tiles':'http://mt1.google.com/vt/',
#    'type':'png',
#    'maxZoom': 21
#    },
#  'gsat':
#    {
#    'label':'Google satelite',
#    'tiles':'http://khm1.google.com/kh/v=54',
#    'type':'jpg',
#    'maxZoom': 20
#    },
#  'vmap':
#    {
#    'label':'Virtual Earth-map',
#    'tiles':'http://tiles.virtualearth.net/tiles/r',
#    'type':'png',
#    'maxZoom': 19 # currently, there are "no tile" images on zl 20, at least for Brno
#    },
#  'vsat':
#    {
#    'label':'Virtual Earth-sat',
#    'tiles':'http://tiles.virtualearth.net/tiles/h',
#    'type':'jpg',
#    'maxZoom': 19 # there are areas, where the resolution is unusably small
#    },
#  'ymap':
#    {
#    'label':'Yahoo map',
#    'tiles':'http://maps.yimg.com/hx/tl?&s=256',
#    # tiles up to u=12 are png, 11 and up is jpg
#    # luckily our jpg handler seems to be extension independent
#    # SIDE EFFECT: producing some pngs with .jpg extension :)
#    'type':'jpg',
#    'maxZoom': 17
#    },
#  'ysat':
#    {
#    'label':'Yahoo sat',
#    'tiles':'http://maps.yimg.com/ae/ximg?&t=a&s=256',
#    'type':'jpg',
#    'maxZoom': 15
#    },
#  'yover':
#    {
#    'label':'Yahoo overlay',
#    'tiles':'http://maps.yimg.com/ae/ximg?&t=h&s=256',
#    'type':'jpg',
#    'maxZoom': 15
#    },
#  'cycle':
#    {
#    'label':'Cycle map',
##    'tiles':'http://thunderflames.org/tiles/cycle/', # this urls is probably broken
#    'tiles':'http://andy.sandbox.cloudmade.com/tiles/cycle/',
#    'type':'png',
#    'maxZoom': 15
#    },
##  'localhost': # not much usable right now
##    {
##    'label':'Localhost',
##    'tiles':'http://localhost:1280/default/',
##    'maxZoom': 15,
##    'type':'png'
##    }
#  };


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
    self.threads = {}
#    self.oldZ = None
#    self.oldThreadCount = None
    self.set('maplayers', maplayers) # export the maplyers definition for use by other modules

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

    layer = self.get('layer','osma')
    # Cover the whole map view with tiles
    for x in range(int(floor(proj.px1)), int(ceil(proj.px2))):
      for y in range(int(floor(proj.py1)), int(ceil(proj.py2))):
        
        # Convert corner to screen coordinates
        x1,y1 = proj.pxpy2xy(x,y)

        # Try to load and display images
        name = self.loadImage(x,y,z,layer)
        if(name != None):
          self.drawImage(cr,name,x1,y1)

  def update(self):
    """monitor if the automatic tile downalods finished and then remove them from the dictionary
    (also automagicaly refreshes the screen once new tiles are avalabale, even when not centered)"""

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
    
  def loadImage(self,x,y,z, layer):
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
        return(None)
    
    # Third, is it in the disk cache?  (including ones recently-downloaded)
    layerInfo = maplayers.get(layer, None)
    if(layerInfo == None):
      return

    layerType = layerInfo.get('type','png')
    layerPrefix = layerInfo.get('folderPrefix','OSM')

#    filename = "%s/%s.%s" % (self.tileFolder, name, layerType)
    filename = self.tileFolder + (self.imagePath(x,y,z,layerPrefix, layerType))

#    tangoStylePath = '/home/melf-san/Maps/'
#    filename = tangoStylePath + (self.imagePath(x,y,z,layerPrefix, layerType))
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
        self.images[name] = surface #TODO: remove "old" images from cache (possible memmory leak ?)
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
    if(self.get('threadedDownload',True)):
      folder = self.tileFolder + self.imageFolder(x, z, layerPrefix) # target folder
      if not os.path.exists(folder): # does it exist ?
        try:
          os.makedirs(folder) # create the folder
        except:
          print "mapTiles: cant crate folder %s for %s" % (folder,filename)
      self.threads[name] = tileLoader(x,y,z,layer,filename)
      self.threads[name].start()
      return(None)
    else:
      downloadTile(x,y,z,layer,filename)
      return(name)

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

def downloadTile(x,y,z,layer,filename):
  """Downloads an image"""
  layerDetails = maplayers.get(layer, None)
  if(layerDetails == None):
    return
  if(layerDetails.get('pyrender',False)):
    # Generate from local data
    renderer = RenderModule.RenderClass()
    renderer.RenderTile(z,x,y, 'default', filename) # TODO: pyrender layers
  else:
    url = getTileUrl(x,y,z,layer)
    # Download from network
#    if layer == 'gmap' or layer == 'gsat':
#      url = '%s&x=%d&y=%d&z=%d' % (
#        layerDetails['tiles'],
#        x,y,z)
#    else:
#      url = '%s%d/%d/%d.%s' % (
#        layerDetails['tiles'],
#        z,x,y,
#        layerDetails.get('type','png'))

  urllib.urlretrieve(url, filename)

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


class tileLoader(Thread):
  """Downloads an image (in a thread)"""
  def __init__(self, x,y,z,layer,filename):
    self.x = x
    self.y = y
    self.z = z
    self.layer = layer
    self.finished = 0
    self.filename = filename
    Thread.__init__(self)
    
  def run(self):
    try:
      downloadTile( \
        self.x,
        self.y,
        self.z,
        self.layer,
        self.filename)
      self.finished = 1
    except Exception, e:
      print "mapTiles: download thread reports error"
      print "** we were doing this, when an exception occured:"
      print "** downloading tile: x:%d,y:%d,z:%d, layer:%s, filename:%s" % ( \
                                                                          self.x,
                                                                          self.y,
                                                                          self.z,
                                                                          self.layer,
                                                                          self.filename)
      print "** this exception occured: %s" % e


      time.sleep(10) # dont DOS the system, when we temorarily loose internet connection or other error occurs
      self.finished = 1 # finished thread can be removed from the set and retryed
