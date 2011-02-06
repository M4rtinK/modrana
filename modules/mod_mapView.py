#!/usr/bin/python
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
from base_module import ranaModule
from time import time
from tilenames import *

def getModule(m,d):
  return(mapView(m,d))

class mapView(ranaModule):
  """Controls the view being displayed on the map"""
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.lastPos = None
    
  def handleMessage(self, message, type, args):
    z = self.get('z', 15)
    if(message == 'zoomIn'):
      self.set('z', z + 1)
    elif(message == 'zoomOut'):
#      self.set('z', max(z - 1, 8))
      self.set('z', max(z - 1, 6))

    elif (message=='recentreToPos'):
      pos = self.get('pos', None)
      proj = self.m.get('projection', None)
      if pos and proj:
        (lat,lon) = pos
        proj.recentre(lat, lon, z)

    elif(message):
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
      except:
        print "mapView: cant recentre cooridnates"
  
  def dragEvent(self,startX,startY,dx,dy,x,y):
    # check if centering is on
    if self.get("centred",True):
      fullDx = x - startX
      fullDy = y - startY
      distSq = fullDx * fullDx + fullDy * fullDy
      """ check if the drag is strong enought to disable centering
      -> like this, centering is not dsabled by pressing buttons"""
      if distSq > 1024:
        self.set("centred",False) # turn off centering after dragging the map (like in TangoGPS)
    else:
      proj = self.m.get('projection', None)
      if proj:
        proj.nudge(dx,dy)
        self.set('needRedraw', True)

  def handleCentring(self):
    # check if centring is on
    if(self.get("centred",True) or self.get('centreOnce', False)):
      # get current position information
      pos = self.get('pos', None)
      # check if the position changed from last time
      if pos != self.lastPos:
        if(self.setCentre(pos)):
          self.set('centreOnce', False)
        self.lastPos = pos


        

#    request = self.get("centreOn", None)
#    if(request):
#      self.setCentre([float(a) for a in request.split(",")])
      
  def setCentre(self,pos):
    """takes care for centering the map on current position"""
    proj = self.m.get('projection', None)
    if proj and pos:
      (lat,lon) = pos
      self.set('map_centre', pos)

      z = int(self.get('z', 15))
      x,y = latlon2xy(lat,lon,z)

      if(not self.d.has_key('viewport')):
        return(False)
      (sx,sy,sw,sh) = self.get('viewport')


      """
      the shift amount represents a perentage of the distance from screen center
      to an edge:
      ceneter+---------->|edge
      0 -> no shift
      1 -> directly on the edge
      0.5 -> shifted by half of this distance, eq. in 3/4 of the screen
      """
      shiftAmount = self.get('posShiftAmount', None)
      if shiftAmount:
        intShiftAmount = int(shiftAmount)
        shiftDirection = self.get('posShiftDirection', "down")
        if shiftDirection == "down":
          y = y - sh * 0.5 * intShiftAmount
        elif shiftDirection == "up":
          y = y + sh * 0.5 * intShiftAmount
        elif shiftDirection == "left":
          x = x + sw * 0.5 * intShiftAmount
        else: # right
          x = x + sw * 0.5 * intShiftAmount

        (lat, lon) = proj.xy2ll(x, y)


      print (sx,sy,sw,sh)
      proj.recentre(lat,lon,z)
      self.set("needRedraw", True)
      return(True)