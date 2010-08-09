#!/usr/bin/python
#---------------------------------------------------------------------------
# Does routing using pyroutelib2
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


import sys

if(__name__ == '__main__'):
  sys.path.append('pyroutelib2')
else:
  sys.path.append('modules/pyroutelib2')

from loadOsm import *
from route import Router

def getModule(m,d):
  return(route(m,d))

class route(ranaModule):
  """Routes"""
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.route = []
    
  def handleMessage(self, message, type, args):
    if(message == "route"): # simple route, from here to selected point
      to_pos = self.get("selected_pos", None)
      if(to_pos):
        to_lat,to_lon = [float(a) for a in to_pos.split(",")]

        from_pos = self.get("pos", None)
        if(from_pos):
          (from_lat, from_lon) = from_pos
          #print "Routing %1.3f,%1.3f to %1.3f,%1.3f" % (from_lat, from_lon, to_lat, to_lon)

          # TODO: wait message
          self.doRoute(from_lat, from_lon, to_lat, to_lon)
          self.set("menu",None)

  def doRoute(self, from_lat, from_lon, to_lat, to_lon):
    """Route from one point to another, and set that as the active route"""
    data = LoadOsm(self.get('transport', 'cycle'))

    node1 = data.findNode(from_lat, from_lon)
    node2 = data.findNode(to_lat, to_lon)
    print "Routing from node %d to %d..." %(node1,node2)

    router = Router(data)
    result, route = router.doRoute(node1, node2)
    
    if result == 'success':
      self.route = []
      for node_id in route:
        node = data.rnodes[node_id]
        self.route.append((node[0], node[1]))
      print "Route discovered"
    else:
      print "Error in routing: " + result
      

  def drawMapOverlay(self, cr):
    """Draw a route"""
    # Where is the map?
    proj = self.m.get('projection', None)
    if(proj == None):
      return
    if(not proj.isValid()):
      return
    if(not len(self.route)):
      return
    cr.set_source_rgb(0,0, 0.5)
    cr.set_line_width(7)
    first = True
    for p in self.route:
      (lat,lon) = p
      x,y = proj.ll2xy(lat,lon)
      if(first):
        cr.move_to(x,y)
        first = False
      else:
        cr.line_to(x,y)
      
    cr.stroke()
    
if(__name__ == '__main__'):
  d = {'transport':'car'}
  a = route({},d)
  a.doRoute(51.51565, 0.06036, 51.65299, -0.19974) # Beckton -> Barnet
  print a.route
  
  