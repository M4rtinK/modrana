from __future__ import with_statement # for python 2.5
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
import math
import re
import csv
import unicodedata
import time
import threading
from core import constants
from core.point import Point, TurnByTurnPoint
from core.signal import Signal
from core.way import Way
from core.backports.six import u
from core import routing_providers


DIRECTIONS_FILTER_CSV_PATH = 'data/directions_filter.csv'

# OSD menu states
OSD_EDIT = 1 # route editing buttons
OSD_CURRENT_ROUTE = 2 # a single button that triggers the options menu
OSD_ROUTE_OPTIONS = 3 # buttons that go to the edit or info menus


def getModule(*args, **kwargs):
    return Route(*args, **kwargs)


#noinspection PyAttributeOutsideInit
class Route(RanaModule):
    """Routes"""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self._goToInitialState()
        # how long the last routing lookup took in seconds
        self.routeLookupDuration = 0
        self.once = True
        self.entry = None

        # tracks the state of the onscreen routing menu
        self.osdMenuState = None

        self.set('startPos', None)
        self.set('endPos', None)

        self._directionsFilterRules = []
        self._directionsFilterRulesLoaded = False

        self._addressLookupLock = threading.Lock()
        self._startLookup = False
        self._destinationLookup = False

        # offline routing provider
        self._offline_routing_provider = None

        # signals
        self.routingDone = Signal()

    def _goToInitialState(self):
        """restorer initial routing state
        -> used in init and when rerouting"""
        self.pxpyRoute = [] # route in screen coordinates
        self.directions = [] # directions object
        self.set('midText', [])
        self.durationString = None # in seconds
        self.start = None
        self.destination = None
        self.startAddress = None
        self.destinationAddress = None
        self.text = None
        self.textPortrait = None
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
        self.log.debug("directions filter loaded in %1.2f ms", (time.time() - start) * 1000)

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
                self.start = Point(lat, lon)
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
                self.destination = Point(lat, lon)
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
            self.log.info("Using handmade routing")
            self.log.info(self.handmade)

        elif message == "selectTwoPoints":
            self.set('startPos', None)
            self.set('endPos', None)
            self.set('middlePos', [])
            self.selectOnePoint = False
            self.selectTwoPoints = True
            self.selectManyPoints = False
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
            destination = self.get("endPos", None)
            start = self.get("startPos", None)
            if destination and start:
                middlePoints = self.get('middlePos', [])
                self.llRoute(start, destination, middlePoints)
                self.set('needRedraw', True)

        elif message == "p2phmRoute": # simple route, from start to middle to end (handmade routing)
            start = self.get("startPos", None)
            destination = self.get("endPos", None)
            if start and destination:
                toLat, toLon = destination
                fromLat, fromLon = start
                middlePoints = self.get("middlePos", [])
                self.log.info("Handmade route")
                self.log.info("%f,%f", fromLat, fromLon)
                self.log.info("through")
                self.log.info(middlePoints)
                self.log.info("to %f,%f", toLat, toLon)
                handmadeRoute = Way.from_handmade(start, middlePoints, destination)
                self._handleRoutingResultCB((handmadeRoute, "", 0))

        elif message == "p2posRoute": # simple route, from here to selected point
            startPos = self.get('startPos', None)
            endPos = self.get('endPos', None)
            pos = self.get('pos', None)
            start = None
            destination = None
            if pos is None: # well, we don't know where we are, so we don't know here to go :)
                return None

            if startPos is None and endPos is None: # we know where we are, but we don't know where we should go :)
                return None

            if startPos is not None: # we want a route from somewhere to our current position
                start = startPos
                destination = pos

            if endPos is not None: # we go from here to somewhere
                start = pos
                destination = endPos

            middlePoints = self.get("middlePos", [])
            if start and destination:
                self.llRoute(start, destination, middlePoints)
                self.set('needRedraw', True) # show the new route

        elif message == "route": # find a route
            if messageType == 'md': # message-list based unpack requires a string argument of length 4 routing
                if args:
                    messageType = args['type']
                    start = None
                    destination = None
                    if messageType == 'll2ll':
                        start = (float(args['fromLat']), float(args['fromLon']))
                        destination = (float(args['toLat']), float(args['toLon']))
                    elif messageType == 'pos2ll':
                        pos = self.get('pos', None)
                        if pos:
                            start = pos
                            destination = (float(args['toLat']), float(args['toLon']))

                    if start and destination: # are we GO for routing ?
                        try:
                            self.llRoute(start, destination)
                        except Exception:
                            self.sendMessage('ml:notification:m:No route found;3')
                            self.set('needRedraw', True)
                            self.log.exception("exception during routing")
                        if "show" in args:
                            # switch to map view and go to start/destination, if requested
                            where = args['show']
                            if where == 'start':
                                self.sendMessage('mapView:recentre %f %f|set:menu:None' % start)
                            elif where == "destination":
                                self.sendMessage('mapView:recentre %f %f|set:menu:None' % destination)

                        self.set('needRedraw', True)
            else: # simple route, from here to selected point
                # disable the point selection GUIs
                self.selectManyPoints = False # handmade
                self.selectTwoPoints = False
                self.selectOnePoint = False
                self.osdMenuState = OSD_CURRENT_ROUTE
                start = self.get("pos", None)
                destination = self.get("selectedPos", None)
                destination = [float(a) for a in destination.split(",")]
                if start and destination:
                    self.llRoute(start, destination)
                    self.set('needRedraw', True)

        elif message == 'storeRoute':
            loadTracklogs = self.m.get('loadTracklogs', None)
            if loadTracklogs is None:
                self.log.error("can't store route without the loadTracklog module")
                return
            if not self.directions:
                self.log.info("the route is empty, so it will not be stored")
                return
            # TODO: rewrite this when we support more routing providers
            loadTracklogs.storeRouteAndSetActive(self.directions.points_lle,
                                                 '',
                                                 'online')

        elif message == "clearRoute":
            self._goToInitialState()

        elif message == 'startInput':
            entry = self.m.get('textEntry', None)
            if entry is None:
                self.log.error("text entry module not available")
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
                self.log.error("text entry module not available")
                return
            entryText = self.get('destinationAddress', "")
            entry.entryBox(self, 'destination', 'Input the destination address', entryText)

        elif message == 'addressRoute':
            startAddress = self.get('startAddress', None)
            destinationAddress = self.get('destinationAddress', None)
            if startAddress and destinationAddress:
                self.log.info("address routing")
                self.set('menu', None) # go to the map screen
                self.addressRoute(startAddress, destinationAddress)
            else: # notify the user about insufficient input and remain in the menu
                self.log.error("can't route - start or destination (or both) not set")
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
                self.log.info("rerouting from current position to last destination")
                pos = self.get('pos', None)
                if self.destination and pos:
                    start = Point(*pos)
                    self.doRoute([start, self.destination])
                    self.start = None
                    self.set('needRedraw', True)

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

    def routeAsync(self, callback, waypoints, route_params=None):
        """Asynchronous routing

        NOTE: online/offline routing provider is selected automatically

        :param callback: routing result handler
        :type callback: a callable
        :param waypoints: a list of 2 or more waypoints defining the route
        :type waypoints: a list of Point objects
        :param route_params: parameters for the route search
        :type route_params: RouteParameters object instance or None for defaults
        """

        if route_params is None:
            route_params = self._getDefaultRouteParameters()
            # no custom route parameters provided, build default ones
            # based on current settings

        providerID = self.get('routingProvider', constants.DEFAULT_ROUTING_PROVIDER)
        self.log.debug("routing provider ID: %s", providerID)
        if providerID in (constants.ROUTING_PROVIDER_MONAV_SERVER, constants.ROUTING_PROVIDER_MONAV_LIGHT):
            # is Monav initialized ? (lazy initialization)
            if self._offline_routing_provider is None:
                # instantiate the offline routing provider
                if providerID == constants.ROUTING_PROVIDER_MONAV_LIGHT:
                    provider = routing_providers.MonavLightRouting(
                        monav_light_executable_path=self.modrana.dmod.monav_light_binary_path,
                        monav_data_path = self._getMonavDataPath()
                    )
                else:
                    provider = routing_providers.MonavServerRouting(
                        monav_server_executable_path=self.modrana.paths.getMonavServerBinaryPath(),
                        monav_data_path = self._getMonavDataPath()
                    )
                self._offline_routing_provider = provider

            # update the path to the Monav data folder
            # in the Monav wrapper in case in changed since last search
            self._offline_routing_provider.data_path = self._getMonavDataPath()

            # do the offline routing
            self._offline_routing_provider.searchAsync(
            callback,
            waypoints,
            route_params=route_params
        )
        elif providerID == constants.ROUTING_PROVIDER_GOOGLE:
            provider = routing_providers.GoogleRouting()
            provider.searchAsync(
                callback,
                waypoints,
                route_params=route_params
            )
        else:
            self.log.error("unknown routing provider ID: %s", providerID)


    def _getDefaultRouteParameters(self):
        mode = self.get("mode", "car")
        routeMode = constants.ROUTE_CAR
        langCode = self.get("directionsLanguage", "en en")
        # the (Google) language code is the second part of
        # this whitespace delimited string
        langCode = langCode.split(" ")[1]
        if self.modrana.gui.getIDString() == "GTK":
            if mode == "walk":
                routeMode = constants.ROUTE_PEDESTRIAN
            elif mode == "cycle":
                routeMode = constants.ROUTE_BIKE
        elif self.modrana.gui.getIDString() == "Qt5":
            # the Qt 5 GUI currently does not use an application wide
            # mode concept and sets the routing mode separately
            routeMode = self.get("routingModeQt5", constants.ROUTE_CAR)
        route_params = routing_providers.RouteParameters(
            routeMode=routeMode,
            avoidTollRoads=self.get("routingAvoidToll", False),
            avoidHighways=self.get("routingAvoidHighways", False),
            language = langCode
        )
        return route_params

    def llRoute(self, start, destination, middlePoints=None):
        if not middlePoints: middlePoints = []

        # tuples -> Points
        start = Point(*start)
        destination = Point(*destination)

        # list of tuples -> list of Points
        #middlePoints = list(map(lambda x: Point(x[0], x[1]), middlePoints))
        waypoints = [start]
        for mpTuple in middlePoints:
            waypoints.append(Point(mpTuple[0], mpTuple[1]))
        waypoints.append(destination)
        self.log.info("Routing %s to %s through %d waypoints",
              start, destination, len(middlePoints))
        # TODO: wait message (would it be needed when using internet routing ?)
        self.doRoute(waypoints)

    def addressRoute(self, start, destination):
        """Route from one address to another, and set the result as the active route
        NOTE: both address string and plaintext geographic coordinates can be used

        :param start: starting address
        :type start: str
        :param destination: destination address
        :type destination: str
        """
        # cleanup any possible previous routes
        self._goToInitialState()
        self.log.info("Address-routing from %s to %s", start, destination)
        waypoints = [start, destination]
        # specify that this route lookup should expect start and destination
        # specified as address strings
        params = self._getDefaultRouteParameters()
        params.addressRoute = True
        self.routeAsync(self._handleRoutingResultCB, waypoints, route_params=params)

    def doRoute(self, waypoints):
        """Route from one point to another"""

        # clear old addresses
        self.startAddress = None
        self.destinationAddress = None
        # the new result would probably have different start and destination coordinates
        self.routeDetailGeocodingTriggered = False

        #TODO: respect offline mode and automatically
        # use offline routing methods
        # TODO: notify user if no offline routing data is available for the current area

        self.routeAsync(self._handleRoutingResultCB, waypoints)

    def _handleRoutingResultCB(self, result):
        # remove any previous route description
        self.text = None
        # trigger the routing done signal
        self.routingDone(result)

        if result.route and result.returnCode == constants.ROUTING_SUCCESS:
            # process and save routing results
            self.routeLookupDuration = result.lookupDuration

            # set start and destination
            start = result.route.get_point_by_index(0)
            destination = result.route.get_point_by_index(-1)
            # use coordinates for start dest or use first/last point from the route
            # if start/dest coordinates are unknown (None)
            if self.start is None:
                self.start = start
            if self.destination is None:
                self.destination = destination

            self.osdMenuState = OSD_CURRENT_ROUTE

            # do the GTK GUI specific stuff only when running with GTK GUI
            if self.modrana.gui.getIDString() == "GTK":
                # save a copy of the route in projection units for faster drawing
                proj = self.m.get('projection', None)
                if proj:
                    self.pxpyRoute = [proj.ll2pxpyRel(x[0], x[1]) for x in result.route.points_lle]
                self.processAndSaveDirections(result.route)
                self.osdMenuState = OSD_CURRENT_ROUTE
                self.startNavigation()

        else: # routing failed
            self.log.error("routing ended with error")
            if result.errorMessage:
                error_message = result.errorMessage
            else:
                error_message = constants.ROUTING_FAILURE_MESSAGES.get(result.returnCode, "Routing failed.")
            self.log.error("routing error message: %s", error_message)
            self.notify(error_message, 3000)

    def getAvailableMonavDataPacks(self):
            """Return all available Monav data packs in the main monav data folder

            :return: list of all packs in Monav data folder
            :rtype: a list of strings
            """
            # basically just list all directories in the Monav data folder
            try:
                mainMonavFolder = self.modrana.paths.getMonavDataPath()
                dataPacks = os.listdir(mainMonavFolder)
                dataPacks = filter(lambda x: os.path.isdir(os.path.join(mainMonavFolder, x)), dataPacks)
                return sorted(dataPacks)
            except Exception:
                self.log.exception('listing the Monav data packs failed')
                return []

    def _getMonavDataPath(self):
        """Get path to the correct Monav data path based on current settings
        """
        # TODO: handle not all mode folders being available
        # (eq. user only downloading routing data for cars)
        modeFolders = {
            'cycle': 'routing_bike',
            'walk': 'routing_pedestrian',
            'car': 'routing_car'
        }
        mode = self.get('mode', 'car')
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
                self.log.info("monav: no preferred pack set, "
                      "using first available:\n%s", preferredPack)
            mainMonavFolder = self.modrana.paths.getMonavDataPath()
            monavDataFolder = os.path.abspath(os.path.join(mainMonavFolder, packName, subFolder))
            self.log.info('Monav data folder:\n%s', monavDataFolder)
            return monavDataFolder
        else:
            return None

    def startNavigation(self):
        """handle navigation autostart"""
        autostart = self.get('autostartNavigationDefaultOnAutoselectTurn', 'enabled')
        if autostart == 'enabled':
            self.sendMessage('ms:turnByTurn:start:%s' % autostart)

    def processAndSaveDirections(self, route):
        """process and save directions"""

        # apply filters
        route = self.filterDirections(route)

        # add a fake destination step, so there is a "destination reached" message
        if route.point_count > 0:
            (lat, lon) = route.get_point_by_index(-1).getLL()
            destStep = TurnByTurnPoint(lat, lon)
            destStep.ssmlMessage = '<p xml:lang="en">you <b>should</b> be near the destination</p>'
            destStep.description ='you <b>should</b> be near the destination'
            destStep.distanceFromStart = route.length
            # TODO: make this multilingual
            # add it to the end of the message point list
            route.add_message_point(destStep)

        # save
        self.directions = route

    def getDirections(self):
        return self.directions

    def filterDirections(self, directions):
        """
        filter directions according to substitution rules (specified by a CSV file)
        -> mostly used to replace abbreviations by full words in espeak output
        -> also assure Pango compatibility (eq. get rid of  <div> and company)
        """
        steps = directions.message_points

        for step in steps:
            originalMessage = "".join(str(step.description))
            message = ""
            try:
                message = step.description #TODO: make a method for this
                message = re.sub(r'<div[^>]*?>', '\n<i>', message)
                message = re.sub(r'</div[^>]*?>', '</i>', message)
                message = re.sub(r'<wbr/>', ', ', message)
                message = re.sub(r'<wbr>', ', ', message)
                step.description = message
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
                step.ssmlMessage = message
            except Exception:
                self.log.exception("error during direction filtering")
                step.ssmlMessage = message

        # replace old message points with new ones
        directions.clear_message_points
        directions.add_message_points(steps)

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
                    unicodeName = unicodedata.name(u(character))
                    if unicodeName.find('CYRILLIC') != -1:
                        cyrillicCharFound = True
                        break
                except Exception:
                    import sys
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
            steps = self.directions.message_points_lle

            # now we convert geographic coordinates to screen coordinates, so we dont need to do it twice
            steps = map(lambda x: (proj.ll2xy(x[0], x[1])), steps)

            if self.start:
                start = proj.ll2xy(self.start.lat, self.start.lon)
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
                destination = proj.ll2xy(self.destination.lat, self.destination.lon)
                # line from the destination point to end of the route
                (x, y) = destination
                (px1, py1) = self.pxpyRoute[-1]
                (x1, y1) = proj.pxpyRel2xy(px1, py1)
                cr.set_source_rgba(0, 0, 0.5, 0.45)
                cr.set_line_width(10)
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

                    #    self.log.debug(drawCount)
                    #    self.log.debug(modulo)

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

            #    self.log.debug("Redraw took %1.9f ms" % (1000 * (clock() - start1)))

    def getCurrentDirections(self):
        """return the current route"""
        return self.directions

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
                         'set:menu:route#currentRouteBackToMap|ms:route:setOSDState:%d' % OSD_CURRENT_ROUTE)

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
        routingProvider = self.get('routingProvider', constants.DEFAULT_ROUTING_PROVIDER)
        # TODO: find if Monav/Routino can handle middle points ?
        if self.handmade or routingProvider == constants.ROUTING_PROVIDER_GOOGLE:
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
                self.log.error("no menu module, no menus will be drawn")
                return

            # if called from the osd menu, go back to map at escape
            if menuName == 'currentRouteBackToMap':
                parent = 'set:menu:None'
            else:
                parent = 'set:menu:route'

            if self.directions:
                (lat, lon) = self.directions.get_point_by_index(0).getLL()
                action = "mapView:recentre %f %f|set:menu:None" % (lat, lon)

            else:
                action = "set:menu:None"

            button1 = ("map#show on", "generic", action)
            button2 = ("tools", "tools", "set:menu:currentRouteTools")

            # re-render text if viewport aspect ratio changed
            if self.textPortrait is not self.modrana.gui.portrait:
                self.text = None

            if not self.directions:
                text = "There is currently no active route."
            elif self.text is None: # the new text for the info-box only once
                # record viewport type during text caching
                self.textPortrait = self.modrana.gui.portrait


                # check if start and destination geocoding is needed
                if self.destinationAddress is None or self.startAddress is None:
                    with self._addressLookupLock:
                        if not self._startLookup and not self._destinationLookup:
                            self._geocodeStartAndDestination()

                if self.durationString:
                    duration = self.durationString # a string describing the estimated time to finish the route
                else:
                    duration = "? minutes"
                units = self.m.get('units', None) # get the correct units
                length = self.directions.length
                if length:
                    distance = units.m2CurrentUnitString(length, 1)
                else:
                    distance = "? km"
                steps = self.directions.message_point_count  # number of steps

                # TODO: do this cleaner with autowrap and elide

                if self.modrana.gui.portrait:
                    itemsPerLine = 2
                else:
                    itemsPerLine = 3

                if self.startAddress:
                    start = ""
                    index = 1
                    for item in self.startAddress.split(','):
                        if index%itemsPerLine: # add newline after every second item
                            start += " %s," % item
                        else:
                            start += "%s\n" % item
                        index+=1
                    start = start[1:-1]
                else:
                    start = "start address unknown"

                if self.destinationAddress:
                    destination = " \n\n\n"
                    index = 1
                    for item in self.destinationAddress.split(','):
                        if index%itemsPerLine: # add newline after every second item
                            destination += " %s," % item
                        else:
                            destination += "%s\n" % item
                        index+=1
                    # drop trailing ,
                    destination = destination[1:-1]
                else:
                    destination = "\ndestination address unknown"

                text = "%s" % start
                text += "%s" % destination
                text += "\n\n%s in about %s and %s steps" % (distance, duration, steps)
                if self.start and self.destination:
                    (lat1, lon1) = self.start.getLL()
                    (lat2, lon2) = self.destination.getLL()
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
        """Get the address of start and destination coordinates by using geocoding"""
        onlineModule = self.m.get('onlineServices', None)
        connectivity = (self.modrana.dmod.connectivityStatus in (constants.ONLINE, constants.CONNECTIVITY_UNKNOWN))
        if connectivity and onlineModule:
            # set that address lookups are in progress
            # (this function should be called from "inside" the address lookup lock)
            self._startLookup = True
            self._destinationLookup = True

            # start coordinates
            if self.start:
                start = self.start
            else:
                start = self.directions.get_point_by_index(0)
                # geocode start
            onlineModule.reverseGeocodeAsync(start, self._setStartAddressCB)

            # destination coordinates
            if self.destination:
                destination = self.destination
            else:
                destination = self.directions.get_point_by_index(-1)
            onlineModule.reverseGeocodeAsync(destination, self._setDestinationAddressCB)

    def _setStartAddressCB(self, results):
        """Set start address based on result from reverse geocoding

        :param results: list of results from reverse encoding
        :type results: a list of Point instances
        """
        if results:
            self.startAddress = results[0].description
        with self._addressLookupLock:
            self._startLookup = False
        # trigger route text update
        self.text = None
        self.set('needRedraw', True)

    def _setDestinationAddressCB(self, results):
        """Set destination address based on result from reverse geocoding

        :param results: list of results from reverse encoding
        :type results: a list of Point instances
        """
        if results:
            self.destinationAddress = results[0].description
        with self._addressLookupLock:
            self._destinationLookup = False
        # trigger route text update
        self.text = None
        self.set('needRedraw', True)
