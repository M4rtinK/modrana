#!/usr/bin/python
#---------------------------------------------------------------------------
# Finds routes using Google Direction (and possibly other services in the future).
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
    
  def handleMessage(self, message):
    if(message == "route"): # simple route, from here to selected point
      toPos = self.get("selectedPos", None)
      if(toPos):
        toLat,toLon = [float(a) for a in toPos.split(",")]

        fromPos = self.get("pos", None)
        if(fromPos):
          (fromLat, fromLon) = fromPos
          print "Routing %f,%f to %f,%f" % (fromLat, fromLon, toLat, toLon)

          # TODO: wait message
          self.doRoute(fromLat, fromLon, toLat, toLon)
          self.set("menu",None)

  def doRoute(self, fromLat, fromLon, toLat, toLon):
    """Route from one point to another, and set that as the active route"""
    online = self.m.get('onlineServices', None)
    if online == None:
      return
    directions = online.googleDirectionsLL(fromLat, fromLon, toLat, toLon)
    if directions == None:
      return
    polyline = directions['Directions']['Polyline']['points'] # the route is encoded as a polyline
    route = self.decode_line(polyline) # we decode the polyline to a list of points

    self.route = route

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
    route = self.route
    for point in route:
      (lat,lon) = (point[0],point[1])
      x,y = proj.ll2xy(lat,lon)
      if(first):
        cr.move_to(x,y)
        first = False
      else:
        cr.line_to(x,y)
      
    cr.stroke()

  #from: http://seewah.blogspot.com/2009/11/gpolyline-decoding-in-python.html
  def decode_line(self, encoded):

    """Decodes a polyline that was encoded using the Google Maps method.

    See http://code.google.com/apis/maps/documentation/polylinealgorithm.html

    This is a straightforward Python port of Mark McClure's JavaScript polyline decoder
    (http://facstaff.unca.edu/mcmcclur/GoogleMaps/EncodePolyline/decode.js)
    and Peter Chng's PHP polyline decode
    (http://unitstep.net/blog/2008/08/02/decoding-google-maps-encoded-polylines-using-php/)
    """

    encoded_len = len(encoded)
    index = 0
    array = []
    lat = 0
    lng = 0

    while index < encoded_len:

        b = 0
        shift = 0
        result = 0

        while True:
            b = ord(encoded[index]) - 63
            index = index + 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break

        dlat = ~(result >> 1) if result & 1 else result >> 1
        lat += dlat

        shift = 0
        result = 0

        while True:
            b = ord(encoded[index]) - 63
            index = index + 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break

        dlng = ~(result >> 1) if result & 1 else result >> 1
        lng += dlng

        array.append((lat * 1e-5, lng * 1e-5))

    return array
    
if(__name__ == '__main__'):
  d = {'transport':'car'}
  a = route({},d)
  a.doRoute(51.51565, 0.06036, 51.65299, -0.19974) # Beckton -> Barnet
  print a.route
  
  