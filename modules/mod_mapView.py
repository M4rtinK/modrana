# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Controls the view being displayed on the map
#---------------------------------------------------------------------------
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
from modules.base_module import RanaModule

def getModule(m,d,i):
  return MapView(m,d,i)

class MapView(RanaModule):
  """Controls the view being displayed on the map"""
  def __init__(self, m, d, i):
    RanaModule.__init__(self, m, d, i)

  def firstTime(self):
    self.checkMapDraggingMode() # check the map dragging mode on startup
    self.checkCenteringDisableThreshold() # check centering disable treshold on startup
    self.lastZ = int(self.get('z', 15))
    
  def handleMessage(self, message, type, args):
    z = self.get('z', 15)
    if message == 'zoomIn':
      newZ = z + 1
      self.set('z', newZ)
      proj = self.m.get('projection', None)
      if proj:
        proj.setZoom(newZ)
      self.notify("zooming <b>in</b> to zl %d" % newZ)
    elif message == 'zoomOut':
      newZ = max(z - 1, 4)
      self.set('z', newZ)
      proj = self.m.get('projection', None)
      if proj:
        proj.setZoom(newZ)
      if newZ != z:
        self.notify("zooming <b>out</b> to zl %d" % newZ)
      else:
        self.notify("minimum zoomlevel reached")


    elif message=='recentreToPos':
      pos = self.get('pos', None)
      proj = self.m.get('projection', None)
      if pos and proj:
        (lat,lon) = pos
        proj.recentre(lat, lon, z)

    elif message=="dragModeChanged":
      self.checkMapDraggingMode()

    elif message=="centeringDisableThresholdChanged":
      self.checkCenteringDisableThreshold()

    elif message:
      try:
        list = message.split(' ')
        lat = float(list[1])
        lon = float(list[2])
        if len(list) == 4:
          zoom = int(list[3])
        else:
          zoom = z
        proj = self.m.get('projection', None)
        self.set("centred",False) # turn off centering before moving screen to the coordinates
        proj.recentre(lat, lon, zoom)
      except Exception, e:
        print("mapView: cant recenter coordinates")
        print(e)
  
  def dragEvent(self,startX,startY,dx,dy,x,y):
    """only drag the map if centering is disabled"""
    if not self.get("centred",False):
      proj = self.m.get('projection', None)
      if proj:
        proj.nudge(dx,dy)
        self.set('needRedraw', True)

  def handleCentring(self):
    """check if centring is on"""
    if self.get("centred",True):
      # get current position information
      pos = self.get('pos', None)
      # check if the position changed from last time
      self.setCentre(pos)     
      
  def setCentre(self,pos):
    """takes care for centering the map on current position"""
    proj = self.m.get('projection', None)
    if proj and pos:
      (lat,lon) = pos
      self.set('map_centre', pos)
      z = int(self.get('z', 15))
      x,y = proj.ll2xy(lat,lon)
      if not self.d.has_key('viewport'):
        return False
      (sx,sy,sw,sh) = self.get('viewport')
      # the shift amount represents a percentage of the distance from screen center
      # to an edge:
      # center+---------->|edge
      # 0 -> no shift
      # 1 -> directly on the edge
      # 0.5 -> shifted by half of this distance, eq. in 3/4 of the screen
      newZoom = None
      if z != self.lastZ:
        newZoom = z
        self.lastZ = newZoom
      proj.recentre(lat,lon,newZoom)
      return True

  # * map dragging mode control * #

  def checkMapDraggingMode(self):
    """check and set current redraw mode configuration"""
    draggingMode = self.get('mapDraggingMode', "default")
    print("mapView: switching map drag mode to %s" % draggingMode)
    if draggingMode == 'default':
      self.modrana.gui.enableDefaultDrag()
    elif draggingMode == "staticMapDrag":
      self.modrana.gui.enableStaticMapDrag()

  def checkCenteringDisableThreshold(self):
    """check ans set current centering disable threshold"""
    centeringDisableThreshold = self.get('centeringDisableThreshold', 2048)
    print("mapView: switching centering disable threshold to %s" % centeringDisableThreshold)
    self.modrana.gui.setCDDragThreshold(int(centeringDisableThreshold))

  def jump2point(self, point):
    """recenter on a given point"""
    z = self.get('z', 15)
    lat, lon = point.getLL()
    self.sendMessage('mapView:recentre %f %f %d|set:menu:None|set:needRedraw:True' % (lat, lon, z))

