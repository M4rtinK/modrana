#!/usr/bin/python
#----------------------------------------------------------------------------
# Python rendering engine for OpenStreetMap data
#
# Input:  OSM XML files
# Output: 256x256px PNG images in slippy-map format
#----------------------------------------------------------------------------
# Copyright 2008, authors:
# * Sebastian Spaeth
# * Oliver White
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
import StringIO
import cairo
import math
import xml.sax
from tiledata import *
from parseOsm import *
from tilenames import *

class proj:
  """Simple projection class for geographic data.  Converts lat/long to pixel position"""
  def __init__(self, tx,ty,tz, to):
    """Setup a projection.  
    tx,ty,tz is the slippy map tile number.  
    to is the (width,height) of an image to render onto
    """ 
    dd = 1.0 / float(numTiles(tz))
    self.to = to
    self.N = ty * dd
    self.S = self.N + dd
    self.W = tx * dd
    self.E = self.W + dd
    self.dLat = -dd
    self.dLon = dd
    
    self.x1 = 0
    self.y1 = 0
    self.x2 = to[0]
    self.y2 = to[1]
    self.dx = self.x2 - self.x1
    self.dy = self.y2 - self.y1
  def project(self,lat,lon):
    """Project lat/long (in degrees) into pixel position on the tile"""
    pLat = (lat - self.S) / self.dLat
    pLon = (lon - self.W) / self.dLon
    x = self.x1 + pLon * self.dx
    y = self.y2 - pLat * self.dy
    return(x,y)

class OsmRenderBase:
  
  def imageBackgroundColour(self, mapLayer=None):
    return (0,0,0.5,0.5) # Override this function (r,g,b,a)

  def requireDataTile(self):
    return(True)  # override this if you don't want OSM data
  
  def draw(self, layer):
    pass # Override this function
  
  def getLayer(self, layernum):
    layerid = str(layernum)
    layer = self.layers.get(layerid, None)
    if(not layer):
      # Create the image
      im = cairo.ImageSurface (cairo.FORMAT_ARGB32, 256, 256)
      ctx = cairo.Context(im)  # create a drawing context
      layer = [im, ctx, layerid]
      self.layers[layerid] = layer
    return(layer)

  def getCtx(self, layernum):
    layer = self.getLayer(layernum)
    return(layer[1])
    
  def Render(self, filename,tx,ty,tz,layer):
    """Render an OSM tile
    im - an image to render onto
    filename - location of OSM data for the tile
    tx,ty,tz - the tile number
    layer - which map style to use
    """

    #set context variables that should be available during drawing
    self.z = tz
    self.mapLayer = layer

    if(filename):
      self.osm = parseOsm(filename)  # get OSM data into memory
    self.proj = proj(tx,ty,tz,(256,256))  # create a projection for this tile

    # Call the draw function
    self.draw()

  def addBackground(self,ctx, mapLayer):
    # Fill with background color
    (r,g,b,a) = self.imageBackgroundColour(mapLayer)
    ctx.set_source_rgba(r,g,b,a)
    ctx.rectangle(0, 0, 256, 256)
    ctx.fill()

  def RenderTile(self, z,x,y, mapLayer, outputFile=None):
    """Render an OSM tile
    z,x,y - slippy map tilename
    mapLayer - what style of map to draw
    outputFile - optional file to save to
    otherwise returns PNG image data"""

    print "Rendering %d,%d@%d, %s to %s" % (x,y,z,mapLayer, outputFile)
    self.layers = {}
    
    # Get some OSM data for the area, and return which file it's stored in
    if(self.requireDataTile()):
      filename = GetOsmTileData(z,x,y)
      if(filename == None):
        return(None)
    else:
      filename = None
  
    # Render the map
    self.Render(filename,x,y,z,mapLayer)
  
    out = cairo.ImageSurface (cairo.FORMAT_ARGB32, 256, 256)
    outCtx = cairo.Context(out)
    self.addBackground(outCtx, mapLayer)
    
    layerIDs = self.layers.keys()
    layerIDs.sort()
    for num in layerIDs:
      layer = self.layers[num]
      #(im,ctx,num) = layer
      outCtx.set_source_surface(layer[0], 0, 0)
      outCtx.set_operator(cairo.OPERATOR_OVER)  # was: OPERATOR_SOURCE
      outCtx.paint();

    # Either save the result to a file
    if(outputFile):
      out.write_to_png(outputFile) # Output to PNG
      return
    else:
      # Or return it in a string
      f = StringIO.StringIO()
      out.write_to_png(f)
      data = f.getvalue()
      return(data)

  def beziercurve(self,xy):
    """is handed a list of (x,y) tuples of a path and returns a list
       of 2*xy control points that can be used to draw bezier curves.
       Algorithm based on: 
       http://www.antigrain.com/research/bezier_interpolation/index.html
    """
    
    point_distance = lambda a,b: math.sqrt(pow(a[0]-b[0],2)+pow(a[1]-b[1],2))

    # first control point is 1st point
    cp = list()
    cp.append(xy[0])

    for index in range(1,len(xy)-1):
      x1,y1 = xy[index-1]
      x2,y2 = xy[index]
      x3,y3 = xy[index+1]
      
      L1=point_distance((x2,y2),(x1,y1))
      L2=point_distance((x3,y3),(x2,y2))
      C1=0.5 * (x1+x2), 0.5 *(y1+y2)
      C2=0.5 * (x2+x3), 0.5 *(y2+y3)
      C1x,C1y = C1
      C2x,C2y = C2
      
      if (L1+L2==0) or (C2x==C1x) or (C2y==C1y):
        #if impossible, just use the point as control points
        cp.append(xy[index])
        cp.append(xy[index])
      else:
        #usually just calculate the control points properly:
        Mx = L1/(L1+L2) * (C2x - C1x) + C1x
        My = L1/(L1+L2) * (C2y - C1y) + C1y 
        cp1x,cp1y = C1x-Mx + x2, C1y-My + y2
        cp2x,cp2y = C2x-Mx + x2, C2y-My + y2      

        cp.append((cp1x,cp1y))
        cp.append((cp2x,cp2y))
    #last control point is last point
    cp.append(xy[-1])
    return cp


if(__name__ == '__main__'):
  # Test suite: render a tile in london, and save it to a file
  a = OsmRenderBase()
  a.RenderTile(15, 16372, 10895, "default", "sample2.png")
