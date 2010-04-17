#!/usr/bin/python
#----------------------------------------------------------------------------
# Draw OSD (On Screen Display).
#----------------------------------------------------------------------------
# Copyright 2010, Martin Kolman
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
import time

def getModule(m,d):
  return(showOSD(m,d))

class showOSD(ranaModule):
  """Draw OSD (On Screen Display)."""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.items = None
#    self.avail = set(
#                      'speed'
#                      )
    
  def update(self):
    # Get and set functions are used to access global data
    self.set('num_updates', self.get('num_updates', 0) + 1)
    #print "Updated %d times" % (self.get('num_updates'))

  def drawScreenOverlay(self, cr):
#    if items:
    if self.m.get('config', {}):
      config = self.m.get('config', None).userConfig

#      relevant [item in osd, for   ]
#      maxElevationPoint = (max(pointsWithElevation, key=lambda x: x.elevation))

      mode = self.get('mode', None)
      if mode == None:
        return

      if mode not in config:
        return
      if 'OSD' in config[mode]:
        items = config[mode]['OSD']
        for item in items:
          self.drawWidget(cr,items[item],item)


  def drawWidget(self, cr, item, type):
    if type == 'speed':
      speed = self.get('speed', 0)
      units = self.m.get('units', None)
#      speedString = "%1.0f|" % units.km2CurrentUnit(speed)
#      speedString+= units.currentUnitPerHourString()
      speedString = units.km2CurrentUnitPerHourString(speed)
      self.drawMultilineTextWidget(cr, item, speedString)
    elif type == 'time':
      timeString = time.strftime("%H:%M")
      self.drawMultilineTextWidget(cr, item, timeString)
    elif type == 'coordinates':
      pos = self.get('pos', None)
      if pos == None:
        return
      posString = "%f(lat)|%f(lon)" % pos
      self.drawMultilineTextWidget(cr, item, posString)
    elif type == 'statistics':
      units = self.m.get('units', None)
      maxSpeed = self.get('maxSpeed', 0)
      avg = self.get('avgSpeed', 0)
      statString = "max:%s|" % units.km2CurrentUnitPerHourStringTwoDP(maxSpeed)
      statString+= "avg:%s" % units.km2CurrentUnitPerHourStringTwoDP(avg)
      self.drawMultilineTextWidget(cr, item, statString)


  def drawMultilineTextWidget(self,cr ,item ,text=""):
    if 'px' and 'py' in item:
      proj = self.m.get('projection', None)
      (px,py) = float(item['px']), float(item['py'])
      (x, y) = proj.screenPos(px,py)

      if 'font_size' in item:
        fontSize = int(item['font_size'])
      else:
        fontSize = 30
      cr.set_font_size(fontSize)

#      if 'pw' and 'ph' in item: # are the width and height set ?
#        w = proj.screenWidth(float(item['pw']))
#        h = proj.screenHeight(float(item['ph']))
#      else: # width and height are not set, we ge them from the text size
#        extents = cr.text_extents(text)
#        (w,h) = (extents[2], extents[3])

      lines  = text.split('|')
      print lines
      border = 10
      (w,h) = (0,0)
      yOffset = []
      for line in lines:
        print (w,h)
        extents = cr.text_extents(line)
        (w,h) = (max(w,extents[2]), h + extents[3] + border)
        yOffset.append(y+h)

      if 'align' in item:
        if item['align'] == 'right':
          x = x - w



      self.drawBackground(cr, x, y, w, h)
      
      i = 0
      for line in lines:
        self.drawText(cr, x, yOffset[i], line)
        i = i + 1




  def drawBackground(self, cr, x, y, w, h, source=None):
    cr.set_line_width(2)
    cr.set_source_rgba(0, 0, 1, 0.45) # trasparent blue
#    (rx,ry,rw,rh) = (x, y-h*1.4, w*1.2, (h*2))
    (rx,ry,rw,rh) = (x, y, w*1.2, h*1.2)
    cr.rectangle(rx,ry,rw,rh) # create the transparent background rectangle
    cr.fill()

  def drawText(self, cr, x, y, text, source=None):
    cr.set_source_rgba(1, 1, 1, 0.95) # slightly transparent white
    cr.move_to(x+10,y)
    cr.show_text(text) # show the trasparent notification text
    cr.stroke()
    cr.fill()

# from PyCha.color module
def hex2rgb(hexstring, digits=2):
    """Converts a hexstring color to a rgb tuple.

    Example: #ff0000 -> (1.0, 0.0, 0.0)

    digits is an integer number telling how many characters should be
    interpreted for each component in the hexstring.
    """
    if isinstance(hexstring, (tuple, list)):
        return hexstring

    top = float(int(digits * 'f', 16))
    r = int(hexstring[1:digits+1], 16)
    g = int(hexstring[digits+1:digits*2+1], 16)
    b = int(hexstring[digits*2+1:digits*3+1], 16)
    return r / top, g / top, b / top

if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
