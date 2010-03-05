#!/usr/bin/python
#----------------------------------------------------------------------------
# 
#----------------------------------------------------------------------------
# Copyright 2008, authors:
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
from render_cairo_base import OsmRenderBase
from tilenames import *

class RenderClass(OsmRenderBase):
  
  # Specify the background for new tiles
  def imageBackgroundColour(self, mapLayer=None):
    return(0,0,0,0)
  def requireDataTile(self):
    return(False)
  
  # Draw a tile
  def draw(self):
    file = open("places.txt","r")
    ctx = self.getCtx("mainlayer")

    print self.proj.S, self.proj.dLat
    #pLon = (lon - self.W) / self.dLon
    
    for line in file:
      line = line.strip()
      (lat,lon,id,type,name) = line.split("\t")
      if(type in ('c', 't')):
        (px,py) = latlon2relativeXY(float(lat), float(lon))
        (x,y) = self.proj.project(py,px)
        ctx.set_source_rgb(0.0, 0.0, 0.0)
        ctx.set_font_size(12)
        ctx.move_to(x,y)
        ctx.show_text(name)
        ctx.stroke()

#-----------------------------------------------------------------
# Test suite - call this file from the command-line to generate a
# sample image
if(__name__ == '__main__'):
  a = RenderClass()
  filename = "sample_"+__file__+".png"
  a.RenderTile(8, 128, 84, 'default', filename) # norwch
  
  print "------------------------------------"
  print "Saved image to " + filename
