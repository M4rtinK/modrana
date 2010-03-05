#!/usr/bin/python
#----------------------------------------------------------------------------
# Python rendering engine for OpenStreetMap data
#
# Input:  OSM XML files
# Output: 256x256px PNG images in slippy-map format
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
import Image
import StringIO
import ImageDraw
import xml.sax
from OsmTileData import *
from loadOsm import *
from tilenames import *

class proj:
  """Simple projection class for geographic data.  Converts lat/long to pixel position"""
  def __init__(self, tx,ty,tz, to):
    """Setup a projection.  
    tx,ty,tz is the slippy map tile number.  
    to is the (width,height) of an image to render onto
    """ 
    (S,W,N,E) = tileEdges(tx,ty,tz)
    self.to = to
    self.S = S
    self.N = N
    self.E = E
    self.W = W
    self.dLat = N - S
    self.dLon = E - W
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
  
  def imageBackgroundColour(self):
    return("blue") # Override this function
  
  def draw(self):
    pass # Override this function
    
  def Render(self, im,filename,tx,ty,tz,layer):
    """Render an OSM tile
    im - an image to render onto
    filename - location of OSM data for the tile
    tx,ty,tz - the tile number
    layer - which map style to use
    """
    
    self.osm = LoadOsm(filename)  # get OSM data into memory
    self.proj = proj(tx,ty,tz,im.size)  # create a projection for this tile
    self.drawContext = ImageDraw.Draw(im)  # create a drawing context
    
    # Call the draw function
    self.draw()
    
    del self.drawContext # cleanup  
  
  def RenderTile(self, z,x,y, outputFile):
    """Render an OSM tile
    z,x,y - slippy map tilename
    outputFile - optional file to save to
    otherwise returns PNG image data"""
    
    # Create the image
    im = Image.new('RGBA',(256,256), self.imageBackgroundColour())
  
    # Get some OSM data for the area, and return which file it's stored in
    filename = GetOsmTileData(z,x,y)
    if(filename == None):
      return(None)
  
    # Render the map
    self.Render(im,filename,x,y,z,'default')
  
    # Either save the result to a file
    if(outputFile):
      im.save(outputFile)
      return
    else:
      # Or return it in a string
      f = StringIO.StringIO()
      im.save(f, "PNG")
      data = f.getvalue()
      return(data)

if(__name__ == '__main__'):
  # Test suite: render a tile in hersham, and save it to a file
  a = OsmRenderBase()
  a.RenderTile(17,65385,43658, "sample2.png")
