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
import googlemaps # for handling google directions exceptions
import sys
import math
import gtk
import gobject
from time import sleep
from time import clock

#if(__name__ == '__main__'):
#  sys.path.append('pyroutelib2')
#else:
#  sys.path.append('modules/pyroutelib2')

#from loadOsm import *
#from route import Router

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
    self.selectTwoPoints = False
    self.selectOnePoint = False
    self.once = True
    self.entry = None

    self.expectStart = False
    self.expectEnd = False

    self.startAddress = None
    self.destinationAddress = None

    self.set('startPos', None)
    self.set('endPos', None)

  def handleMessage(self, message):
    if (message == "clear"):
      self.route = []
      self.directions = []
      self.start = None
      self.destination = None
      self.text = None
      self.selectTwoPoints = False
      self.selectOnePoint = False

      self.expectStart = False
      self.expectEnd = False

      self.set('startPos', None)
      self.set('endPos', None)

    elif(message == 'expectStart'):
      self.expectStart = True
      self.set('needRedraw', True) # we need to show the changed buttons

    elif(message == 'setStart'):
      if self.selectOnePoint:
        self.set('endPos', None)
      proj = self.m.get('projection', None)
      if proj != None and self.expectStart == True:
        lastClick = self.get('lastClickXY', None)
        (x, y) = lastClick
        """
        x and y must be floats, otherwise strang rounding errors occur, whan converting to lat lon coridnates
        """
        (lat, lon) = proj.xy2ll(x, y)
        self.set('startPos', (lat,lon))
        self.testStart = (lat,lon)

      self.expectStart = False
      self.set('needRedraw', True) # refresh the screen to show the new point

    elif(message == 'expectEnd'):
      self.expectEnd = True
      self.set('needRedraw', True) # we need to show the changed buttons

    elif(message == 'setEnd'):
      if self.selectOnePoint:
        self.set('startPos', None)
      proj = self.m.get('projection', None)
      if proj != None and self.expectEnd == True:
        lastClick = self.get('lastClickXY', None)
        (x, y) = lastClick
        """
        x and y must be floats, otherwise strang rounding errors occur, whan converting to lat lon coridnates
        """
        (lat, lon) = proj.xy2ll(x, y)
        self.set('endPos', (lat,lon))

      self.expectEnd = False
      self.set('needRedraw', True) # refresh the screen to show the new point

    elif(message == "selectTwoPoints"):
      self.set('startPos', None)
      self.set('endPos', None)
      self.selectOnePoint = False
      self.selectTwoPoints = True

    elif(message == "selectOnePoint"):
      self.set('startPos', None)
      self.set('endPos', None)
      self.selectTwoPoints = True # we reuse the p2p menu
      self.selectOnePoint = True

    elif(message == "p2pRoute"): # simple route, from here to selected point
      toPos = self.get("endPos", None)
      if(toPos):
        toLat,toLon = toPos

        fromPos = self.get("startPos", None)
        if(fromPos):
          fromLat,fromLon = fromPos

          print "Routing %f,%f to %f,%f" % (fromLat, fromLon, toLat, toLon)

          # TODO: wait message (would it be needed when using internet routing ?)
          self.doRoute(fromLat, fromLon, toLat, toLon)
          self.set('needRedraw', True) # show the new route

    elif(message == "p2posRoute"): # simple route, from here to selected point
      startPos = self.get('startPos', None)
      endPos = self.get('endPos', None)
      pos = self.get('pos', None)
      if pos == None: # well, we dont know where we are, so we dont know here to go :)
        return

      if startPos == None and endPos == None: # we know where we are, but we dont know where we should go :)
        return

      if startPos != None: # we want a route from somewhere to our current position
        fromPos = startPos
        toPos = pos

      if endPos != None: # we go from here to somewhere
        fromPos = pos
        toPos = endPos

      (toLat,toLon) = toPos
      (fromLat,fromLon) = fromPos

      print "Routing %f,%f to %f,%f" % (fromLat, fromLon, toLat, toLon)

      # TODO: wait message (would it be needed when using internet routing ?)
      self.doRoute(fromLat, fromLon, toLat, toLon)
      self.set('needRedraw', True) # show the new route

    elif(message == "route"): # simple route, from here to selected point
      # disable the point selection guis
      self.selectTwoPoints = False
      self.selectOnePoint = False
      toPos = self.get("selectedPos", None)
      if(toPos):
        toLat,toLon = [float(a) for a in toPos.split(",")]

        fromPos = self.get("pos", None)
        if(fromPos):
          (fromLat, fromLon) = fromPos
          print "Routing %f,%f to %f,%f" % (fromLat, fromLon, toLat, toLon)

          # TODO: wait message (would it be needed when using internet routing ?)
          self.doRoute(fromLat, fromLon, toLat, toLon)
          self.set('needRedraw', True) # show the new route

    elif(message == 'storeRoute'):
      loadTracklogs = self.m.get('loadTracklogs', None)
      if loadTracklogs == None:
        print "route: cant store route without the loadTracklog module"
        return
      if self.route == []:
        print "route: the route is empty, so it will not be stored"
        return

      loadTracklogs.storeRoute(self.route) # TODO: rewrite this when we support more routing providers

      length = len(loadTracklogs.tracklogs)
      self.set('activeTracklog', "%d" % (length-1)) # jump to the new tracklog


    elif(message == 'startInput'):
      entry = self.m.get('textEntry', None)
      if entry == None:
        return
      entryText = ""
      if self.startAddress:
        entryText = self.startAddress
      entry.entryBox(self ,'start','Input the start address',entryText)
#      self.expectTextEntry = 'start'

    elif(message == 'destinationInput'):
      entry = self.m.get('textEntry', None)
      if entry == None:
        return
      entryText = ""
      if self.destinationAddress:
        entryText = self.destinationAddress

      entry.entryBox(self,'destination','Input the start address',entryText)
#      self.expectTextEntry = 'destination'

    elif(message == 'addressRoute'):
      if self.startAddress and self.destinationAddress:
        print "address routing"
        self.doAddressRoute(self.startAddress,self.destinationAddress)
      else:
        print "cant route, start or destionation (or both) not set"

    elif(message == 'posToStart'):
      pos = self.get('pos', None)
      if pos:
        posString = "%f,%f" % pos
        self.startAddress = posString

    elif(message == 'posToDestination'):
      pos = self.get('pos', None)
      if pos:
        posString = "%f,%f" % pos
        self.destinationAddress = posString


      

  def doRoute(self, fromLat, fromLon, toLat, toLon):
    """Route from one point to another, and set that as the active route"""
    online = self.m.get('onlineServices', None)
    if online == None:
      return
    directions = online.googleDirectionsLL(fromLat, fromLon, toLat, toLon)
    if directions == None:
      return

    # remove any possible prev. route description, so new a new one for this route is created
    self.text = None 

    polyline = directions['Directions']['Polyline']['points'] # the route is encoded as a polyline
    route = self.decode_line(polyline) # we decode the polyline to a list of points

    self.route = route
    self.directions = directions
    # reverse geocode the start and destination coordinates (for the info menu)
    startAddress = online.googleReverseGeocode(fromLat,fromLon)
    destinationAddress = online.googleReverseGeocode(toLat,toLon)
    self.start = (fromLat, fromLon, startAddress)
    self.destination = (toLat, toLon, destinationAddress)

  def doAddressRoute(self, start, destination):
    """Route from one point to another, and set that as the active route"""
    online = self.m.get('onlineServices', None)
    if online == None:
      return
    print "routing from %s to %s" % (start,destination)
    directions = None
    try:
      directions = online.googleDirections(start, destination)
    except googlemaps.googlemaps.GoogleMapsError, e:
      if e.status == 602: # address/addresses not found
        print "address not found"
        self.sendMessage('notification:one or both of the adresses were not found#5')

    if directions == None:
      return

    # remove any possible prev. route description, so new a new one for this route is created
    self.text = None

    polyline = directions['Directions']['Polyline']['points'] # the route is encoded as a polyline
    route = self.decode_line(polyline) # we decode the polyline to a list of points

    self.route = route
    self.directions = directions

    (fromLat, fromLon) = route[0]
    (toLat, toLon) = route[-1]
    # reverse geocode the start and destination coordinates (for the info menu)
    startAddress = online.googleReverseGeocode(fromLat,fromLon)
    destinationAddress = online.googleReverseGeocode(toLat,toLon)
    self.start = (fromLat, fromLon, startAddress)
    self.destination = (toLat, toLon, destinationAddress)


  def firstTime(self):
    """Load stored addresses at startup.
      TODO: toggle for this, privacy reasons perhaps ?"""
    startAddress = self.get('startAddress', None)
    if startAddress:
      self.startAddress = startAddress
    destinationAddress = self.get('destinationAddress', None)
    if destinationAddress:
      self.destinationAddress = destinationAddress

  def sendMessage(self,message):
    m = self.m.get("messages", None)
    if(m != None):
      print "mapData: Sending message: " + message
      m.routeMessage(message)
    else:
      print "mapData: No message handler, cant send message."

  def update(self):
    self.set('num_updates', self.get('num_updates', 0) + 1)

    """register areas for manual point imput"""

    if self.expectStart:
      clickHandler = self.m.get('clickHandler', None)
      (x,y,w,h) = self.get('viewport')
      if clickHandler != None:
        clickHandler.registerXYWH(x, y, x+w, y+h, 'route:setStart')

    if self.expectEnd:
      clickHandler = self.m.get('clickHandler', None)
      (x,y,w,h) = self.get('viewport')
      if clickHandler != None:
        clickHandler.registerXYWH(x, y, x+w, y+h, 'route:setEnd')

  def drawMapOverlay(self, cr):
    """Draw a route"""
#    start1 = clock()
    # Where is the map?
    if self.selectTwoPoints == True:
      self.drawTwoPointsMenu(cr)

    if(not len(self.route)):
      return
    proj = self.m.get('projection', None)
    if(proj == None):
      return
    if(not proj.isValid()):
      return

    route = self.route

    # as you can see, for some reason, the cooridnates in direction steps are reversed, (lon,lat,0)
    steps = map(lambda x: (x['Point']['coordinates'][1],x['Point']['coordinates'][0]), self.directions['Directions']['Routes'][0]['Steps'])

    steps.append(route[-1])

    # now we convert geographic cooridnates to screen coordinates, so we dont need to do it twice
    steps = map(lambda x: (proj.ll2xy(x[0],x[1])), steps)

    # geo to screen at once
#    route = map(lambda x: (proj.ll2xy(x[0],x[1])), route)
    route = [proj.ll2xy(x[0],x[1]) for x in route]

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
    (x1,y1) = steps[-1]
    cr.move_to(x,y)
    cr.line_to(x1,y1)
    cr.stroke()

    cr.fill()

    # draw the step point background (under the polyline, it seems to look better this way)

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

    (x,y) = route[0]
    cr.move_to(x,y)

    # well, this SHOULD be faster and this is a performance critical section after all...
#    map(lambda x: cr.line_to(x[0],x[1]), route[1:]) # lambda drawing :)
    # according to numerous sources, list comprehensions should be faster than for loops and map+lambda
    # if its faster in this case too has not been determined
    [cr.line_to(x[0],x[1])for x in route[1:]] # list comprehension drawing :D
    cr.stroke()

    # draw the step points over then polyline
    cr.set_source_rgb(1, 1, 0)
    cr.set_line_width(7)
    for step in steps:
      (x,y) = (step)
      cr.arc(x, y, 2, 0, 2.0 * math.pi)
      cr.stroke()
    cr.fill()

#    print "Redraw took %1.9f ms" % (1000 * (clock() - start1))


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

  def drawTwoPointsMenu(self, cr):
    (x,y,w,h) = self.get('viewport')
    dx = min(w,h) / 5.0
    dy = dx
    menus = self.m.get('menu', None)
    x1 = (x+w)-dx
    y1 = (y-dy)+h

    startIcon = "generic_alpha"
    endIcon = "generic_alpha"
    if self.expectStart:
      startIcon = "generic_alpha_red"
    if self.expectEnd:
      endIcon = "generic_alpha_green"

    routingAction = 'route:p2pRoute'
    if self.selectOnePoint == True:
      routingAction = 'route:p2posRoute'

    menus.drawButton(cr, x1-dx, y1, dx, dy, 'start', startIcon, "route:expectStart")
    menus.drawButton(cr, x1, y1-dy, dx, dy, 'end', endIcon, "route:expectEnd")
    menus.drawButton(cr, x1, y1, dx, dy, 'route', "generic_alpha", routingAction)
    # "flush" cairo operations
    cr.stroke()
    cr.fill()

    # draw point selectors

    proj = self.m.get('projection', None)
    fromPos = self.get('startPos', None)
    toPos = self.get('endPos', None)
    if fromPos != None:
      print "drawing start point"
      cr.set_line_width(10)
      cr.set_source_rgb(1, 0, 0)
      (lat,lon) = fromPos

      (x, y) = proj.ll2xy(lat, lon)

      cr.arc(x, y, 3, 0, 2.0 * math.pi)
      cr.stroke()
      cr.fill()

      cr.set_line_width(8)
      cr.set_source_rgba(1, 0, 0, 0.95) # transparent red
      cr.arc(x, y, 15, 0, 2.0 * math.pi)
      cr.stroke()
      cr.fill()

    if toPos != None:
      print "drawing start point"
      cr.set_line_width(10)
      cr.set_source_rgb(0, 1, 0)
      (lat,lon) = toPos
      (x, y) = proj.ll2xy(lat, lon)
      cr.arc(x, y, 2, 0, 2.0 * math.pi)
      cr.stroke()
      cr.fill()

      cr.set_line_width(8)
      cr.set_source_rgba(0, 1, 0, 0.95) # transparent green
      cr.arc(x, y, 15, 0, 2.0 * math.pi)
      cr.stroke()
      cr.fill()

    if toPos != None:
      print "drawing end point"

#  def respondToText(self, entry, dialog, response):
#        print "responce"
#        print entry.get_text()
#        print "hiding now"
#        dialog.destroy()

  def handleTextEntryResult(self, key, result):
    if key == 'start':
      self.startAddress = result
      self.set('startAddress', result)
    elif key == 'destination':
      self.destinationAddress = result
      self.set('destinationAddress', result)

    self.set('needRedraw', True)


  def drawMenu(self, cr, menuName):
    if menuName == 'currentRoute':
      menus = self.m.get("menu",None)
      if menus == None:
        print "route: no menus module, no menus will be drawn"
        return

      parent = 'route'

      if self.route == []:
        action = "set:menu:None"
      else:
        (lat,lon) = self.route[0]
        action = "mapView:recentre %f %f|set:menu:None" % (lat, lon)

      button1 = ("map#show on", "generic", action)
      button2 = ("tools", "generic", "set:menu:currentRouteTools")

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

#      print self.get('textEntry', None)

      if self.once:
        self.once = False

#        entry = self.m.get('textEntry', None)
#        entry.entryBox("Enter destination")

      box = (text , "set:menu:currentRoute")
      menus.drawThreePlusOneMenu(cr, menuName, parent, button1, button2, box)

      menus.clearMenu('currentRouteTools', "set:menu:currentRoute")
      menus.addItem('currentRouteTools', 'tracklog#save as', 'generic', 'route:storeRoute|set:menu:tracklogInfo')

    if menuName == "showAdressRoute":
      
      menus = self.m.get("menu",None)
      if menus == None:
        print "route: no menus module, no menus will be drawn"
        return


#      print self.get('textEntry', "")
#      print self.get('textEntryDone', "")
#      print self.expectTextEntry
#      print self.startAddress
#      print self.destinationAddress


      (e1,e2,e3,e4,alloc) = menus.threePlusOneMenuCoords()
      (x1,y1) = e1
      (x2,y2) = e2
      (x3,y3) = e3
      (x4,y4) = e4
      (w1,h1,dx,dy) = alloc

      # * draw "escape" button
      menus.drawButton(cr, x1, y1, dx, dy, "", "up", "set:menu:main")
      # * route
      menus.drawButton(cr, x2, y2, dx, dy, "route", "generic", "route:addressRoute|set:menu:None")
      # * tools
#      menus.drawButton(cr, x3, y3, dx, dy, "tools", "generic", "set:menu:main")

      menus.clearMenu('currentRouteTools', "set:menu:currentRoute")
      
      menus.drawButton(cr, x4, y4, w1-x4, dy,  "start", "3h", "route:startInput")
      menus.drawButton(cr, x4, y4+2*dy, w1-x4, dy, "destination", "3h", "route:destinationInput")
      menus.drawButton(cr, x4, y4+dy, (w1-x4)/2, dy, "as start#position", "2h", "route:posToStart")
      menus.drawButton(cr, x4+(w1-x4)/2, y4+dy, (w1-x4)/2, dy, "as destination#position", "2h", "route:posToDestination")


      if self.startAddress == None:
        startText = "click to input starting adres"
      else:
        startText = self.startAddress
      if self.destinationAddress == None:
        destinationText = "click to input destination adres"
      else:
        destinationText = self.destinationAddress

      menus.showText(cr, startText, x4+w1/20, y4+dy/5, w1-x4-(w1/20)*2)
      menus.showText(cr, destinationText, x4+w1/20, y4+2*dy+dy/5, w1-x4-(w1/20)*2)


if(__name__ == '__main__'):
  d = {'transport':'car'}
  a = route({},d)
  a.doRoute(51.51565, 0.06036, 51.65299, -0.19974) # Beckton -> Barnet
  print a.route
  
  