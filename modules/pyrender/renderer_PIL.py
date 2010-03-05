#!/usr/bin/python
#----------------------------------------------------------------------------
# Basic test of the PIL rendering engine, using OSM tags to control
# width and colour of the lines
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

roadColours = {
  'highway=motorway':'blue:9',
  'highway=primary':'red:4',
  'highway=secondary':'orange:4',
  'highway=residential':'black:2',
  'highway=unclassified':'black:2',
  'railway=rail':'black:1',
  'waterway=river':'blue:3'
  }

def wayStyle(tags):
  for (ident, style) in roadColours.items():
    (tag,value) = ident.split('=')
    if(tags.get(tag,'default') == value):
      return(style)
  return(None)  


class RenderClass(OsmRenderBase):
  
  # Specify the background for new tiles
  def imageBackgroundColour(self):
    return("white")
  
  # Draw a tile
  def draw(self):
    # Ways
    for w in self.osm.ways.values():
      style = wayStyle(w['t'])
      
      if(style != None):
        
        (colour, width) = style.split(":")
        width = int(width)
        
        last = (0,0,False)
        for n in w['n']: 
          # need to lookup that node's lat/long from the osm.nodes dictionary
          (lat,lon) = self.osm.nodes[n]
          
          # project that into image coordinates
          (x,y) = self.proj.project(lat,lon)
          
          # draw lines on the image
          if(last[2]):
            self.drawContext.line((last[0], last[1], x, y), fill=colour, width=width)
          last = (x,y,True)
    
    # POIs
    if(0):
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
