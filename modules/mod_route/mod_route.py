#!/usr/bin/python
# -*- coding: utf-8 -*-
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
from modules.base_module import ranaModule

import os
import sys
import math
import re
import csv
import traceback
import unicodedata
import way
from time import clock
import time

DIRECTIONS_FILTER_CSV_PATH = 'data/directions_filter.csv'

ROUTING_SUCCESS = 0
ROUTING_NO_DATA = 1 # failed to load routing data
ROUTING_LOAD_FAILED = 2 # failed to load routing data
ROUTING_LOOKUP_FAILED = 3 # failed to locate nearest way/edge
ROUTING_ROUTE_FAILED = 4 # failed to compute route

def getModule(m,d,i):
  return(route(m,d,i))

class route(ranaModule):
  """Routes"""
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self._goToInitialState()
    self.routeRequestSentTimestamp = None
    self.once = True
    self.entry = None

    self.set('startPos', None)
    self.set('endPos', None)

    file = open(DIRECTIONS_FILTER_CSV_PATH, 'rb')
    CSVReader = csv.reader(file, delimiter=';', quotechar='|') #use an iterator
    self.directionsFilterRules = []
    for row in CSVReader:
      if row[0] != '#' and len(row) >= 2:
        regex = re.compile(unicode(row[0].decode("utf-8")))
        self.directionsFilterRules.append((regex, row[1].decode("utf-8")))
    file.close()

  def _goToInitialState(self):
    """restorer initial routing state
    -> used in init and when rerouting"""
    self.routeRequestSentTimestamp = None
    self.pxpyRoute = [] # route in screen coordinates
    self.directions = [] # directions object
    self.duration = None # in seconds
    self.start = None
    self.destination = None
    self.startAddress = None
    self.destinationAddress = None
    self.text = None
    self.selectTwoPoints = False
    self.selectOnePoint = False

    self.expectStart = False
    self.expectEnd = False

    self.routeDetailGeocodingTriggered = False

    # Monav
    self.monav = None
    self.monavDataFolder = None

  def handleMessage(self, message, type, args):
    if message == "clear":
      self._goToInitialState()
      self.set('startPos', None)
      self.set('endPos', None)

      # stop Turn-by-turn navigation, that can be possibly running
      self.sendMessage('turnByTurn:stop')

    elif message == 'expectStart':
      self.expectStart = True
      self.set('needRedraw', True) # we need to show the changed buttons

    elif message == 'setStart':
      if self.selectOnePoint:
        self.set('endPos', None)
      proj = self.m.get('projection', None)
      if proj and self.expectStart:
        lastClick = self.get('lastClickXY', None)
        (x, y) = lastClick
        """
        x and y must be floats, otherwise strange rounding errors occur, when converting to lat lon coordinates
        """
        (lat, lon) = proj.xy2ll(x, y)
        self.set('startPos', (lat,lon))
        self.start = (lat,lon)
        self.destination = None # clear destination

      self.expectStart = False
      self.set('needRedraw', True) # refresh the screen to show the new point

    elif message == 'expectEnd':
      self.expectEnd = True
      self.set('needRedraw', True) # we need to show the changed buttons

    elif message == 'setEnd':
      if self.selectOnePoint:
        self.set('startPos', None)
      proj = self.m.get('projection', None)
      if proj and self.expectEnd:
        lastClick = self.get('lastClickXY', None)
        (x, y) = lastClick
        """
        x and y must be floats, otherwise strange rounding errors occur, when converting to lat lon coordinates
        """
        (lat, lon) = proj.xy2ll(x, y)
        self.set('endPos', (lat,lon))
        self.destination = (lat,lon)
        self.start = None # clear start

      self.expectEnd = False
      self.set('needRedraw', True) # refresh the screen to show the new point

    elif message == "selectTwoPoints":
      self.set('startPos', None)
      self.set('endPos', None)
      self.selectOnePoint = False
      self.selectTwoPoints = True

    elif message == "selectOnePoint":
      self.set('startPos', None)
      self.set('endPos', None)
      self.selectTwoPoints = True # we reuse the p2p menu
      self.selectOnePoint = True

    elif message == "p2pRoute": # simple route, from here to selected point
      toPos = self.get("endPos", None)
      if toPos:
        toLat,toLon = toPos

        fromPos = self.get("startPos", None)
        if fromPos:
          fromLat,fromLon = fromPos

          print("Routing %f,%f to %f,%f" % (fromLat, fromLon, toLat, toLon))

          # TODO: wait message (would it be needed when using internet routing ?)
          self.doRoute(fromLat, fromLon, toLat, toLon)
          self.set('needRedraw', True) # show the new route

    elif message == "p2posRoute": # simple route, from here to selected point
      startPos = self.get('startPos', None)
      endPos = self.get('endPos', None)
      pos = self.get('pos', None)
      if pos is None: # well, we don't know where we are, so we don't know here to go :)
        return

      if startPos is None and endPos is None: # we know where we are, but we don't know where we should go :)
        return

      if startPos is not None: # we want a route from somewhere to our current position
        fromPos = startPos
        toPos = pos

      if endPos is not None: # we go from here to somewhere
        fromPos = pos
        toPos = endPos

      (toLat,toLon) = toPos
      (fromLat,fromLon) = fromPos

      print("Routing %f,%f to %f,%f" % (fromLat, fromLon, toLat, toLon))

      self.doRoute(fromLat, fromLon, toLat, toLon)
      self.set('needRedraw', True) # show the new route

    elif message == "route": # find a route
      if type == 'md': # message-list based routing
        if args:
          type = args['type']
          go = False
          if type == 'll2ll':
            (fromLat,fromLon) = (float(args['fromLat']),float(args['fromLon']))
            (toLat,toLon) = (float(args['toLat']),float(args['toLon']))
            go = True
          elif type == 'pos2ll':
            pos = self.get('pos', None)
            if pos:
              (fromLat,fromLon) = pos
              (toLat,toLon) = (float(args['toLat']),float(args['toLon']))
              go = True

          if go: # are we GO for routing ?
            print("Routing %f,%f to %f,%f" % (fromLat, fromLon, toLat, toLon))
            try:
              self.doRoute(fromLat, fromLon, toLat, toLon)
            except Exception, e:
              traceback.print_exc(file=sys.stdout)
              self.sendMessage('ml:notification:m:No route found;3')
              self.set('needRedraw', True)
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
        # disable the point selection GUIs
        self.selectTwoPoints = False
        self.selectOnePoint = False
        toPos = self.get("selectedPos", None)
        if toPos:
          toLat,toLon = [float(a) for a in toPos.split(",")]

          fromPos = self.get("pos", None)
          if fromPos:
            (fromLat, fromLon) = fromPos
            print("Routing %f,%f to %f,%f" % (fromLat, fromLon, toLat, toLon))

            # TODO: wait message (would it be needed when using internet routing ?)
            self.doRoute(fromLat, fromLon, toLat, toLon)
            self.set('needRedraw', True) # show the new route

    elif message == 'storeRoute':
      loadTracklogs = self.m.get('loadTracklogs', None)
      if loadTracklogs is None:
        print("route: cant store route without the loadTracklog module")
        return
      if not self.directions:
        print("route: the route is empty, so it will not be stored")
        return

      loadTracklogs.storeRouteAndSetActive(self.directions.getPointsLLE(), '', 'online') # TODO: rewrite this when we support more routing providers

    elif message == "clearRoute":
      self._goToInitialState()

    elif message == 'startInput':
      entry = self.m.get('textEntry', None)
      if entry is None:
        print("route: text entry module not available")
        return
      entryText = self.get('startAddress', "")
      entry.entryBox(self ,'start','Input the start address',entryText)

    elif message == 'destinationInput':
      entry = self.m.get('textEntry', None)
      if entry is None:
        print("route: text entry module not available")
        return
      entryText = self.get('destinationAddress', "")
      entry.entryBox(self,'destination','Input the destination address',entryText)

    elif message == 'addressRoute':
      startAddress = self.get('startAddress', None)
      destinationAddress = self.get('destinationAddress', None)
      if startAddress and destinationAddress:
        print("route: address routing")
        self.set('menu', None) # go to the map screen
        self.doAddressRoute(startAddress, destinationAddress)
      else: # notify the user about insufficient input and remain in the menu
        print("route: can't route, start or destination (or both) not set")
        if startAddress is None and destinationAddress is None:
          self.notify("Can't route: start & destination not set", 3000)
        elif startAddress is None:
          self.notify("Can't route: start not set", 3000)
        elif destinationAddress is None:
          self.notify("Can't route: destination not set", 3000)

    elif message == 'posToStart':
      pos = self.get('pos', None)
      if pos:
        posString = "%f,%f" % pos
        self.startAddress = posString # set as current address
        self.set('startAddress', posString) # also store in the persistent dictionary

    elif message == 'posToDestination':
      pos = self.get('pos', None)
      if pos:
        posString = "%f,%f" % pos
        self.destinationAddress = posString # set as current address
        self.set('destinationAddress', posString) # also store in the persistent dictionary

    elif message == 'reroute':
      if type == 'ms' and args == "fromPosToDest":
        """reroute from current position to destination"""
        # is there a destination and valid position ?
        print("route: rerouting from current position to last destination")
        pos = self.get('pos', None)
        if self.destination and pos:
          (pLat, pLon) = pos
          (dLat, dLon) = (self.destination[0], self.destination[1])
          self.doRoute(pLat, pLon, dLat, dLon)
          self.start = None

  def doRoute(self, fromLat, fromLon, toLat, toLon):
    """Route from one point to another, and set that as the active route"""
    # clear old addresses
    self.startAddress = None
    self.destinationAddress = None
    # the new result would probably have different start and destination coordinates
    self.routeDetailGeocodingTriggered = False

    #TODO: respect offline mode and automatically
    # use offline routing methods

    # TODO: notify user if no offline routing data is available for the current area

    provider = self.get('routingProvider', "GoogleDirections")
    if provider == "Monav":
      sentTimestamp = time.time()
      print('routing: using Monav as routing provider')
      waypoints = [(fromLat, fromLon), (toLat, toLon)]
      result = self.getMonavRoute(waypoints)
      #TODO: asynchronous processing & error notifications
      # as monav is VERY fast for routing, the routing might still get done
      # asynchronously, but the work-in-progress overlay might show up
      # only once the search takes longer than say 2 seconds
      self._handleResults("MonavRoute", (result, waypoints[0], waypoints[-1], sentTimestamp) )

    else: # use Google Directions as fallback
      online = self.m.get('onlineServices', None)
      if online:
        online.googleDirectionsLLAsync((fromLat, fromLon), (toLat, toLon), self._handleResults, "onlineRoute")

  def getMonavRoute(self, waypoints):
    mainMonavFolder = self.modrana.paths.getMonavDataPath()
    mode = self.get('mode', 'car')
    # get mode based sub-folder
    # TODO: handle not all mode folders being available
    # (eq. user only downloading routing data for cars)
    modeFolders = {
      'cycle':'routing_bike',
      'walk':'routing_pedestrian',
      'car':'routing_car'
    }
    subFolder = modeFolders.get(mode, 'routing_car')

    try:
      # list all directories in the Monav data folder
      dataPacks = os.listdir(mainMonavFolder)
      dataPacks = filter(lambda x: os.path.isdir(os.path.join(mainMonavFolder, x)), dataPacks )
    except Exception, e:
      print("route: can't list Monav data directory")
      print(e)
      dataPacks = []


    if dataPacks:
      # TODO: bounding box based pack selection

      preferredPack = self.get('preferredMonavDataPack', None)
      if preferredPack in dataPacks:
        packName = preferredPack
      else:
        # just take the first (and possibly only) pack
        packName = sorted(dataPacks)[0]

      monavDataFolder = os.path.abspath(os.path.join(mainMonavFolder, packName, subFolder))
      print('Monav data folder:\n%s' % monavDataFolder)
      print(os.path.exists(monavDataFolder))
      try:
        # is Monav initialized ?
        if self.monav is None:
          # start Monav

          # only import Monav & company when actually needed
          # -> the protobuf modules are quite large
          import monav_support
          self.monav = monav_support.Monav(self.modrana.paths.getMonavServerBinaryPath())
          self.monav.startServer()
        result = self.monav.monavDirections(monavDataFolder, waypoints)


      except Exception, e:
        print('route: Monav route lookup failed')
        print(e)
        traceback.print_exc(file=sys.stdout) # find what went wrong
        return None, None

      if result.type == result.SUCCESS:
        return result, ROUTING_SUCCESS
      elif result.type == result.LOAD_FAILED:
        return result, ROUTING_LOAD_FAILED
      elif result.type == result.LOOKUP_FAILED:
        return result, ROUTING_LOOKUP_FAILED
      elif result.type == result.ROUTE_FAILED:
        return result, ROUTING_ROUTE_FAILED
      else:
        return result, None

    else:
      print("route: no Monav routing data - can't route")
      return None, ROUTING_NO_DATA

  def doAddressRoute(self, start, destination):
    """Route from one point to another, and set that as the active route"""
    # cleanup any possible previous routes
    self._goToInitialState()
    online = self.m.get('onlineServices', None)
    if online:
      print("route: routing from %s to %s" % (start,destination))
      online.googleDirectionsAsync(start, destination, self._handleResults, "onlineRouteAddress2Address")

  def _handleResults(self, key, resultsTuple):
    """handle a routing result"""
    if key in ("onlineRoute", "onlineRouteAddress2Address"):
      if key == "onlineRoute":
        (directions, start, destination, routeRequestSentTimestamp) = resultsTuple
        # remove any possible prev. route description, so new a new one for this route is created
        self.text = None

        # TODO: support other providers than Google & offline routing

        if directions: # is there actually something in the directions ?
          # create the directions Way object
          self.duration = directions['Directions']['Duration']['html']
          dirs = way.fromGoogleDirectionsResult(directions)
          #TODO: use seconds from Way object directly
          #(needs seconds to human representation conversion)
          #self.duration = dirs.getDuration()
          self.processAndSaveResults(dirs, start, destination, routeRequestSentTimestamp)
      elif key == "onlineRouteAddress2Address":
        (directions, start, destination, routeRequestSentTimestamp) = resultsTuple
        # remove any possible prev. route description, so new a new one for this route is created
        self.text = None
        if directions: # is there actually something in the directions ?
          self.duration = directions['Directions']['Duration']['html']
          #TODO: use seconds from Way object directly
          #(needs seconds to human representation conversion)
          #self.duration = dirs.getDuration()

          # create the directions Way object
          dirs = way.fromGoogleDirectionsResult(directions)
          self.processAndSaveResults(dirs, start, destination, routeRequestSentTimestamp)
      # handle navigation autostart
      autostart = self.get('autostartNavigationDefaultOnAutoselectTurn', 'enabled')
      if autostart == 'enabled':
        self.sendMessage('ms:turnByTurn:start:%s' % autostart)
      self.set('needRedraw', True)
    elif key == "MonavRoute":
      (result, start, destination, routeRequestSentTimestamp) = resultsTuple
      directions, returnCode = result

      if returnCode == ROUTING_SUCCESS:
        self.duration = "" # TODO : correct predicted route duration
        dirs = way.fromMonavResult(directions)
        self.processAndSaveResults(dirs, start, destination, routeRequestSentTimestamp)
      else: # routing failed
        # show what & why failed
        if returnCode == ROUTING_LOOKUP_FAILED:
          self.notify('no ways near start or destination', 3000)
        elif returnCode == ROUTING_NO_DATA:
          self.notify('no routing data available', 3000)
        elif returnCode == ROUTING_LOAD_FAILED:
          self.notify('failed to load routing data', 3000)
        elif returnCode == ROUTING_ROUTE_FAILED:
          self.notify('failed to compute route', 3000)
        else:
          self.notify('offline routing failed', 5000)
    elif key == "startAddress":
      self.startAddress = resultsTuple
      self.text = None # clear route detail cache
    elif key == "destinationAddress":
      self.destinationAddress = resultsTuple
      self.text = None # clear route detail cache

  def processAndSaveResults(self, directions, start, destination, routeRequestSentTimestamp):
    """process and save routing results"""
    self.routeRequestSentTimestamp = routeRequestSentTimestamp
    proj = self.m.get('projection', None)
    if proj:
      self.pxpyRoute = [proj.ll2pxpyRel(x[0],x[1]) for x in directions.getPointsLLE()]
    self.processAndSaveDirections(directions)

    (fromLat, fromLon) = directions.getPointByID(0).getLL()
    (toLat, toLon) = directions.getPointByID(-1).getLL()

    """use coordinates for start dest or use first/last point from the route
       if start/dest coordinates are unknown (None)"""
    if self.start is None:
      self.start = (fromLat, fromLon)
    if self.destination is None:
      self.destination = (toLat, toLon)

  def processAndSaveDirections(self, directions):
    """process and save directions"""

    # apply filters
    directions = self.filterDirections(directions)

    # add a fake destination step, so there is a "destination reached" message
    if directions.getPointCount() > 0:
      (lat, lon) = directions.getPointByID(-1).getLL()
      destStep = way.TurnByTurnPoint(lat, lon)
      destStep.setSSMLMessage('<p xml:lang="en">you <b>should</b> be near the destination</p>')
      destStep.setMessage('you <b>should</b> be near the destination')
      destStep.setDistanceFromStart(directions.getLength())
      # TODO: make this multilingual
      # add it to the end of the message point list
      directions.addMessagePoint(destStep)

    # save
    self.directions = directions

  def filterDirections(self, directions):
    """
    filter directions according to substitution rules (specified by a CSV file)
    -> mostly used to replace abbreviations by full words in espeak output
    -> also assure Pango compatibility (eq. get rid of  <div> and company)
    """
    steps = directions.getMessagePoints()

    for step in steps:
      originalMessage = "".join(step.getMessage())
      message = step.getMessage() #TODO: make a method for this
      message = re.sub(r'<div[^>]*?>', '\n<i>', message)
      message = re.sub(r'</div[^>]*?>', '</i>', message)
      message = re.sub(r'<wbr/>', ', ', message)
      message = re.sub(r'<wbr>', ', ', message)
      step.setMessage(message)
      # special processing of the original message for Espeak
      message = originalMessage

      # check if cyrillic -> russian voice is enabled
      cyrillicVoice = self.get('voiceNavigationCyrillicVoice', 'ru')
      if cyrillicVoice:
        message = self.processCyrillicString(message, cyrillicVoice)

      message = re.sub(r'<div[^>]*?>', '<br>', message)
      message = re.sub(r'</div[^>]*?>', '', message)
      message = re.sub(r'<b>', '<emphasis level="strong">', message)
      message = re.sub(r'</b>', '</emphasis>', message)

      # apply external rules from a CSV file
      for (regex, replacement) in self.directionsFilterRules:
        # replace strings according to the csv file
        message = regex.sub(replacement, message, re.UNICODE)
      step.setSSMLMessage(message)

    # replace old message points with new ones
    directions.clearMessagePoints()
    directions.addMessagePoints(steps)

    return directions

  def processCyrillicString(self,inputString, voiceCode):
    """test if a given string contains any words with cyrillic characters
    if it does, tell espeak (by adding a sgml tag) to speak such words
    using voiceCode"""
    substrings = inputString.split(' ')
    outputString = ""
    cyrillicStringTemp = ""
    for substring in substrings: # split the message to words
      cyrillicCharFound = False
      # test if the word has any cyrillic characters (a single one is enough)
      for character in substring:
        try: # there are probably some characters that dont have a known name
          unicodeName = unicodedata.name(unicode(character))
          if unicodeName.find('CYRILLIC') != -1:
            cyrillicCharFound = True
            break
        except Exception, e:
          """just skip this as the character is  most probably unknown"""
          pass
      if cyrillicCharFound: # the substring contains at least one cyrillic character
        if cyrillicStringTemp: # append to the already "open" cyrillic string
          cyrillicStringTemp += ' ' + substring
        else: # create a new cyrillic string
          """make espeak say this word in russian (or other voiceCode),
          based on Cyrillic being detected in it"""
          cyrillicStringTemp = '<p xml:lang="%s">%s' % (voiceCode, substring)

      else: # no cyrillic found in this substring
        if cyrillicStringTemp: # is there an "open" cyrillic string ?
          cyrillicStringTemp += '</p>'# close the string
          # store it and the current substring
          outputString += ' ' + cyrillicStringTemp + ' ' + substring
          cyrillicStringTemp = ""
        else: # no cyrillic string in progress
          # just store the current substring
          outputString = outputString + ' ' + substring
    # cleanup
    if cyrillicStringTemp: #is there an "open" cyrillic string ?
      cyrillicStringTemp += '</p>' # close the string
      outputString += ' ' + cyrillicStringTemp
      cyrillicStringTemp = ""
    return outputString

  def drawScreenOverlay(self, cr):
    menus = self.m.get('menu', None)
    if menus:
      if not menus.buttonsHidingOn(): # check if the buttons should not be hidden
        if self.directions: # current route info button
          self.drawCurrentRouteInfoButton(cr)

        if self.selectTwoPoints: # point selection menu
          self.drawTwoPointsMenu(cr)

    #register clickable areas for manual point input
    if self.expectStart:
      clickHandler = self.m.get('clickHandler', None)
      (x,y,w,h) = self.get('viewport')
      if clickHandler is not None:
        clickHandler.registerXYWH(x, y, x+w, y+h, 'route:setStart')
    if self.expectEnd:
      clickHandler = self.m.get('clickHandler', None)
      (x,y,w,h) = self.get('viewport')
      if clickHandler is not None:
        clickHandler.registerXYWH(x, y, x+w, y+h, 'route:setEnd')

  def drawMapOverlay(self, cr):
    """Draw a route"""
#    start1 = clock()

    if self.directions:
      # Where is the map?
      proj = self.m.get('projection', None)
      if proj is None:
        return
      if not proj.isValid():
        return

      # get LLE tuples for message points
      steps = self.directions.getMessagePointsLLE()

      # now we convert geographic coordinates to screen coordinates, so we dont need to do it twice
      steps = map(lambda x: (proj.ll2xy(x[0],x[1])), steps)

      if self.start:
        start = proj.ll2xy(self.start[0], self.start[1])
        # line from starting point to start of the route
        (x,y) = start
        (px1,py1) = self.pxpyRoute[0]
        (x1,y1) = proj.pxpyRel2xy(px1, py1)
        cr.set_source_rgba(0, 0, 0.5, 0.45)
        cr.set_line_width(10)
        cr.move_to(x,y)
        cr.line_to(x1,y1)
        cr.stroke()

      if self.destination:
        destination = proj.ll2xy(self.destination[0], self.destination[1])
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
        (x,y) = step
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

      # these setting seem to work the best for routing results:
      # (they have a different structure than logging traces,
      # eq. long segments delimited by only two points, etc)
      # basically, routing results have only the really needed points -> less points than traces
      if 16 > z > 10:
        modulo = 2**(14-z)
      elif z <= 10:
        modulo = 16
      else:
        modulo = 1

  #    maxDraw = 300
  #    drawCount = 0
      counter=0

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

  #    print(drawCount)
  #    print(modulo)

      # make sure the last point is connected
      (px,py) = self.pxpyRoute[-1]
      (x,y) = proj.pxpyRel2xy(px, py)
      cr.line_to(x,y)

      cr.stroke()

      # draw the step points over the polyline
      cr.set_source_rgb(1, 1, 0)
      cr.set_line_width(7)
      for step in steps:
        (x,y) = step
        cr.arc(x, y, 2, 0, 2.0 * math.pi)
        cr.stroke()
      cr.fill()
    # draw the the start/dest indicators over the route
    if self.selectTwoPoints:
      self.drawPointSelectors(cr)

#    print("Redraw took %1.9f ms" % (1000 * (clock() - start1)))

  def getCurrentDirections(self):
    # return the current route
    return self.directions, self.routeRequestSentTimestamp

  def drawCurrentRouteInfoButton(self,cr):
    (x,y,w,h) = self.get('viewport')
    menus = self.m.get('menu', None)
    dx = min(w,h) / 5.0
    dy = dx
    x1 = (x+w)-dx
    y1 = (y-dy)+h
    if self.selectTwoPoints:
      """move to avoid collision with the point selection menu"""
      x1 -= dx
      y1 -= dy
    menus.drawButton(cr, x1, y1, dx, dy, 'info#route', "generic:;0.5;;0.5;;", 'set:menu:route#currentRouteBackToMap')

  def drawTwoPointsMenu(self, cr):
    (x,y,w,h) = self.get('viewport')
    dx = min(w,h) / 5.0
    dy = dx
    menus = self.m.get('menu', None)
    x1 = (x+w)-dx
    y1 = (y-dy)+h

    startIcon = "generic:;0.5;;0.5;;"
    endIcon = "generic:;0.5;;0.5;;"
    if self.expectStart:
      startIcon = "generic:red;0.5;red;0.5;;"
    if self.expectEnd:
      endIcon = "generic:green;0.5;green;0.5;;"

    routingAction = 'route:p2pRoute'
    if self.selectOnePoint:
      routingAction = 'route:p2posRoute'

    menus.drawButton(cr, x1-dx, y1, dx, dy, 'start', startIcon, "route:expectStart")
    menus.drawButton(cr, x1, y1-dy, dx, dy, 'end', endIcon, "route:expectEnd")
    menus.drawButton(cr, x1, y1, dx, dy, 'route', "generic:;0.5;;0.5;;", routingAction)

    # "flush" cairo operations
    cr.stroke()
    cr.fill()

  def drawPointSelectors(self,cr):
    # draw point selectors
    proj = self.m.get('projection', None)
    fromPos = self.get('startPos', None)
    toPos = self.get('endPos', None)
    if fromPos is not None:
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

    if toPos is not None:
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

  def handleTextEntryResult(self, key, result):
    if key == 'start':
      self.startAddress = result
      self.set('startAddress', result)
    elif key == 'destination':
      self.destinationAddress = result
      self.set('destinationAddress', result)
    self.set('needRedraw', True)

  def drawMenu(self, cr, menuName, args=None):
    if menuName == 'currentRoute' or menuName == 'currentRouteBackToMap':
      menus = self.m.get("menu",None)
      if menus is None:
        print("route: no menu module, no menus will be drawn")
        return

      # if called from the osd menu, go back to map at escape
      if menuName == 'currentRouteBackToMap':
        parent = 'set:menu:None'
      else:
        parent = 'set:menu:route'

      if self.directions:
        (lat,lon) = self.directions.getPointByID(0).getLL()
        action = "mapView:recentre %f %f|set:menu:None" % (lat, lon)

      else:
        action = "set:menu:None"

      button1 = ("map#show on", "generic", action)
      button2 = ("tools", "tools", "set:menu:currentRouteTools")

      if not self.directions:
        text = "There is currently no active route."
      elif self.text is None: # the new text for the info-box only once
        # check if start and destination geocoding is needed
        if not self.routeDetailGeocodingTriggered:
          self._geocodeStartAndDestination()
          self.routeDetailGeocodingTriggered = True

        if self.duration:
          duration = self.duration # a string describing the estimated time to finish the route
        else:
          duration = "unknown"
        units = self.m.get('units', None) # get the correct units
        distance = units.m2CurrentUnitString(self.directions.getLength())
        steps = self.directions.getMessagePointCount() # number of steps

        if self.startAddress:
          start = ""
          for item in self.startAddress.split(','):
            start += "%s\n" % item
        else:
          start = "start address unknown"

        if self.destinationAddress:
          destination = ""
          for item in self.destinationAddress.split(','):
            destination += "\n%s" % item
        else:
          destination = "\ndestination address unknown"

        text = "%s" % start
        text+= "%s" % destination
        text+= "\n\n%s in about %s and %s steps" % (distance, duration, steps)
        if self.start and self.destination:
          (lat1,lon1) = (self.start[0],self.start[1])
          (lat2,lon2) = (self.destination[0],self.destination[1])
          text+= "\n(%f,%f)->(%f,%f)" % (lat1,lon1,lat2,lon2)

        self.text = text
      else:
        text = self.text

      if self.once:
        self.once = False

      box = (text , "set:menu:route#currentRoute")
      menus.drawThreePlusOneMenu(cr, menuName, parent, button1, button2, box)
      menus.clearMenu('currentRouteTools', "set:menu:route#currentRoute")
      menus.addItem('currentRouteTools', 'tracklog#save as', 'generic', 'route:storeRoute|set:currentTracCat:online|set:menu:tracklogManager#tracklogInfo')

      # add turn-by-turn navigation buttons
      tbt = self.m.get('turnByTurn', None)
      if tbt:
        if tbt.enabled():
          menus.addItem('currentRouteTools', 'navigation#stop', 'generic', 'turnByTurn:stop|set:menu:None')
          menus.addItem('currentRouteTools', 'navigation#restart', 'generic', 'turnByTurn:stop|ms:turnByTurn:start:closest|set:menu:None')
          self.set('needRedraw', True) # refresh the screen to show the changed button
        else:
          menus.addItem('currentRouteTools', 'navigation#start', 'generic', 'ms:turnByTurn:start:enabled|set:menu:None')

      menus.addItem('currentRouteTools', 'clear', 'generic', 'route:clear|set:menu:None')

    if menuName == "showAddressRoute":
      menus = self.m.get("menu",None)
      if menus:
        (e1,e2,e3,e4,alloc) = menus.threePlusOneMenuCoords()
        (x1,y1) = e1
        (x2,y2) = e2
        (x3,y3) = e3
        (x4,y4) = e4
        (w1,h1,dx,dy) = alloc

        # * draw "escape" button
        menus.drawButton(cr, x1, y1, dx, dy, "", "back", "set:menu:main")
        # * route
        menus.drawButton(cr, x2, y2, dx, dy, "route", "generic", "route:addressRoute")

        menus.clearMenu('currentRouteTools', "set:menu:route#currentRoute")

        menus.drawButton(cr, x4, y4, w1-x4, dy,  "start", "generic", "route:startInput")
        menus.drawButton(cr, x4, y4+2*dy, w1-x4, dy, "destination", "generic", "route:destinationInput")
        menus.drawButton(cr, x4, y4+dy, (w1-x4)/2, dy, "as start#position", "generic", "route:posToStart|set:needRedraw:True")
        menus.drawButton(cr, x4+(w1-x4)/2, y4+dy, (w1-x4)/2, dy, "as destination#position", "generic", "route:posToDestination|set:needRedraw:True")

        # try to get last used addresses
        startText = self.get('startAddress', None)
        destinationText = self.get('destinationAddress', None)

        # if there are no last used addresses, use defaults
        if startText is None:
          startText = "click to input starting address"

        if destinationText is None:
          destinationText = "click to input destination address"

        menus.showText(cr, startText, x4+w1/20, y4+dy/5, w1-x4-(w1/20)*2)
        menus.showText(cr, destinationText, x4+w1/20, y4+2*dy+dy/5, w1-x4-(w1/20)*2)

  def _geocodeStartAndDestination(self):
    """get the address of start and destination coordinates by using geocoding"""
    online = self.m.get('onlineServices', None)
    if online:
      # start coordinates
      if self.start:
        (sLat, sLon) = self.start
      else:
        (sLat, sLon) = self.directions.getPointByID(0).getLL()
      # geocode start
      online.reverseGeocodeAsync(sLat, sLon, self._handleResults, "startAddress", "Geocoding start")

      # destination coordinates
      if self.destination:
        (dLat, dLon) = self.destination
      else:
        (dLat, dLon) = self.directions.getPointByID(-1).getLL()
      online.reverseGeocodeAsync(dLat, dLon, self._handleResults, "destinationAddress", "Geocoding destination")

  def shutdown(self):
    # stop the Monav server, if running
    if self.monav:
      self.monav.stopServer()

if(__name__ == '__main__'):
  d = {'transport':'car'}
  a = route({},d)
  a.doRoute(51.51565, 0.06036, 51.65299, -0.19974) # Beckton -> Barnet
  print(a.route)
  
  
