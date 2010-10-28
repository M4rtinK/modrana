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
import re
import csv
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
    self.route = [] # maybe remove this ?
    self.pxpyRoute = []
    self.directions = []
    self.start = None
    self.destination = None
    self.text = None
    self.selectTwoPoints = False
    self.selectOnePoint = False
    self.once = True
    self.entry = None
    self.directionsFilterCSV = 'data/directions_filter.csv'

    self.expectStart = False
    self.expectEnd = False

    self.startAddress = None
    self.destinationAddress = None

    self.set('startPos', None)
    self.set('endPos', None)

  def handleMessage(self, message, type, args):
    if (message == "clear"):
      self.route = []
      self.pxpyRoute = []
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

      # stop Turn-by-turn navigation, that can be possibly running
      self.sendMessage('turnByTurn:stop')

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

    elif(message == "route"): # find a route
      if (type=='md'): # mesage-list based routing
        if args:
          type = args['type']
          go = False
          if type=='ll2ll':
            (fromLat,fromLon) = (float(args['fromLat']),float(args['fromLon']))
            (toLat,toLon) = (float(args['toLat']),float(args['toLon']))
            go = True
          elif type=='pos2ll':
            pos = self.get('pos', None)
            if pos:
              (fromLat,fromLon) = pos
              (toLat,toLon) = (float(args['toLat']),float(args['toLon']))
              go = True
          if go: # are ve GO for routing ?
            print "Routing %f,%f to %f,%f" % (fromLat, fromLon, toLat, toLon)
            try:
              self.doRoute(fromLat, fromLon, toLat, toLon)
            except:
              self.sendMessage('ml:notification:m:No route found;3')
            if "show" in args:
              """switch to map view and go to start/destination, if requested"""
              where = args['show']
              if where == 'start':
                (cLat, cLon) = (fromLat,fromLon)
              elif where == "destination":
                (cLat, cLon) = (toLat,toLon)
              self.sendMessage('mapView:recentre %f %f|set:menu:None' % (cLat,cLon))

            self.set('needRedraw', True) # show the new route
      else: # simple route, from here to selected point
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

      loadTracklogs.storeRouteAndSetActive(self.route, '', 'online') # TODO: rewrite this when we support more routing providers


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

      entry.entryBox(self,'destination','Input the destination address',entryText)
#      self.expectTextEntry = 'destination'

    elif(message == 'addressRoute'):
      if self.startAddress and self.destinationAddress:
#        # remove possible markers from p2p routing
#        if self.start:
#          self.start = None
#        if self.destination:
#          self.destination = None
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

    elif(message == 'reroute'):
      if type == 'ms' and args == "fromPosToDest":
        """reroute from current position to destination"""
        # is there a destination and valid position ?
        print "rerouting from current position to last destination"
        pos = self.get('pos', None)
        if self.destination and pos:
          (pLat, pLon) = pos
          (dLat, dLon) = (self.destination[0], self.destination[1])
          self.doRoute(pLat, pLon, dLat, dLon)


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
    # handle the results
    start = (fromLat, fromLon)
    destination = (toLat, toLon)
    self.processAndSaveResults(route, directions, start, destination)

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
        self.sendMessage('notification:adress(es) not found#5')

    if directions == None:
      return

    # remove any possible prev. route description, so new a new one for this route is created
    self.text = None

    polyline = directions['Directions']['Polyline']['points'] # the route is encoded as a polyline
    route = self.decode_line(polyline) # we decode the polyline to a list of points
    # handle the results
    if len(route) >= 2:
      start = (route[0])
      print start
      destination = (route[-1])
      print destination
    self.processAndSaveResults(route, directions, start, destination)
    
  def processAndSaveResults(self, route, directions, start=None, destination=None):
    """process and save routing results"""
    self.route = route
    proj = self.m.get('projection', None)
    if proj:
      self.pxpyRoute = [proj.ll2pxpyRel(x[0],x[1]) for x in route]
    self.processAndSaveDirections(directions, 'gdirections')

    (fromLat, fromLon) = route[0]
    (toLat, toLon) = route[-1]
    # reverse geocode the start and destination coordinates (for the info menu)
    online = self.m.get('onlineServices', None)
    if online == None:
      return
    startAddress = online.googleReverseGeocode(fromLat,fromLon)
    destinationAddress = online.googleReverseGeocode(toLat,toLon)

    if start:
      (startLat, startLon) = start
      self.start = (startLat, startLon, startAddress)
    if destination:
      (destLat, destLon) = destination
      self.destination = (destLat, destLon, destinationAddress)
    
  def processAndSaveDirections(self, rawDirections, type):
    """process a raw route to a unified format"""
    if type == 'gdirections':
    # add a fake destination step, so there is a "destination reached" message
      destStep = {}
      destStep[u'descriptionHtml'] = 'you <b>should</b> be near the destination'
      (lat,lon) = self.route[-1]
      # NOTE: steps have reversed coordinates
      destStep[u'Point'] = {'coordinates':[lon,lat,0]}
      destStep[u'Distance'] = {u'meters' : 100}
      rawDirections['Directions']['Routes'][0]['Steps'].append(destStep) # add it to the end of the list

      # make the direction messages pango compatible
      filteredDirections = self.filterDirections(rawDirections)
      self.directions = filteredDirections

  def filterDirections(self, rawDirections):
    i = 0
    for step in rawDirections['Directions']['Routes'][0]['Steps']:
      message = step['descriptionHtml'] #TODO: make a method for this
      message = re.sub(r'<div[^>]*?>', '\n<i>', message)
      message = re.sub(r'</div[^>]*?>', '</i>', message)
      message = re.sub(r'<wbr/>', ', ', message)
      message = re.sub(r'<wbr>', ', ', message)
#        message = re.sub(r'<[^>]*?>', '<b>', message)
#        message = re.sub(r'</div[^>]*?>', '</i>', message)
      step['descriptionHtml'] = message
      # get a special version for espeak
      message = step['descriptionHtml']
      message = re.sub(r'<div[^>]*?>', '<br>', message)
      message = re.sub(r'</div[^>]*?>', '', message)
      message = re.sub(r'<b>', '<emphasis level="strong">', message)
      message = re.sub(r'</b>', '</emphasis>', message)
      step['descriptionEspeak'] = message
      step['visited'] = False
      step['id'] = i
      i = i + 1

    # apply external rules rom a CSV file
    rawDirections = self.applyRulesFromCSVFile(rawDirections)

    return rawDirections

  def applyRulesFromCSVFile(self,rawDirections):
      filename = self.directionsFilterCSV
      CSVreader = csv.reader(open(filename, 'rb'), delimiter=';', quotechar='|')

      for step in rawDirections['Directions']['Routes'][0]['Steps']:
        message = step['descriptionEspeak']
        for row in CSVreader:
          if len(row)>=2:
            # replace strings according to the csv file
            message = re.sub(row[0], row[1], message)
        step['descriptionEspeak'] = message
      return rawDirections


  def firstTime(self):
    """Load stored addresses at startup.
      TODO: toggle for this, privacy reasons perhaps ?"""
    startAddress = self.get('startAddress', None)
    if startAddress:
      self.startAddress = startAddress
    destinationAddress = self.get('destinationAddress', None)
    if destinationAddress:
      self.destinationAddress = destinationAddress

    """setup the first step selection menu"""
    menus = self.m.get('menu', None)
    if menus:
      menus.clearMenu('routeSelectFirstStep', "set:menu:currentRouteTools")
      menus.addItem('routeSelectFirstStep', 'step#first', 'generic', 'ms:turnByTurn:start:first|set:menu:None')
      menus.addItem('routeSelectFirstStep', 'step#closest', 'generic', 'ms:turnByTurn:start:closest|set:menu:None')

  def update(self):
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

  def drawScreenOverlay(self, cr):
    if self.route: # current route info button
      self.drawCurrentRouteInfoButton(cr)

    if self.selectTwoPoints == True: # poin selection menu
      self.drawTwoPointsMenu(cr)

  def drawMapOverlay(self, cr):
    """Draw a route"""
#    start1 = clock()

    if len(self.route):
      # Where is the map?
      proj = self.m.get('projection', None)
      if(proj == None):
        return
      if(not proj.isValid()):
        return

      # as you can see, for some reason, the cooridnates in direction steps are reversed, (lon,lat,0)
      steps = map(lambda x: (x['Point']['coordinates'][1],x['Point']['coordinates'][0]), self.directions['Directions']['Routes'][0]['Steps'])

      # draw the destination as a step point
      steps.append(self.route[-1])

      # now we convert geographic cooridnates to screen coordinates, so we dont need to do it twice
      steps = map(lambda x: (proj.ll2xy(x[0],x[1])), steps)


      start = proj.ll2xy(self.start[0], self.start[1])
      destination = proj.ll2xy(self.destination[0], self.destination[1])

      # line from starting point to start of the route
      (x,y) = start
      (px1,py1) = self.pxpyRoute[0]
      (x1,y1) = proj.pxpyRel2xy(px1, py1)
      cr.set_source_rgba(0, 0, 0.5, 0.45)
      cr.set_line_width(10)
      cr.move_to(x,y)
      cr.line_to(x1,y1)
      cr.stroke()

      # line from the destination point to end of the route
      (x,y) = destination
      (px1,py1) = self.pxpyRoute[-1]
      (x1,y1) = proj.pxpyRel2xy(px1, py1)
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

      (px,py) = self.pxpyRoute[0]
      (x,y) = proj.pxpyRel2xy(px, py)
      cr.move_to(x,y)

      # well, this SHOULD be faster and this is a performance critical section after all...
  #    map(lambda x: cr.line_to(x[0],x[1]), route[1:]) # lambda drawing :)
      # according to numerous sources, list comprehensions should be faster than for loops and map+lambda
      # if its faster in this case too has not been determined


      """
      routing result drawing algorithm
      adapted from TangoGPS source (tracks.c)
      works surprisingly good :)
      """

      z = proj.zoom


      # these setting seem to werk the best for routing results:
      # (they have a different structure than loging traces,
      # eq. long segments delimited by only two points, etc)
      # basicly, routing results heva only the really nedded points -> less points than traces
      if z < 16 and z > 10:
        modulo = 2**(14-z)
      elif (z <= 10):
        modulo = 16
      else:
        modulo = 1

  #    maxDraw = 300
  #    drawCount = 0
      counter=0
  #
  #
      for point in self.pxpyRoute[1:]: #draw the track
        counter+=1
        if counter%modulo==0:
  #      if 1:
  #        drawCount+=1
  #        if drawCount>maxDraw:
  #          break
          (px,py) = point
          (x,y) = proj.pxpyRel2xy(px, py)
          cr.line_to(x,y)

      # make a line to the last point (the modulo method sometimes skips the end of the track)
  #    [cr.line_to(x[0],x[1])for x in route[1:]] # list comprehension drawing :D

  #    print drawCount
  #    print modulo

      # make sure the last point is connected
      (px,py) = self.pxpyRoute[-1]
      (x,y) = proj.pxpyRel2xy(px, py)
      cr.line_to(x,y)

      cr.stroke()

      # draw the step points over the polyline
      cr.set_source_rgb(1, 1, 0)
      cr.set_line_width(7)
      for step in steps:
        (x,y) = (step)
        cr.arc(x, y, 2, 0, 2.0 * math.pi)
        cr.stroke()
      cr.fill()
    # draw the the start/dest indicators over the route
    if self.selectTwoPoints:
      self.drawPointSelectors(cr)

#    print "Redraw took %1.9f ms" % (1000 * (clock() - start1))


  def getCurrentRoute(self):
    # return the current route
    return self.route

  def getCurrentDirections(self):
    # return the current route
    return self.directions

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

  def drawCurrentRouteInfoButton(self,cr):
    (x,y,w,h) = self.get('viewport')
    menus = self.m.get('menu', None)
    dx = min(w,h) / 5.0
    dy = dx
    x1 = (x+w)-dx
    y1 = (y-dy)+h
    if self.selectTwoPoints:
      """move to avoid colision with the point selection menu"""
      x1 = x1-dx
      y1 = y1-dy
    menus.drawButton(cr, x1, y1, dx, dy, 'info#route', "generic_alpha", 'set:menu:currentRouteBackToMap')
    

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

  def drawPointSelectors(self,cr):
    # draw point selectors

    proj = self.m.get('projection', None)
    fromPos = self.get('startPos', None)
    toPos = self.get('endPos', None)
    if fromPos != None:
#      print "drawing start point"
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
#      print "drawing start point"
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

#    if toPos != None:
#      print "drawing end point"

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
    if menuName == 'currentRoute' or menuName == 'currentRouteBackToMap':
      menus = self.m.get("menu",None)
      if menus == None:
        print "route: no menus module, no menus will be drawn"
        return

      # if called from the osd menu, go back to map at escape
      if menuName == 'currentRouteBackToMap':
        parent = 'set:menu:None'
      else:
        parent = 'set:menu:route'

      if self.route == []:
        action = "set:menu:None"
      else:
        (lat,lon) = self.route[0]
        action = "mapView:recentre %f %f|set:menu:None" % (lat, lon)

      button1 = ("map#show on", "generic", action)
      button2 = ("tools", "tools", "set:menu:currentRouteTools")

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
          start += "\n%s" % item
    #    start += "\n(%f,%f)" % (lat1,lon1)

        destination = ""
        destinationAddress = self.destination[2]
        (lat2,lon2) = (self.destination[0],self.destination[1])
        for item in destinationAddress.split(','):
          destination += "\n%s" % item
    #    destination += "\n(%f,%f)" % (lat2,lon2)

        text = "%s" % start
        text+= "\n%s" % destination
        text+= "\n\n%s in about %s and %s steps" % (distance, duration, steps)
        text+= "\n(%f,%f)->(%f,%f)" % (lat1,lon1,lat2,lon2)

        self.text = text
      else:
        text = self.text

#      print self.get('textEntry', None)

      if self.once:
        self.once = False

      box = (text , "set:menu:currentRoute")
      menus.drawThreePlusOneMenu(cr, menuName, parent, button1, button2, box)
      menus.clearMenu('currentRouteTools', "set:menu:currentRoute")
      menus.addItem('currentRouteTools', 'tracklog#save as', 'generic', 'route:storeRoute|set:currentTracCat:online|set:menu:tracklogInfo')

      # add turn-by-turn navigation buttons
      tbt = self.m.get('turnByTurn', None)
      if tbt:
        if tbt.enabled():
          menus.addItem('currentRouteTools', 'navigation#stop', 'generic', 'turnByTurn:stop|set:menu:None')
          menus.addItem('currentRouteTools', 'navigation#restart', 'generic', 'turnByTurn:stop|set:menu:routeSelectFirstStep')
          self.set('needRedraw', True) # refresh the screen to show the changed button
        else:
          menus.addItem('currentRouteTools', 'navigation#start', 'generic', 'set:menu:routeSelectFirstStep')

      menus.addItem('currentRouteTools', 'clear', 'generic', 'route:clear|set:menu:None')



    if menuName == "showAdressRoute":
      
      menus = self.m.get("menu",None)
      if menus == None:
        print "route: no menus module, no menus will be drawn"
        return


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
      
      menus.drawButton(cr, x4, y4, w1-x4, dy,  "start", "generic", "route:startInput")
      menus.drawButton(cr, x4, y4+2*dy, w1-x4, dy, "destination", "generic", "route:destinationInput")
      menus.drawButton(cr, x4, y4+dy, (w1-x4)/2, dy, "as start#position", "generic", "route:posToStart|set:needRedraw:True")
      menus.drawButton(cr, x4+(w1-x4)/2, y4+dy, (w1-x4)/2, dy, "as destination#position", "generic", "route:posToDestination|set:needRedraw:True")


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
  
  