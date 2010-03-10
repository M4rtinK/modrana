#!/usr/bin/python
#----------------------------------------------------------------------------
# Overlay some information on the map screen
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
from datetime import *

def getModule(m,d):
  return(infoOverlay(m,d))

class infoOverlay(ranaModule):
  """Overlay info on the map"""
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.lines = ['hello', 'world']
    self.oldlines = ['','']
    self.mode = 0
    self.isGraphical = False
    self.modes = ['pos', 'gps', 'road', 'speed', 'maxSpeed', 'bearing', 'time']
    self.unitString = ""

  def get_none(self):
    pass
  
  def get_pos(self):
    pos = self.get('pos', None)
    if(pos == None):
      self.lines.append('No position')
    else:
      self.lines.append('%1.4f, %1.4f' % pos)
      self.lines.append("Position from: %s" % self.get('pos_source', 'unknown'))
  
  def get_gps(self):
    self.isGraphical = "GPS"
    
  def get_road(self):
    text = self.get('nearest_road', None)
    if(text != None):
      self.lines.append(text)
    text = self.get('nearest_place', None)
    if(text != None):
      self.lines.append(text)
    if(len(self.lines) == 0):
      self.lines.append('No data')

  def get_speed(self):
    self.lines.append('Speed: %1.1f ' % self.get('speed', 0) + self.unitString)
  
  def get_bearing(self):
    self.lines.append('Bearing: %03.0f ' % self.get('bearing', 0))
  def get_maxSpeed(self):
    self.lines.append('Max: %1.1f ' % self.get('maxSpeed', 0) + self.unitString)
    self.lines.append('Average: %1.1f ' % self.get('avgSpeed', 0) + self.unitString)
  
  def get_time(self):
    now = datetime.now()
    self.lines.append(now.strftime("%Y-%m-%d (%a)"))
    self.lines.append(now.strftime("%H:%M:%S"))
  

  def update(self):
    return #TODO: rewrite this
    # The get_xxx functions all fill-in the self.lines array with
    # text to display, where xxx is the selected mode
    self.lines = []
    self.isGraphical = False
    fn = getattr(self, "get_%s" % self.modes[self.mode], self.get_none)
    fn()

    # Detect which units we are using and set the description acordingly
    if self.get("unitType", "kmh") == "kmh":
      self.unitString = "km/h"
    else:
      self.unitString = "mph"

    # Detect changes to the lines being displayed,
    # and ask for redraw if they change
    if(len(self.lines) != len(self.oldlines) or self.isGraphical):
      self.set('needRedraw', True)
    else:
      for i in range(len(self.lines)):
        if(self.lines[i] != self.oldlines[i]):
          self.set('needRedraw', True)
    self.oldlines = self.lines

  def onModeChange(self):
    self.set('lookup_road', self.modes[self.mode] == 'road')
    self.set('lookup_place', self.modes[self.mode] == 'road')

  def handleMessage(self, message):
    if(message == 'nextField'):
      self.mode += 1
      if(self.mode >= len(self.modes)):
        self.mode = 0
      self.onModeChange()
      
  def drawGPS(self, cr,x,y,w,h):
    num = self.get("gps_num_sats", 0)
    #print "%d sats" % num
    if(num < 1):
      return
    
    max = 1.0
    sats = []
    for i in range(num):
      (db,used,id) = self.get("gps_sat_%d"%i, (0,0,0))

      db = float(db)
      sats.append((db, used, id))
      if(db > max):
        max = db

    max *= 1.1

    dx = w / float(num)
    barWidth = dx * 0.7

    for sat in sats:
      (db,used,id) = sat
      #print "%d: %f" % (i, db)
      
      # Signal strength meter
      if(used):
        cr.set_source_rgb(0,0.7,0.9)
      else:
        cr.set_source_rgb(0,0.3,0.5)
      barHeight = h * (float(db) / max)
      cr.rectangle(x,y,barWidth,barHeight)
      cr.fill()

      # Satellite ID atop the signal strength meter
      cr.set_font_size(20.0 * 8.0 / float(num))
      cr.set_source_rgb(1,1,0)
      cr.move_to(x+6, y - 4)
      cr.show_text("%02d" % id)
      cr.stroke()
      
      x += dx
      
  def drawMapOverlay(self, cr):
    return #TODO: rewrite this
    """Draw an overlay on top of the map, showing various information
    about position etc."""
    (x,y,w,h) = self.get('viewport')

    # Bottom of screen:
    dy = h * 0.13
    border = 10

    y2 = y + h
    y1 = y2 - dy
    x1 = x

    # Clicking on the rectangle should toggle which field we display
    m = self.m.get('clickHandler', None)
    if(m != None):
      m.registerXYWH(x1,y1,w,dy, "infoOverlay:nextField")
    # Draw a background
    cr.set_source_rgb(0,0,0)
    cr.rectangle(x1,y1,w,dy)
    cr.fill()
    if(self.isGraphical == 'GPS'):
      self.drawGPS(cr,x,y2,w,-dy)

    numlines = len(self.lines)
    if(numlines < 1):
      return
    linespacing = (dy / numlines)
    fontsize = linespacing * 0.8

    cr.set_source_rgb(1.0, 1.0, 0.0)

    liney = y1
    for text in self.lines:
      # Check that font size is small enough to display width of text
      fontx = w / len(text)
      if(fontx < fontsize):
        cr.set_font_size(fontx)
      else:
        cr.set_font_size(fontsize)

      # Draw the text
      cr.move_to(x1+border,liney + (0.9 * linespacing))
      cr.show_text(str(text))
      cr.stroke()
      liney += linespacing

