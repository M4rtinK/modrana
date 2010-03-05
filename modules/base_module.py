#!/usr/bin/python
#----------------------------------------------------------------------------
# Base class for Rana modules
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
class ranaModule:
  def __init__(self, modules={}, data={}):
    self.m = modules
    self.d = data
    self.status = ''
    self.moduleName = '' # will be provided by rana.py
    self.device = '' # will be provided by rana.py
    
  def module_exists(self, module):
    """Test whether a named module is loaded"""
    return(self.m.get(module, None) != None)
  
  def get(self, name, default=None):
    """Get an item of data"""
    return(self.d.get(name, default))
  
  def set(self, name, value):
    """Set an item of data"""
    if(self.module_exists('watchlist')):
      self.m['watchlist'].notify(name, value, self.d.get(name, None))
    self.d[name] = value
    
  def getStatus(self):
    return(self.status)
  
  # Overridable
  def firstTime(self):
    """Runs on application start (after all other modules are loaded)"""
    pass
  def update(self):
    """Regular updates (several per second)"""
    pass
  def beforeDraw(self):
    """Before a screen is redrawn (don't use this for regular updates)"""
    pass
  def drawMenu(self, cr, menuName):
    """Drawing, in menu mode.  Only handle this if you know your menu is active"""
    pass
  def drawMap(self, cr):
    """Draw the base map"""
    pass
  def drawMapOverlay(self, cr):
    """Draw overlay that's part of the map"""
    pass
  def drawScreenOverlay(self, cr):
    """Draw overlay that's on top of all maps"""
    pass
  def handleMessage(self, message):
    """Handles a message from another module, or in response to user action"""
    pass
  def dragEvent(self,startX,startY,dx,dy,x,y):
    """Handles notification of a drag event"""
    pass
  def shutdown(self):
    """Program is about to shutdown (don't rely solely on this for anything important like saving someone's tracklog!)"""
    pass
