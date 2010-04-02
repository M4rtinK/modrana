#!/usr/bin/python
#----------------------------------------------------------------------------
# This module provides notification support.
#----------------------------------------------------------------------------
# Copyright 2007, Oliver White
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
  return(notification(m,d))

class notification(ranaModule):
  """This module provides notification support."""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.notificationText = ""
    self.timeout = 5
    self.position = 'middle'
    self.expirationTimestamp = time.time()
    self.draw = False
    
  def update(self):
#    # Get and set functions are used to access global data
#    self.set('num_updates', self.get('num_updates', 0) + 1)
#    #print "Updated %d times" % (self.get('num_updates'))
    pass

  def handleMessage(self, message):
    """the first part is the message, that will be displayed,
       there can also by some parameters, delimited by |"""
    list = message.split('|')
    # TODO: supprot setting timeout and position
    timeout = self.timeout
    self.position = 'middle'
    self.expirationTimestamp = time.time() + timeout
    self.notificationText = list[0]
    self.draw = True # enable drawing of notifications


  def drawMenu(self,cr,menuName):
    """We want the notification to work even over the menu."""
    if self.draw == True:
      self.drawNotification(cr)

  def drawScreenOverlay(self, cr):
    """We want the notification to work even over the map."""
    if self.draw == True:
      self.drawNotification(cr)

  def drawNotification(self, cr):
    """Draw the notifications on the screen on top of everything."""
    timestamp = time.time()
    expirationTimestamp = self.expirationTimestamp
    if timestamp <= expirationTimestamp:
      proj = self.m.get('projection', None)
      (x1,y1) = proj.screenPos(0.5, 0.5) # middle fo the screen
      cr.set_font_size(30)
      text = self.notificationText
      cr.set_source_rgba(0, 0, 1, 0.45) # trasparent blue
      extents = cr.text_extents(text)
      (w,h) = (extents[2], extents[3])
      (x,y) = (x1-w/2.0,y1-h/2.0)
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
    else:
      self.draw = False # we are finished, disable drawing notifications









if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
