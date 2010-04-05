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
import math
from time import clock

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
    self.directions = []
    self.start = None
    self.destination = None
    self.text = None
    
  def handleMessage(self, message):
    if (message == "clear"):
      self.route = []
      self.directions = []
      self.start = None
      self.destination = None
      self.text = None


    if(message == "route"): # simple route, from here to selected point
      toPos = self.get("selectedPos", None)
      if(toPos):
        toLat,toLon = [float(a) for a in toPos.split(",")]

        fromPos = self.get("pos", None)
        if(fromPos):
          (fromLat, fromLon) = fromPos
          print "Routing %f,%f to %f,%f" % (fromLat, fromLon, toLat, toLon)

          # TODO: wait message (would it bee neede when using internet routing ?)
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
    self.directions = directions
    # reverse geocode the start and destination coordinates (for the info menu)
    startAddress = online.googleReverseGeocode(fromLat,fromLon)
    destinationAddress = online.googleReverseGeocode(toLat,toLon)
    self.start = (fromLat, fromLon, startAddress)
    self.destination = (toLat, toLon, destinationAddress)

  def drawMapOverlay(self, cr):
    """Draw a route"""
    start1 = clock()
    # Where is the map?
    proj = self.m.get('projection', None)
    if(proj == None):
      return
    if(not proj.isValid()):
      return
    if(not len(self.route)):
      return

    route = self.route

    # as you can see, for some reason, the cooridnates in direction steps are reversed, (lon,lat,0)
    steps = map(lambda x: (x['Point']['coordinates'][1],x['Point']['coordinates'][0]), self.directions['Directions']['Routes'][0]['Steps'])

    steps.append(route[len(route)-1])

    # now we convert geographic cooridnates to screen coordinates, so we dont need to do it twice
    steps = map(lambda x: (proj.ll2xy(x[0],x[1])), steps)

    # geo to screen at once
    route = map(lambda x: (proj.ll2xy(x[0],x[1])), route)

    start = proj.ll2xy(self.start[0], self.start[1])
    destination = proj.ll2xy(self.destination[0], self.destination[1])

    # line from starting point to start of the route
    (x,y) = start
    (x1,y1) = steps[0]
    cr.set_source_rgba(0, 0, 0.5, 0.45)
    cr.set_line_width(10)
    cr.move_to(x,y)
    cr.line_to(x1,y1)
    cr.stroke()

    # line from the destination point to end of the route
    (x,y) = destination
    (x1,y1) = steps[len(steps)-1]
    cr.move_to(x,y)
    cr.line_to(x1,y1)
    cr.stroke()

    cr.fill()

    # draw the stepp point background (under the polyline, it seems to look better this way)

    cr.set_source_rgb(0, 0, 0)
    cr.set_line_width(10)

    for step in steps:
      (x,y) = (step)
      cr.arc(x, y, 3, 0, 2.0 * math.pi)
      cr.stroke()

    cr.fill()



    cr.set_source_rgb(0, 0, 0.5)
    cr.set_line_width(10)

    # draw the points from the polyline as a polyline :)
    first = True
    
    for point in route:
#      (lat,lon) = (point[0],point[1])
#      x,y = proj.ll2xy(lat,lon)
      (x,y) = (point)
      if(first):
        cr.move_to(x,y)
        first = False
      else:
        cr.line_to(x,y)
    cr.stroke()

    # draw the step points over then polyline
    cr.set_source_rgb(1, 1, 0)
    cr.set_line_width(7)
    for step in steps:
      (x,y) = (step)
      cr.arc(x, y, 2, 0, 2.0 * math.pi)
      cr.stroke()
    cr.fill()

    print "Redraw took %1.2f ms" % (1000 * (clock() - start1))


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


  def drawMenu(self, cr, menuName):
    if menuName != 'currentRoute':
      return

    menus = self.m.get("menu",None)
    if menus == None:
      return
    parent = 'route'

    if self.route == []:
      action = "set:menu:None"
    else:
      (lat,lon) = self.route[0]
      action = "mapView:recentre %f %f|set:menu:None" % (lat, lon)

    button1 = ("map#show on", "generic", action)
    button2 = ("tools", "generic", "set:menu:currentRoute")
#    activePOINr = int(self.get('activePOINr', 0))
#    point = points[activePOINr]

    if self.route == []:
      text = "There is currently no active route."
    elif self.text == None: # the new text for the infobox only once
      dir = self.directions
      duration = dir['Directions']['Duration']['html'] # a string describing the estimated time to finish the route
      units = self.m.get('units', None) # get the correct units
      distance = units.m2CurrentUnitString(float(dir['Directions']['Distance']['meters']))
      steps = len(dir['Directions']['Routes'][0]['Steps']) # number of steps

      start = ""
      startAddress = self.start[2]
      (lat1,lon1) = (self.start[0],self.start[1])
      for item in startAddress.split(','):
        start += "|%s" % item
  #    start += "|(%f,%f)" % (lat1,lon1)

      destination = ""
      destinationAddress = self.destination[2]
      (lat2,lon2) = (self.destination[0],self.destination[1])
      for item in destinationAddress.split(','):
        destination += "|%s" % item
  #    destination += "|(%f,%f)" % (lat2,lon2)

      text = "%s" % start
      text+= "|%s" % destination
      text+= "||%s in about %s and %s steps" % (distance, duration, steps)
      text+= "|(%f,%f)->(%f,%f)" % (lat1,lon1,lat2,lon2)

      self.text = text
    else:
      text = self.text

    box = (text , "set:menu:currentRoute")
    menus.drawThreePlusOneMenu(cr, menuName, parent, button1, button2, box)
    

if(__name__ == '__main__'):
  d = {'transport':'car'}
  a = route({},d)
  a.doRoute(51.51565, 0.06036, 51.65299, -0.19974) # Beckton -> Barnet
  print a.route
  
  