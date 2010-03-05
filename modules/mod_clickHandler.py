#!/usr/bin/python
#----------------------------------------------------------------------------
# Allows areas of screen to be registered as clickable, sending a message
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
import cairo
from rect import rect

def getModule(m,d):
  return(clickHandler(m,d))

class clickHandler(ranaModule):
  """handle mouse clicks"""
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.beforeDraw()
    self.cycle = 0

  def beforeDraw(self):
    self.areas = []
    self.dragareas = []
    self.dragscreen = None

  def register(self, rect, action):
    self.areas.append([rect, action])
  
  def registerXYWH(self, x1,y1,dx,dy, action):
    area = rect(x1,y1,dx,dy)
    self.register(area, action)
  
  def registerXYXY(self, x1,y1,x2,y2, action):
    area = rect(x1,y1,x2-x1,y2-y1)
    self.register(area, action)
    
  def handleClick(self, x,y):
    #print "Clicked at %d,%d" % (x,y)
    for area in self.areas:
      (rect, action) = area
      if(rect.contains(x,y)):
        m = self.m.get("messages", None)
        if(m != None):
          print "Clicked, sending " + action
          m.routeMessage(action)
        else:
          print "No message handler to receive clicks"
          
  def registerDraggable(self, x1,y1,x2,y2, module):
    self.dragareas.append((rect(x1,y1,x2-x1,y2-y1), module))

  def registerDraggableEntireScreen(self, module):
    print "Entire screen is draggable for %s " % module
    self.dragscreen = module

  def handleDrag(self,startX,startY,dx,dy,x,y):
    if(self.dragscreen):
      m = self.m.get(self.dragscreen, None)
      if(m != None):
        m.dragEvent(startX,startY,dx,dy,x,y)
    else:
	    for area in self.dragareas:
	      (rect, module) = area
	      if(rect.contains(startX,startY)):
	        m = self.m.get(module, None)
	        if(m != None):
	          m.dragEvent(startX,startY,dx,dy,x,y)
	        else:
	          print "Drag registered to nonexistant module %s" % module
	  
  def update(self):
    self.cycle += 1

if(__name__ == "__main__"):
  print "Testing rect"
  a = clickHandler({},{})