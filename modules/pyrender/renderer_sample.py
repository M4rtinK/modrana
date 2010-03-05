#!/usr/bin/python
#----------------------------------------------------------------------------
# Sample rendering engine
#
# Copy and modify this file to create your own rendering engine
# - please keep this file clean so it's easy to understand how to
#   derive copies of it
#
# To serve tiles using your new rendering engine, change the line at
# the top of server.py, from:
#   import renderer_simple as RenderModule
# to:
#   import renderer_yourNewModule as RenderModule
#
# ..then run server.py and view it on http://localhost:1280/ as usual
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
from render_base import OsmRenderBase

class RenderClass(OsmRenderBase):
  
  # Specify the background for new tiles
  def imageBackgroundColour(self):
    return("white")
    
  # Draw a tile
  def draw(self):
    # Certain things have already been created for you at this point:
    #
    #  * self.osm contains the OpenStreetMap data for your tile
    #     - w is a list of ways
    #     - poi is a list of points-of-interest
    #     - nodes is a hash of lat/long values for nodes
    #
    #  * self.drawContext is a PIL object (Python Imageing library)
    #     - Documentation is available at:
    #       http://www.pythonware.com/library/pil/handbook/imagedraw.htm
    #
    #  * self.proj is a projection module, which you can pass lat/long
    #    values and get image coordinates back, like:
    #    (x,y) = self.proj.project(lat,lon)
    
    # Example of parsing through all the ways
    for w in self.osm.ways.values():
      last = (0,0,False)
     
      # way['n'] contains the list of its nodes
      for n in w['n']: 
        
        # need to lookup that node's lat/long from the osm.nodes dictionary
        (lat,lon) = self.osm.nodes[n]
        
        # project that into image coordinates
        (x,y) = self.proj.project(lat,lon)
        
        # draw lines on the image
        if(last[2]):
          self.drawContext.line((last[0], last[1], x, y), fill='black')
        last = (x,y,True)
    
    # Similar code for points of interest 
    # (they have just one node, as ['id'])
    for poi in self.osm.poi:
      n = poi['id']
      (lat,lon) = self.osm.nodes[n]
      (x,y) = self.proj.project(lat,lon)
      s = 1
      self.drawContext.rectangle((x-s,y-s,x+s,y+s),fill='blue')



#-----------------------------------------------------------------
# Test suite - call this file from the command-line to generate a
# sample image
if(__name__ == '__main__'):
  a = RenderClass()
  filename = "sample_"+__file__+".png"
  a.RenderTile(17,65385,43658, filename)
  print "------------------------------------"
  print "Saved image to " + filename
