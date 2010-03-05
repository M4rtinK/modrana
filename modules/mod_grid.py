#!/usr/bin/python
#----------------------------------------------------------------------------
# Show map grid
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
import cairo
import os
import sys
import geo

def getModule(m,d):
  return(grid(m,d))
  
class grid(ranaModule):
  """Display map images"""
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)

  def drawMapOverlay(self, cr):
    # Where is the map?
    proj = self.m.get('projection', None)
    if(proj == None):
      return
    if(not proj.isValid()):
      return
    self.drawCorners(cr, proj)
    self.drawScalebar(cr, proj)

  def drawScalebar(self, cr, proj):
    (x1,y1) = proj.screenPos(0.05, 0.85)
    (x2,y2) = proj.screenPos(0.25, 0.85)
    
    (lat1,lon1) = proj.xy2ll(x1,y1)
    (lat2,lon2) = proj.xy2ll(x2,y2)

    dist = geo.distance(lat1,lon1,lat2,lon2)
    text = "%1.1f km" % dist

    cr.set_source_rgb(0,0,0)
    cr.move_to(x1,y1)
    cr.line_to(x2,y2)
    cr.stroke()
    
    self.boxedText(cr, x1, y1-4, text, 12, 1)
    
  def drawCorners(self, cr, proj):
    (x1,y1) = proj.screenPos(0.25, 0.2)
    (x2,y2) = proj.screenPos(0.95, 0.85)

    (lat1,lon1) = proj.xy2ll(x1,y1)
    (lat2,lon2) = proj.xy2ll(x2,y2)

    fg = (1,1,1)
    bg = (0,0,0.5)
    
    self.boxedText(
      cr,
      x1, y1,
      "%1.3f,%1.3f" % (lat1,lon1),
      12,
      7,
      2,
      fg,bg)
      
    self.boxedText(
      cr,
      x2, y2,
      "%1.3f,%1.3f" % (lat2,lon2),
      12,
      3,
      2,
      fg,bg)

  def boxedText(self, cr, x,y,text, size=12, align=1, border=2, fg=(0,0,0), bg=(1,1,1)):
    
    cr.set_font_size(12)
    extents = cr.text_extents(text)
    (w,h) = (extents[2], extents[3])

    x1 = x
    if(align in (9,6,3)):
      x1 -= w
    elif(align in (8,5,2)):
      x1 -= 0.5 * w
          
    y1 = y
    if(align in (7,8,9)):
      y1 += h
    elif(align in (4,5,6)):
      y1 += 0.5 * h

    cr.set_source_rgb(bg[0],bg[1],bg[2])
    cr.rectangle(x1 - border, y1 + border, w +2*border, -(h+2*border))
    cr.fill()
    
    cr.set_source_rgb(fg[0],fg[1],fg[2])
    cr.move_to(x1,y1)
    cr.show_text(text)
    cr.fill()

