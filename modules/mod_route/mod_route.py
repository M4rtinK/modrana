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
from modules.base_module import RanaModule

import os
import sys
import math
import re
import csv
import traceback
import unicodedata
import core.way as way
import core.geo as geo
from core.backports.six import u
#from time import clock
import time

DIRECTIONS_FILTER_CSV_PATH = 'data/directions_filter.csv'

# routing error codes
ROUTING_SUCCESS = 0
ROUTING_NO_DATA = 1 # failed to load routing data
ROUTING_LOAD_FAILED = 2 # failed to load routing data
ROUTING_LOOKUP_FAILED = 3 # failed to locate nearest way/edge
ROUTING_ROUTE_FAILED = 4 # failed to compute route

# OSD menu states
OSD_EDIT = 1 # route editing buttons
OSD_CURRENT_ROUTE = 2 # a single button that triggers the options menu
OSD_ROUTE_OPTIONS = 3 # buttons that go to the edit or info menus


def getModule(m, d, i):
    return Route(m, d, i)


class Route(RanaModule):
    """Routes"""

    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)
        self._goToInitialState()
        self.routeRequestSentTimestamp = None
        self.once = True
        self.entry = None

        # tracks the state of the onscreen routing menu
        self.osdMenuState = None

        self.set('startPos', None)
        self.set('endPos', None)

        self._directionsFilterRules = []
        self._directionsFilterRulesLoaded = False

        # Monav
        self.monav = None
        self.monavDataFolder = None

    def _goToInitialState(self):
        """restorer initial routing state
        -> used in init and when rerouting"""
        self.routeRequestSentTimestamp = None
        self.pxpyRoute = [] # route in screen coordinates
        self.directions = [] # directions object
        self.set('midText', [])
        self.durationString = None # in seconds
        self.start = None
        self.destination = None
        self.startAddress = None
        self.destinationAddress = None
        self.text = None
        self.selectManyPoints = False
        # disable OSD menu
        self.osdMenuState = None
        # discern between normal routing with waypoints
        # and handmade routing
        self.handmade = False
        self.selectTwoPoints = False
        self.selectOnePoint = False

        self.expectStart = False
        self.expectMiddle = False # handmade
        self.expectEnd = False

        self.routeDetailGeocodingTriggered = False

    @property
    def directionsFilterRules(self):
        if not self._directionsFilterRulesLoaded:
            self._loadDirectionsFilter()
            # why not just check if _directionsFilterRules
        # is nonempty ?
        # -> the file might be empty or its loading might fail,
        # so if we checked just the rules list in such a case,
        # we would needlessly open the file over and over again
        return self._directionsFilterRules

    def _loadDirectionsFilter(self):
        """Load direction filters from their CSV file"""
        start = time.time()
        f = open(DIRECTIONS_FILTER_CSV_PATH, 'r')
        CSVReader = csv.reader(f, delimiter=';', quotechar='|') #use an iterator
        self._directionsFilterRules = []
        for row in CSVReader:
            if row[0] != '#' and len(row) >= 2:
                regex = re.compile(u(row[0]))
                self._directionsFilterRules.append((regex, u(row[1])))
        f.close()
        self._directionsFilterRulesLoaded = True
        print("route: directions filter loaded in %1.2f ms" % ((time.time() - start) * 1000))

    def handleMessage(self, message, messageType, args):
        if message == "clear":
            self._goToInitialState()
            self.set('startPos', None)
            self.set('endPos', None)
            self.set('middlePos', []) # handmade

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
                # x and y must be floats, otherwise strange rounding errors
                # occur when converting to lat lon coordinates
                (lat, lon) = proj.xy2ll(x, y)
                self.set('startPos', (lat, lon))
                self.start = (lat, lon)
                self.destination = None # clear destination

            self.expectStart = False
            self.set('needRedraw', True) # refresh the screen to show the new point

        elif message == 'expectMiddle': # handmade
            self.expectMiddle = True # handmade
            self.set('needRedraw', True) # we need to show the changed buttons # handmade

        elif message == 'setMiddle': # handmade
            proj = self.m.get('projection', None)
            if proj and self.expectMiddle:
                lastClick = self.get('lastClickXY', None)
                (x, y) = lastClick
                # x and y must be floats, otherwise strange rounding errors
                # occur when converting to lat lon coordinates
                (lat, lon) = proj.xy2ll(x, y)
                middlePos = self.get('middlePos', [])
                middlePos.append((lat, lon, None, ""))
                self.set('middlePos', middlePos)
                # if in handmade input mode,
                # also ask for instructions for the given point
                if self.handmade:
                    self.sendMessage('route:middleInput')
            self.expectMiddle = False
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
                # x and y must be floats, otherwise strange rounding errors
                # occur when converting to lat lon coordinates
                (lat, lon) = proj.xy2ll(x, y)
                self.set('endPos', (lat, lon))
                self.destination = (lat, lon)
                self.start = None # clear start

            self.expectEnd = False
            self.set('needRedraw', True) # refresh the screen to show the new point

        elif message == "handmade":
            self.set('startPos', None)
            self.set('middlePos', [])
            self.set('endPos', None)
            self.selectOnePoint = False
            self.selectTwoPoints = True
            self.selectManyPoints = True
            self.handmade = True
            self.osdMenuState = OSD_EDIT
            print("HANDMADE")
            print(self.handmade)

        elif message == "selectTwoPoints":
            self.set('startPos', None)
            self.set('endPos', None)
            self.set('middlePos', [])
            self.selectOnePoint = False
            self.selectTwoPoints = True
            self.selectManyPoints = True
            self.osdMenuState = OSD_EDIT

        elif message == "selectOnePoint":
            self.set('startPos', None)
            self.set('endPos', None)
            self.set('middlePos', [])
            self.selectTwoPoints = True # we reuse the p2p menu
            self.selectOnePoint = True
            self.selectManyPoints = False
            self.osdMenuState = OSD_EDIT

        elif message == "p2pRoute": # simple route, between two points
            toPos = self.get("endPos", None)
            fromPos = self.get("startPos", None)
            if toPos and fromPos:
                toLat, toLon = toPos
                fromLat, fromLon = fromPos
                middlePoints = self.get('middlePos', [])
                print("Routing %f,%f to %f,%f through %d waypoints"
                      % (fromLat, fromLon, toLat, toLon, len(middlePoints)))
                # TODO: wait message (would it be needed when using internet routing ?)
                self.doRoute(fromLat, fromLon, toLat, toLon, waypoints=middlePoints)
                self.set('needRedraw', True) # show the new route

        elif message == "p2phmRoute": # simple route, from start to middle to end (handmade routing)
            fromPos = self.get("startPos", None)
            toPos = self.get("endPos", None)
            if fromPos and toPos:
                toLat, toLon = toPos
                fromLat, fromLon = fromPos
                middlePoints = self.get("middlePos", [])
                print("Handmade route ")
                print(fromLat, fromLon)
                print(" through ")
                print(middlePoints)
                print(" to %f,%f" % (toLat, toLon))
                war = way.fromHandmade(fromPos, middlePoints, toPos)
                print("NO WAI")
                print(war)
                self.processAndSaveResults(war, "start", "end", time.time())
                # start TbT navigation (if enabled)
                self.startNavigation()
                # switch to the route options OSD menu
                self.osdMenuState = OSD_CURRENT_ROUTE
                self.set('needRedraw', True) # show the new route

        elif message == "p2posRoute": # simple route, from here to selected point
            startPos = self.get('startPos', None)
            endPos = self.get('endPos', None)
            pos = self.get('pos', None)
            if pos is None: # well, we don't know where we are, so we don't know here to go :)
                return None

            if startPos is None and endPos is None: # we know where we are, but we don't know where we should go :)
                return None

            if startPos is not None: # we want a route from somewhere to our current position
                fromPos = startPos
                toPos = pos

            if endPos is not None: # we go from here to somewhere
                fromPos = pos
                toPos = endPos

            (toLat, toLon) = toPos
            (fromLat, fromLon) = fromPos

            middlePoints = self.get("middlePos", [])
            print("Routing %f,%f to %f,%f through %d waypoints"
                  % (fromLat, fromLon, toLat, toLon, len(middlePoints)))

            self.doRoute(fromLat, fromLon, toLat, toLon, waypoints=middlePoints)
            self.set('needRedraw', True) # show the new route

        elif message == "route": # find a route
            if messageType == 'md': # message-list based unpack requires a string argument of length 4 routing
                if args:
                    messageType = args['type']
                    go = False
                    if messageType == 'll2ll':
                        (fromLat, fromLon) = (float(args['fromLat']), float(args['fromLon']))
                        (toLat, toLon) = (float(args['toLat']), float(args['toLon']))
                        go = True
                    elif messageType == 'pos2ll':
                        pos = self.get('pos', None)
                        if pos:
                            (fromLat, fromLon) = pos
                            (toLat, toLon) = (float(args['toLat']), float(args['toLon']))
                            go = True

                    if go: # are we GO for routing ?
                        print("Routing %f,%f to %f,%f" % (fromLat, fromLon, toLat, toLon))
                        try:
                            self.doRoute(fromLat, fromLon, toLat, toLon)
                        except Exception:
                            import sys

                            e = sys.exc_info()[1]
                            self.sendMessage('ml:notification:m:No route found;3')
                            self.set('needRedraw', True)
                            print(e)
                            traceback.print_exc(file=sys.stdout)
                        if "show" in args:
                            # switch to map view and go to start/destination, if requested
                            where = args['show']
                            if where == 'start':
                                (cLat, cLon) = (fromLat, fromLon)
                            elif where == "destination":
                                (cLat, cLon) = (toLat, toLon)
                            self.sendMessage('mapView:recentre %f %f|set:menu:None' % (cLat, cLon))

                        self.set('needRedraw', True) # show the new route
            else: # simple route, from here to selected point
                # disable the point selection GUIs
                self.selectManyPoints = False # handmade
                self.selectTwoPoints = False
                self.selectOnePoint = False
                self.osdMenuState = OSD_CURRENT_ROUTE
                toPos = self.get("selectedPos", None)
                if toPos:
                    toLat, toLon = [float(a) for a in toPos.split(",")]
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
            loadTracklogs.storeRouteAndSetActive(self.directions.getPointsLLE(), '',
                                                 'online') # TODO: rewrite this when we support more routing providers

        elif message == "clearRoute":
            self._goToInitialState()

        elif message == 'startInput':
            entry = self.m.get('textEntry', None)
            if entry is None:
                print("route: text entry module not available")
                return
            entryText = self.get('startAddress', "")
            entry.entryBox(self, 'start', 'Input the start address', entryText)

        elif message == 'middleInput': # handmade
            entry = self.m.get('textEntry', None)
            if entry is None:
                return
            entryText = ""
            entry.entryBox(self, 'middle', 'Input the directions for this middle point', entryText)

        elif message == 'destinationInput':
            entry = self.m.get('textEntry', None)
            if entry is None:
                print("route: text entry module not available")
                return
            entryText = self.get('destinationAddress', "")
            entry.entryBox(self, 'destination', 'Input the destination address', entryText)

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
            if messageType == 'ms' and args == "fromPosToDest" and self.selectManyPoints == False: # handmade
                # reroute from current position to destination

                # is there a destination and valid position ?
                print("route: rerouting from current position to last destination")
                pos = self.get('pos', None)
                if self.destination and pos:
                    (pLat, pLon) = pos
                    (dLat, dLon) = (self.destination[0], self.destination[1])
                    self.doRoute(pLat, pLon, dLat, dLon)
                    self.start = None

        elif messageType == 'ms' and message == 'addressRouteMenu':
            if args == 'swap':
                # get current values
                start = self.get('startAddress', None)
                destination = self.get('destinationAddress', None)
                # swap them
                self.set('startAddress', destination)
                self.set('destinationAddress', start)
                # redraw the screen to show the change
                self.set('needRedraw', True)

        elif messageType == "ms" and message == "setOSDState":
            self.osdMenuState = int(args)
            self.set('needRedraw', True) # show the new menu

    def doRoute(self, fromLat, fromLon, toLat, toLon, waypoints=None):
        """Route from one point to another, and set that as the active route"""
        if not waypoints: waypoints = []
        # try to make sure waypoints are (lat, lon) tuples
        waypoints = map(lambda x: (x[0], x[1]), waypoints)

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
            monavWaypoints = [(fromLat, fromLon), (toLat, toLon)] # start
            # disable additional waypoint usage due to a protobuf serialization bug in monav-server,
            # that prevents getting results from more than 2 waypoints
            #      monavWaypoints.extend(waypoints) # waypoints

            result = self.getMonavRoute(monavWaypoints)
            #TODO: asynchronous processing & error notifications
            # as monav is VERY fast for routing, the routing might still get done
            # asynchronously, but the work-in-progress overlay might show up
            # only once the search takes longer than say 2 seconds
            self._handleResults("MonavRoute", (result, monavWaypoints[0], monavWaypoints[-1], sentTimestamp))

        else: # use Google Directions as fallback
            online = self.m.get('onlineServices', None)
            # prepare waypoints for Google Directions as a list of strings
            gdWaypoints = map(lambda x: "(%f, %f)" % (x[0], x[1]), waypoints)

            if online:
                online.googleDirectionsLLAsync((fromLat, fromLon), (toLat, toLon),
                                               self._handleResults, "onlineRoute", waypoints=gdWaypoints)

    def getMonavRoute(self, waypoints):
        mode = self.get('mode', 'car')
        # get mode based sub-folder
        # TODO: handle not all mode folders being available
        # (eq. user only downloading routing data for cars)
        modeFolders = {
            'cycle': 'routing_bike',
            'walk': 'routing_pedestrian',
            'car': 'routing_car'
        }
        subFolder = modeFolders.get(mode, 'routing_car')
        dataPacks = self.getAvailableMonavDataPacks()

        if dataPacks:
            # TODO: bounding box based pack selection
            preferredPack = self.get('preferredMonavDataPack', None)
            if preferredPack in dataPacks:
                packName = preferredPack
            else:
                # just take the first (and possibly only) pack
                packName = sorted(dataPacks)[0]
            mainMonavFolder = self.modrana.paths.getMonavDataPath()
            monavDataFolder = os.path.abspath(os.path.join(mainMonavFolder, packName, subFolder))
            print('Monav data folder:\n%s' % monavDataFolder)
            print(os.path.exists(monavDataFolder))
            try:
                # is Monav initialized ?
                if self.monav is None:
                    # start Monav #
                    # only import Monav & company when actually needed
                    # -> the protobuf modules are quite large
                    import monav_support

                    self.monav = monav_support.Monav(self.modrana.paths.getMonavServerBinaryPath())
                    self.monav.startServer()
                result = self.monav.monavDirections(monavDataFolder, waypoints)
            except Exception:
                import sys

                e = sys.exc_info()[1]
                print('route: Monav route lookup failed')
                print(e)
                traceback.print_exc(file=sys.stdout) # find what went wrong
                return None, None
            if result is None:
                return result, None
            elif result.type == result.SUCCESS:
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

    def getAvailableMonavDataPacks(self):
        """return all available Monav data packs in the main monav data folder"""
        # basically just list all directories in the Monav data folder
        try:
            mainMonavFolder = self.modrana.paths.getMonavDataPath()
            dataPacks = os.listdir(mainMonavFolder)
            dataPacks = filter(lambda x: os.path.isdir(os.path.join(mainMonavFolder, x)), dataPacks)
            return sorted(dataPacks)
        except Exception:
            import sys

            e = sys.exc_info()[1]
            print('route: listing the Monav data packs failed')
            print(e)
            return []

    def doAddressRoute(self, start, destination):
        """Route from one point to another, and set that as the active route"""
        # cleanup any possible previous routes
        self._goToInitialState()
        online = self.m.get('onlineServices', None)
        if online:
            print("route: routing from %s to %s" % (start, destination))
            online.googleDirectionsAsync(start, destination, self._handleResults, "onlineRouteAddress2Address")

    def _handleResults(self, key, resultsTuple):
        """handle a routing result"""
        routingSuccess = False
        if key in ("onlineRoute", "onlineRouteAddress2Address"):
            if key == "onlineRoute":
                (directions, start, destination, routeRequestSentTimestamp) = resultsTuple
                # remove any possible prev. route description, so new a new one for this route is created
                self.text = None

                # TODO: support other providers than Google & offline routing

                if directions: # is there actually something in the directions ?
                    # create the directions Way object
                    self.durationString = directions['routes'][0]['legs'][0]['duration']['text']
                    dirs = way.fromGoogleDirectionsResult(directions)
                    #TODO: use seconds from Way object directly
                    #(needs seconds to human representation conversion)
                    #self.duration = dirs.getDuration()
                    self.processAndSaveResults(dirs, start, destination, routeRequestSentTimestamp)
                    routingSuccess = True
                    self.startNavigation()
            elif key == "onlineRouteAddress2Address":
                (directions, start, destination, routeRequestSentTimestamp) = resultsTuple
                # remove any possible prev. route description, so new a new one for this route is created
                self.text = None
                if directions: # is there actually something in the directions ?
                    self.durationString = directions['routes'][0]['legs'][0]['duration']['text']
                    #TODO: use seconds from Way object directly
                    #(needs seconds to human representation conversion)
                    #self.duration = dirs.getDuration()

                    # create the directions Way object
                    dirs = way.fromGoogleDirectionsResult(directions)
                    self.processAndSaveResults(dirs, start, destination, routeRequestSentTimestamp)
                    routingSuccess = True
                    self.startNavigation()
            self.set('needRedraw', True)
        elif key == "MonavRoute":
            (result, start, destination, routeRequestSentTimestamp) = resultsTuple
            directions, returnCode = result

            if returnCode == ROUTING_SUCCESS:
                self.durationString = "" # TODO : correct predicted route duration

                # provided a turn detection function to the way object
                tbt = self.m.get("turnByTurn", None)
                if tbt:
                    getTurns = tbt.getMonavTurns
                else:
                    getTurns = None

                dirs = way.fromMonavResult(directions, getTurns)
                self.processAndSaveResults(dirs, start, destination, routeRequestSentTimestamp)

                routingSuccess = True
                # handle navigation autostart
                self.startNavigation()
                self.set('needRedraw', True)

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

        # if routing was successful switch to the current-route OSD menu
        if routingSuccess:
            self.osdMenuState = OSD_CURRENT_ROUTE

    def startNavigation(self):
        """handle navigation autostart"""
        autostart = self.get('autostartNavigationDefaultOnAutoselectTurn', 'enabled')
        if autostart == 'enabled':
            self.sendMessage('ms:turnByTurn:start:%s' % autostart)


    def processAndSaveResults(self, directionsWay, start, destination, routeRequestSentTimestamp):
        """process and save routing results"""
        self.routeRequestSentTimestamp = routeRequestSentTimestamp
        proj = self.m.get('projection', None)
        if proj:
            self.pxpyRoute = [proj.ll2pxpyRel(x[0], x[1]) for x in directionsWay.getPointsLLE()]
        self.processAndSaveDirections(directionsWay)

        (fromLat, fromLon) = directionsWay.getPointByID(0).getLL()
        (toLat, toLon) = directionsWay.getPointByID(-1).getLL()

        # use coordinates for start dest or use first/last point from the route
        # if start/dest coordinates are unknown (None)
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

    def getDirections(self):
        return self.directions

    def filterDirections(self, directions):
        """
        filter directions according to substitution rules (specified by a CSV file)
        -> mostly used to replace abbreviations by full words in espeak output
        -> also assure Pango compatibility (eq. get rid of  <div> and company)
        """
        steps = directions.getMessagePoints()

        for step in steps:
            originalMessage = "".join(str(step.getMessage()))
            try:
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
            except Exception:
                import sys

                e = sys.exc_info()[1]
                print("route: error during direction filtering")
                print(e)
                step.setSSMLMessage(message)


        # replace old message points with new ones
        directions.clearMessagePoints()
        directions.addMessagePoints(steps)

        return directions

    def processCyrillicString(self, inputString, voiceCode):
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
                except Exception:
                    import sys

                    e = sys.exc_info()[1]
                    # just skip this as the character is  most probably unknown
                    pass
            if cyrillicCharFound: # the substring contains at least one cyrillic character
                if cyrillicStringTemp: # append to the already "open" cyrillic string
                    cyrillicStringTemp += ' ' + substring
                else: # create a new cyrillic string
                    # make espeak say this word in russian (or other voiceCode),
                    # based on Cyrillic being detected in it
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
        return outputString

    def drawScreenOverlay(self, cr):
        showMenu = False
        menus = self.m.get('menu', None)
        if menus:
            # check if the buttons should not be hidden
            showMenu = not menus.buttonsHidingOn() and self.osdMenuState is not None

        if showMenu:
            if self.osdMenuState == OSD_EDIT:
                self.drawRoutePlaningMenu(cr)
            elif self.osdMenuState == OSD_CURRENT_ROUTE: # current route info button
                self.drawCurrentRouteButton(cr)
            elif self.osdMenuState == OSD_ROUTE_OPTIONS:
                self.drawCurrentRouteOptionsMenu(cr)


        #register clickable areas for manual point input
        if self.expectStart:
            clickHandler = self.m.get('clickHandler', None)
            (x, y, w, h) = self.get('viewport')
            if clickHandler is not None:
                clickHandler.registerXYWH(x, y, x + w, y + h, 'route:setStart')
        if self.expectMiddle: # handmade
            clickHandler = self.m.get('clickHandler', None)
            (x, y, w, h) = self.get('viewport')
            if clickHandler is not None:
                clickHandler.registerXYWH(x, y, x + w, y + h, 'route:setMiddle')
        if self.expectEnd:
            clickHandler = self.m.get('clickHandler', None)
            (x, y, w, h) = self.get('viewport')
            if clickHandler is not None:
                clickHandler.registerXYWH(x, y, x + w, y + h, 'route:setEnd')

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
            steps = map(lambda x: (proj.ll2xy(x[0], x[1])), steps)

            if self.start:
                start = proj.ll2xy(self.start[0], self.start[1])
                # line from starting point to start of the route
                (x, y) = start
                (px1, py1) = self.pxpyRoute[0]
                (x1, y1) = proj.pxpyRel2xy(px1, py1)
                cr.set_source_rgba(0, 0, 0.5, 0.45)
                cr.set_line_width(10)
                cr.move_to(x, y)
                cr.line_to(x1, y1)
                cr.stroke()

            if self.destination:
                destination = proj.ll2xy(self.destination[0], self.destination[1])
                # line from the destination point to end of the route
                (x, y) = destination
                (px1, py1) = self.pxpyRoute[-1]
                (x1, y1) = proj.pxpyRel2xy(px1, py1)
                cr.move_to(x, y)
                cr.line_to(x1, y1)
                cr.stroke()

            cr.fill()

            # draw the step point background (under the polyline, it seems to look better this way)

            cr.set_source_rgb(0, 0, 0)
            cr.set_line_width(10)

            for step in steps:
                (x, y) = step
                cr.arc(x, y, 3, 0, 2.0 * math.pi)
                cr.stroke()

            cr.fill()

            cr.set_source_rgb(0, 0, 0.5)
            cr.set_line_width(10)

            # draw the points from the polyline as a polyline :)

            (px, py) = self.pxpyRoute[0]
            (x, y) = proj.pxpyRel2xy(px, py)
            cr.move_to(x, y)

            # well, this SHOULD be faster and this is a performance critical section after all...
            #    map(lambda x: cr.line_to(x[0],x[1]), route[1:]) # lambda drawing :)
            # according to numerous sources, list comprehensions should be faster than for loops and map+lambda
            # if its faster in this case too has not been determined

            # routing result drawing algorithm
            # adapted from TangoGPS source (tracks.c)
            # works surprisingly good

            z = proj.zoom
            # these setting seem to work the best for routing results:
            # (they have a different structure than logging traces,
            # eq. long segments delimited by only two points, etc)
            # basically, routing results have only the really needed points -> less points than traces
            if self.handmade or len(self.pxpyRoute) < 20:
                # handmade routes usually have very few points and we don't want to skip any
                # also handle very short routes that might have the same issue
                modulo = 1
            elif 16 > z > 10:
                modulo = 2 ** (14 - z)
            elif z <= 10:
                modulo = 16
            else:
                modulo = 1

                #    maxDraw = 300
                #    drawCount = 0
            counter = 0

            for point in self.pxpyRoute[1:]: #draw the track
                counter += 1
                if counter % modulo == 0:
                #      if 1:
                #        drawCount+=1
                #        if drawCount>maxDraw:
                #          break
                    (px, py) = point
                    (x, y) = proj.pxpyRel2xy(px, py)
                    cr.line_to(x, y)

                    # make a line to the last point (the modulo method sometimes skips the end of the track)
                    #    [cr.line_to(x[0],x[1])for x in route[1:]] # list comprehension drawing :D

                    #    print(drawCount)
                    #    print(modulo)

            # make sure the last point is connected
            (px, py) = self.pxpyRoute[-1]
            (x, y) = proj.pxpyRel2xy(px, py)
            cr.line_to(x, y)

            cr.stroke()

            # draw the step points over the polyline
            cr.set_source_rgb(1, 1, 0)
            cr.set_line_width(7)
            for step in steps:
                (x, y) = step
                cr.arc(x, y, 2, 0, 2.0 * math.pi)
                cr.stroke()
            cr.fill()
            # draw the the start/dest indicators over the route
        if self.selectTwoPoints:
            self.drawPointSelectors(cr)

            #    print("Redraw took %1.9f ms" % (1000 * (clock() - start1)))

    def getCurrentDirections(self):
        """return the current route"""
        return self.directions, self.routeRequestSentTimestamp

    def drawCurrentRouteButton(self, cr):
        """draw the info button for the current route on the map screen"""
        (x, y, w, h) = self.get('viewport')
        menus = self.m.get('menu', None)
        dx = min(w, h) / 5.0
        dy = dx
        x1 = (x + w) - dx
        y1 = (y - dy) + h
        menus.drawButton(cr, x1, y1, dx, dy, 'tools#route', "generic:;0.5;;0.5;;",
                         'ms:route:setOSDState:%d' % OSD_ROUTE_OPTIONS)

    def drawCurrentRouteOptionsMenu(self, cr):
        """draw the options for the current route on the map screen"""
        (x, y, w, h) = self.get('viewport')
        menus = self.m.get('menu', None)
        dx = min(w, h) / 5.0
        dy = dx
        x1 = (x + w) - dx
        y1 = (y - dy) + h
        menus.drawButton(cr, x1 - dx, y1, dx, dy,
                         'edit', "above:edit>generic:;0.5;;0.5;;", 'ms:route:setOSDState:%d' % OSD_EDIT)
        menus.drawButton(cr, x1, y1, dx, dy,
                         'info', "above:info>generic:;0.5;;0.5;;",
                         'set:menu:route#currentRouteBackToMap|ms:route:setOSDState:%d' % OSD_EDIT)

    def drawRoutePlaningMenu(self, cr):
        """draw the onscreen menu for route planing"""
        (x, y, w, h) = self.get('viewport')
        dx = min(w, h) / 5.0
        dy = dx
        menus = self.m.get('menu', None)
        x1 = (x + w) - dx
        y1 = (y - dy) + h

        startIcon = "generic:;0.5;;0.5;;"
        middleIcon = "generic:;0.5;;0.5;;"
        endIcon = "generic:;0.5;;0.5;;"
        if self.expectStart:
            startIcon = "generic:red;0.5;red;0.5;;"
        if self.expectMiddle:
            middleIcon = "generic:blue;0.5;blue;0.5;;"
        if self.expectEnd:
            endIcon = "generic:green;0.5;green;0.5;;"

        routingAction = 'route:p2pRoute'
        if self.selectOnePoint:
            routingAction = 'route:p2posRoute'
        if self.handmade: # handmade
            routingAction = 'route:p2phmRoute'

        menus.drawButton(cr, x1 - dx, y1, dx, dy, 'start', startIcon, "route:expectStart")
        # Monav currently has a bug preventing waypoint routing
        routingProvider = self.get('routingProvider', 'GoogleDirections')
        if self.handmade or routingProvider == 'GoogleDirections':
            menus.drawButton(cr, x1 - dx, y1 - dy, dx, dy, 'middle', middleIcon, "route:expectMiddle") # handmade
        menus.drawButton(cr, x1, y1 - dy, dx, dy, 'end', endIcon, "route:expectEnd")
        menus.drawButton(cr, x1, y1, dx, dy, 'route', "generic:;0.5;;0.5;;", routingAction)

        # "flush" cairo operations
        cr.stroke()
        cr.fill()

    def drawPointSelectors(self, cr):
        # draw point selectors
        proj = self.m.get('projection', None)
        fromPos = self.get('startPos', None)
        middlePos = self.get('middlePos', None)
        toPos = self.get('endPos', None)
        if fromPos is not None:
            cr.set_line_width(10)
            cr.set_source_rgb(1, 0, 0)
            (lat, lon) = fromPos

            (x, y) = proj.ll2xy(lat, lon)

            cr.arc(x, y, 3, 0, 2.0 * math.pi)
            cr.stroke()
            cr.fill()

            cr.set_line_width(8)
            cr.set_source_rgba(1, 0, 0, 0.95) # transparent red
            cr.arc(x, y, 15, 0, 2.0 * math.pi)
            cr.stroke()
            cr.fill()

        # only show middle point indicators in the
        # edit menu mode at they might easily overlay the route otherwise
        if middlePos and self.osdMenuState == OSD_EDIT:
            for point in middlePos:
                (lat, lon) = point[0], point[1]
                cr.set_line_width(10)
                cr.set_source_rgb(0, 0, 1)
                (x, y) = proj.ll2xy(lat, lon)
                cr.arc(x, y, 2, 0, 2.0 * math.pi)
                cr.stroke()
                cr.fill()

                cr.set_line_width(8)
                cr.set_source_rgba(0, 0, 1, 0.95) # transparent blue
                cr.arc(x, y, 15, 0, 2.0 * math.pi)
                cr.stroke()
                cr.fill()

        if toPos is not None:
            cr.set_line_width(10)
            cr.set_source_rgb(0, 1, 0)
            (lat, lon) = toPos
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
        elif key == 'middle':
            mpList = self.get('middlePos', [])
            if mpList:
                # replace the last added point by the same point with
                # message user wrote to the entry box
                lastMiddlePoint = mpList.pop()
                (lat, lon, elev, message) = lastMiddlePoint
                message = result
                mpList.append((lat, lon, elev, message))
                self.set('middlePos', mpList)
        elif key == 'destination':
            self.destinationAddress = result
            self.set('destinationAddress', result)
        self.set('needRedraw', True)

    def drawMenu(self, cr, menuName, args=None):
        if menuName == 'currentRoute' or menuName == 'currentRouteBackToMap':
            menus = self.m.get("menu", None)
            if menus is None:
                print("route: no menu module, no menus will be drawn")
                return

            # if called from the osd menu, go back to map at escape
            if menuName == 'currentRouteBackToMap':
                parent = 'set:menu:None'
            else:
                parent = 'set:menu:route'

            if self.directions:
                (lat, lon) = self.directions.getPointByID(0).getLL()
                action = "mapView:recentre %f %f|set:menu:None" % (lat, lon)

            else:
                action = "set:menu:None"

            button1 = ("map#show on", "generic", action)
            button2 = ("tools", "tools", "set:menu:currentRouteTools")

            if not self.directions:
                text = "There is currently no active route."
            elif self.text is None: # the new text for the info-box only once
                # check for online status
                online = (self.modrana.dmod.getInternetConnectivityStatus() in (True, None))
                # check if start and destination geocoding is needed
                if not self.routeDetailGeocodingTriggered:
                    if online:
                        self._geocodeStartAndDestination()
                        self.routeDetailGeocodingTriggered = True

                if self.durationString:
                    duration = self.durationString # a string describing the estimated time to finish the route
                else:
                    duration = "? minutes"
                units = self.m.get('units', None) # get the correct units
                length = self.directions.getLength()
                if length:
                    distance = units.m2CurrentUnitString(length, 1)
                else:
                    distance = "? km"
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
                text += "%s" % destination
                text += "\n\n%s in about %s and %s steps" % (distance, duration, steps)
                if self.start and self.destination:
                    (lat1, lon1) = (self.start[0], self.start[1])
                    (lat2, lon2) = (self.destination[0], self.destination[1])
                    text += "\n(%f,%f)->(%f,%f)" % (lat1, lon1, lat2, lon2)

                self.text = text
            else:
                text = self.text

            if self.once:
                self.once = False

            box = (text, "set:menu:route#currentRoute")
            menus.drawThreePlusOneMenu(cr, menuName, parent, button1, button2, box)
            menus.clearMenu('currentRouteTools', "set:menu:route#currentRoute")
            menus.addItem('currentRouteTools', 'tracklog#save as', 'generic',
                          'route:storeRoute|set:currentTracCat:online|set:menu:tracklogManager#tracklogInfo')

            # add turn-by-turn navigation buttons
            tbt = self.m.get('turnByTurn', None)
            if tbt:
                if tbt.enabled():
                    menus.addItem('currentRouteTools', 'navigation#stop', 'generic', 'turnByTurn:stop|set:menu:None')
                    menus.addItem('currentRouteTools', 'navigation#restart', 'generic',
                                  'turnByTurn:stop|ms:turnByTurn:start:closest|set:menu:None')
                    self.set('needRedraw', True) # refresh the screen to show the changed button
                else:
                    menus.addItem('currentRouteTools', 'navigation#start', 'generic',
                                  'ms:turnByTurn:start:enabled|set:menu:None')

            menus.addItem('currentRouteTools', 'clear', 'generic', 'route:clear|set:menu:None')

        if menuName == "showAddressRoute":
            self._drawAddressRoutingMenu(cr)

    def _drawAddressRoutingMenu(self, cr):
        menus = self.m.get("menu", None)
        if menus:
            (e1, e2, e3, e4, alloc) = menus.threePlusOneMenuCoords()
            (x1, y1) = e1
            (x2, y2) = e2
            (x3, y3) = e3
            (x4, y4) = e4
            (w1, h1, dx, dy) = alloc

            # * draw "escape" button
            menus.drawButton(cr, x1, y1, dx, dy, "", "back", "set:menu:main")
            # * swap
            menus.drawButton(cr, x2, y2, dx, dy, "swap", "generic", "ms:route:addressRouteMenu:swap")
            # * route
            menus.drawButton(cr, x3, y3, dx, dy, "route", "generic", "route:addressRoute")

            menus.clearMenu('currentRouteTools', "set:menu:route#currentRoute")

            menus.drawButton(cr, x4, y4, w1 - x4, dy, "start", "generic", "route:startInput")
            menus.drawButton(cr, x4, y4 + 2 * dy, w1 - x4, dy, "destination", "generic", "route:destinationInput")
            menus.drawButton(cr, x4, y4 + dy, (w1 - x4) / 2, dy, "as start#position", "generic",
                             "route:posToStart|set:needRedraw:True")
            menus.drawButton(cr, x4 + (w1 - x4) / 2, y4 + dy, (w1 - x4) / 2, dy, "as destination#position", "generic",
                             "route:posToDestination|set:needRedraw:True")

            # try to get last used addresses
            startText = self.get('startAddress', None)
            destinationText = self.get('destinationAddress', None)

            # if there are no last used addresses, use defaults
            if startText is None:
                startText = "click to input starting address"

            if destinationText is None:
                destinationText = "click to input destination address"

            menus.showText(cr, startText, x4 + w1 / 20, y4 + dy / 5, w1 - x4 - (w1 / 20) * 2)
            menus.showText(cr, destinationText, x4 + w1 / 20, y4 + 2 * dy + dy / 5, w1 - x4 - (w1 / 20) * 2)

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
  
  
