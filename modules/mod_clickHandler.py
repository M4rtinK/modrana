#!/usr/bin/python
# -*- coding: utf-8 -*-
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
from rect import rect

def getModule(m,d,i):
  return(clickHandler(m,d,i))

class clickHandler(ranaModule):
  """handle mouse clicks"""
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.beforeDraw()
    self.ignoreNextClicks = 0

  def beforeDraw(self):
    self.areas = []
    self.dragareas = []
    self.dragscreen = None
    self.timedActionInProgress = None

  def register(self, rect, action, timedAction):
    self.areas.append([rect, action, timedAction])
  
  def registerXYWH(self, x1,y1,dx,dy, action, timedAction=None):
    if timedAction: # at least one timed action
      self.timedActionInProgress = True
    area = rect(x1,y1,dx,dy)
    self.register(area, action, timedAction)
  
  def registerXYXY(self, x1,y1,x2,y2, action, timedAction=None):
    if timedAction: # at least one timed action
      self.timedActionInProgress = True
    area = rect(x1,y1,x2-x1,y2-y1)
    self.register(area, action, timedAction)
    
  def handleClick(self, x, y, msDuration):
#    print "Clicked at %d,%d for %d" % (x,y,msDuration)
    if self.ignoreNextClicks > 0:
      self.ignoreNextClicks=self.ignoreNextClicks - 1
#      print "ignoring click, %d remaining" % self.ignoreNextClicks
    else:
      for area in self.areas:
        (rect, action, timedAction) = area
        if(rect.contains(x,y)):
          m = self.m.get("messages", None)
          if m:
            print "Clicked, sending %s" % action
            self.set('lastClickXY', (x,y))
            m.routeMessage(action)
          else:
            print "No message handler to receive clicks"
    self.set('needRedraw', True)

  def handleLongPress(self, pressStartEpoch, msCurrentDuration, startX, startY, x, y):
    """handle long press"""

    """ make sure subsegvent long presses are ignored until release """
    if self.ignoreNextClicks == 0:
      for area in self.areas:
        (rect, normalAction, timedAction) = area
        if timedAction: # we are interested only in timed actions
          if(rect.contains(x,y)):
            (givenMsDuration, action) = timedAction
            if givenMsDuration <= msCurrentDuration:
              m = self.m.get("messages", None)
              if m:
                print "Long-clicked (%f ms), sending %s" % (givenMsDuration, action)
                self.set('lastClickXY', (x,y))
                self.modrana.gui.lockDrag()
                m.routeMessage(action)
                self.set('needRedraw', True)
              else:
                print "No message handler to receive clicks"
              self.ignoreNextClicks = self.dmod.lpSkipCount()
          
  def registerDraggable(self, x1,y1,x2,y2, module):
    self.dragareas.append((rect(x1,y1,x2-x1,y2-y1), module))

  def registerDraggableEntireScreen(self, module):
    print "Entire screen is draggable for %s " % module
    self.dragscreen = module

  def handleDrag(self,startX,startY,dx,dy,x,y,msDuration):
    # react on timed actions interactively
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

if(__name__ == "__main__"):
  print "Testing rect"
  a = clickHandler({},{})