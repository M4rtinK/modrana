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

def getModule(m,d):
  return(showOSD(m,d))

class showOSD(ranaModule):
  """Draw OSD (On Screen Display)."""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.items = None
    self.avail = set(
                      'speed'
                      )
    
  def update(self):
    # Get and set functions are used to access global data
    self.set('num_updates', self.get('num_updates', 0) + 1)
    #print "Updated %d times" % (self.get('num_updates'))

  def drawScreenOverlay(self, cr):
#    if items:
    if True:
      config = self.m.get('config', None).userConfig

#      relevant [item in osd, for   ]
#      maxElevationPoint = (max(pointsWithElevation, key=lambda x: x.elevation))

      mode = self.get('mode', None)
      if mode == None:
        return

      if mode not in config:
        return

      items = config[mode]['OSD']
      print items

      if 'speed' in items:

        item = items['speed']

        x = float(item['x'])
        y = float(item['y'])
        w = float(item['w'])
        h = float(item['h'])
        fontSize = 30
        speed = self.get('speed', 0)
        units = self.m.get('units', None)
        speedString = units.km2CurrentUnitPerHourString(speed)
  #      stats = self.m.get('stats', None)
  #      proj = self.m.get('projection', None)
  #      (x1,y1) = proj.screenPos(0.5, 0.5) # middle fo the screen
        cr.set_font_size(fontSize)
        text = speedString
        cr.set_source_rgba(0, 0, 1, 0.45) # trasparent blue
        extents = cr.text_extents(text)
        (w,h) = (extents[2], extents[3])
  #      (x,y) = (x1-w/2.0,y1-h/2.0)
        cr.set_line_width(2)
        cr.set_source_rgba(0, 0, 1, 0.45) # trasparent blue
        (rx,ry,rw,rh) = (x-0.25*w, y-h*1.5, w*1.5, (h*2))
        cr.rectangle(rx,ry,rw,rh) # create the transparent background rectangle
        cr.fill()
        cr.set_source_rgba(1, 1, 1, 0.95) # slightly trasparent white
        cr.move_to(x+10,y)
        cr.show_text(text) # show the trasparent notification text
        cr.stroke()
        cr.fill()





if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
