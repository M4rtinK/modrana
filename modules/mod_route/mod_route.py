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
from core.point import Waypoint, TurnByTurnPoint
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
        self._go_to_initial_state()
        # how long the last routing lookup took in seconds
        self._route_lookup_duration = 0
        self._once = True
        self._entry = None

        # tracks the state of the onscreen routing menu
        self._osd_menu_state = None

        self.set('startPos', None)
        self.set('endPos', None)

        self._directions_filter_rules = []
        self._directions_filter_rules_loaded = False

        self._addressLookupLock = threading.Lock()
        self._startLookup = False
        self._destinationLookup = False

        # offline routing provider
        self._offline_routing_provider = None

        # signals
        self.routing_done = Signal()

    def _navigation_started_cb(self):
        self.notify("use at own risk, watch for cliffs, etc.", 3000)

    def _go_to_initial_state(self):
        """restorer initial routing state
        -> used in init and when rerouting"""
        self._pxpy_route = [] # route in screen coordinates
        self._directions = [] # directions object
        self.set('midText', [])
        self._duration_string = None # in seconds
        self._start = None
        self._destination = None
        self._start_address = None
        self._destination_address = None
        self._text = None
        self._text_portrait = None
        self._select_many_points = False
        # disable OSD menu
        self._osd_menu_state = None
        # discern between normal routing with waypoints
        # and handmade routing
        self._handmade = False
        self._select_two_points = False
        self._select_one_point = False

        self._expect_start = False
        self._expect_middle = False # handmade
        self._expect_end = False

        self._route_detail_geocoding_triggered = False

    @property
    def route_lookup_duration(self):
        return self._route_lookup_duration

    @property
    def directions_filter_rules(self):
        if not self._directions_filter_rules_loaded:
            self._load_directions_filter()
            # why not just check if _directionsFilterRules
        # is nonempty ?
        # -> the file might be empty or its loading might fail,
        # so if we checked just the rules list in such a case,
        # we would needlessly open the file over and over again
        return self._directions_filter_rules

    def _load_directions_filter(self):
        """Load direction filters from their CSV file"""
        start = time.time()
        f = open(DIRECTIONS_FILTER_CSV_PATH, 'r')
        CSVReader = csv.reader(f, delimiter=';', quotechar='|') #use an iterator
        self._directions_filter_rules = []
        for row in CSVReader:
            if row[0] != '#' and len(row) >= 2:
                regex = re.compile(u(row[0]))
                self._directions_filter_rules.append((regex, u(row[1])))
        f.close()
        self._directions_filter_rules_loaded = True
        self.log.debug("directions filter loaded in %1.2f ms", (time.time() - start) * 1000)

    def handleMessage(self, message, messageType, args):
        if message == "clear":
            self._go_to_initial_state()
            self.set('startPos', None)
            self.set('endPos', None)
            self.set('middlePos', []) # handmade

            # stop Turn-by-turn navigation, that can be possibly running
            self.sendMessage('turnByTurn:stop')

        elif message == 'expectStart':
            self._expect_start = True

        elif message == 'setStart':
            if self._select_one_point:
                self.set('endPos', None)
            proj = self.m.get('projection', None)
            if proj and self._expect_start:
                lastClick = self.get('lastClickXY', None)
                (x, y) = lastClick
                # x and y must be floats, otherwise strange rounding errors
                # occur when converting to lat lon coordinates
                (lat, lon) = proj.xy2ll(x, y)
                self.set('startPos', (lat, lon))
                self._start = Waypoint(lat, lon)
                self._destination = None # clear destination

            self._expect_start = False

        elif message == 'expectMiddle': # handmade
            self._expect_middle = True # handmade

        elif message == 'setMiddle': # handmade
            proj = self.m.get('projection', None)
            if proj and self._expect_middle:
                lastClick = self.get('lastClickXY', None)
                (x, y) = lastClick
                # x and y must be floats, otherwise strange rounding errors
                # occur when converting to lat lon coordinates
                (lat, lon) = proj.xy2ll(x, y)
                middle_pos = self.get('middlePos', [])
                middle_pos.append((lat, lon, None, ""))
                self.set('middlePos', middle_pos)
                # if in handmade input mode,
                # also ask for instructions for the given point
                if self._handmade:
                    self.sendMessage('route:middleInput')
            self._expect_middle = False

        elif message == 'expectEnd':
            self._expect_end = True

        elif message == 'setEnd':
            if self._select_one_point:
                self.set('startPos', None)
            proj = self.m.get('projection', None)
            if proj and self._expect_end:
                lastClick = self.get('lastClickXY', None)
                (x, y) = lastClick
                # x and y must be floats, otherwise strange rounding errors
                # occur when converting to lat lon coordinates
                (lat, lon) = proj.xy2ll(x, y)
                self.set('endPos', (lat, lon))
                self._destination = Waypoint(lat, lon)
                self._start = None # clear start

            self._expect_end = False

        elif message == "handmade":
            self.set('startPos', None)
            self.set('middlePos', [])
            self.set('endPos', None)
            self._select_one_point = False
            self._select_two_points = True
            self._select_many_points = True
            self._handmade = True
            self._osd_menu_state = OSD_EDIT
            self.log.info("Using handmade routing")
            self.log.info(self._handmade)

        elif message == "selectTwoPoints":
            self.set('startPos', None)
            self.set('endPos', None)
            self.set('middlePos', [])
            self._select_one_point = False
            self._select_two_points = True
            self._select_many_points = False
            self._osd_menu_state = OSD_EDIT

        elif message == "selectOnePoint":
            self.set('startPos', None)
            self.set('endPos', None)
            self.set('middlePos', [])
            self._select_two_points = True # we reuse the p2p menu
            self._select_one_point = True
            self._select_many_points = False
            self._osd_menu_state = OSD_EDIT

        elif message == "p2pRoute": # simple route, between two points
            destination = self.get("endPos", None)
            start = self.get("startPos", None)
            if destination and start:
                middle_points = self.get('middlePos', [])
                self.llRoute(start, destination, middle_points)

        elif message == "p2phmRoute": # simple route, from start to middle to end (handmade routing)
            start = self.get("startPos", None)
            destination = self.get("endPos", None)
            if start and destination:
                toLat, toLon = destination
                fromLat, fromLon = start
                middle_points = self.get("middlePos", [])
                self.log.info("Handmade route")
                self.log.info("%f,%f", fromLat, fromLon)
                self.log.info("through")
                self.log.info(middle_points)
                self.log.info("to %f,%f", toLat, toLon)
                handmade_route = Way.from_handmade(start, middle_points, destination)
                self._handle_routing_result_cb((handmade_route, "", 0))

        elif message == "p2posRoute": # simple route, from here to selected point
            start_pos = self.get('startPos', None)
            end_pos = self.get('endPos', None)
            pos = self.get('pos', None)
            start = None
            destination = None
            if pos is None: # well, we don't know where we are, so we don't know here to go :)
                return None

            if start_pos is None and end_pos is None: # we know where we are, but we don't know where we should go :)
                return None

            if start_pos is not None: # we want a route from somewhere to our current position
                start = start_pos
                destination = pos

            if end_pos is not None: # we go from here to somewhere
                start = pos
                destination = end_pos

            middle_points = self.get("middlePos", [])
            if start and destination:
                self.llRoute(start, destination, middle_points)

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
                            self.log.exception("exception during routing")
                        if "show" in args:
                            # switch to map view and go to start/destination, if requested
                            where = args['show']
                            if where == 'start':
                                self.sendMessage('mapView:recentre %f %f|set:menu:None' % start)
                            elif where == "destination":
                                self.sendMessage('mapView:recentre %f %f|set:menu:None' % destination)

            else: # simple route, from here to selected point
                # disable the point selection GUIs
                self._select_many_points = False # handmade
                self._select_two_points = False
                self._select_one_point = False
                self._osd_menu_state = OSD_CURRENT_ROUTE
                start = self.get("pos", None)
                destination = self.get("selectedPos", None)
                destination = [float(a) for a in destination.split(",")]
                if start and destination:
                    self.llRoute(start, destination)

        elif message == 'store_route':
            load_tracklogs = self.m.get('loadTracklogs', None)
            if load_tracklogs is None:
                self.log.error("can't store route without the load_tracklog module")
                return
            if not self._directions:
                self.log.info("the route is empty, so it will not be stored")
                return
            # TODO: rewrite this when we support more routing providers
            load_tracklogs.store_route_and_set_active(self._directions.points_lle,
                                                 '',
                                                 'online')

        elif message == "clearRoute":
            self._go_to_initial_state()

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
            start_address = self.get('startAddress', None)
            destination_address = self.get('destinationAddress', None)
            if start_address and destination_address:
                self.log.info("address routing")
                self.set('menu', None) # go to the map screen
                self.addressRoute(start_address, destination_address)
            else: # notify the user about insufficient input and remain in the menu
                self.log.error("can't route - start or destination (or both) not set")
                if start_address is None and destination_address is None:
                    self.notify("Can't route: start & destination not set", 3000)
                elif start_address is None:
                    self.notify("Can't route: start not set", 3000)
                elif destination_address is None:
                    self.notify("Can't route: destination not set", 3000)

        elif message == 'posToStart':
            pos = self.get('pos', None)
            if pos:
                posString = "%f,%f" % pos
                self._start_address = posString # set as current address
                self.set('startAddress', posString) # also store in the persistent dictionary

        elif message == 'posToDestination':
            pos = self.get('pos', None)
            if pos:
                posString = "%f,%f" % pos
                self._destination_address = posString # set as current address
                self.set('destinationAddress', posString) # also store in the persistent dictionary

        elif messageType == 'ms' and message == 'addressRouteMenu':
            if args == 'swap':
                # get current values
                start = self.get('startAddress', None)
                destination = self.get('destinationAddress', None)
                # swap them
                self.set('startAddress', destination)
                self.set('destinationAddress', start)
                # redraw the screen to show the change

        elif messageType == "ms" and message == "setOSDState":
            self._osd_menu_state = int(args)

    def reroute(self):
        """Reroute from current position to destination."""

        # is there a destination and valid position ?
        self.log.info("rerouting from current position to last destination")
        pos = self.get('pos', None)
        bearing = self.get('bearing', None)
        if self._destination and pos:
            start = Waypoint(lat=pos[0], lon=pos[1], heading=bearing)
            self.waypoints_route([start, self._destination])
            self._start = None

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
            route_params = self._get_default_route_parameters()
            # no custom route parameters provided, build default ones
            # based on current settings

        provider_id = self.get('routingProvider', constants.DEFAULT_ROUTING_PROVIDER)
        self.log.debug("routing provider ID: %s", provider_id)
        if provider_id in (constants.ROUTING_PROVIDER_MONAV_SERVER, constants.ROUTING_PROVIDER_MONAV_LIGHT):
            # is Monav initialized ? (lazy initialization)
            if self._offline_routing_provider is None:
                # instantiate the offline routing provider
                if provider_id == constants.ROUTING_PROVIDER_MONAV_LIGHT:
                    provider = routing_providers.MonavLightRouting(
                        monav_light_executable_path=self.modrana.dmod.monav_light_binary_path,
                        monav_data_path = self._get_monav_data_path()
                    )
                else:
                    provider = routing_providers.MonavServerRouting(
                        monav_server_executable_path=self.modrana.paths.monav_server_binary_path,
                        monav_data_path = self._get_monav_data_path()
                    )
                self._offline_routing_provider = provider

            # update the path to the Monav data folder
            # in the Monav wrapper in case in changed since last search
            self._offline_routing_provider.data_path = self._get_monav_data_path()

            # do the offline routing
            self._offline_routing_provider.searchAsync(
            callback,
            waypoints,
            route_params=route_params
        )
        elif provider_id == constants.ROUTING_PROVIDER_GOOGLE:
            provider = routing_providers.GoogleRouting()
            provider.searchAsync(
                callback,
                waypoints,
                route_params=route_params
            )
        elif provider_id == constants.ROUTING_PROVIDER_OSM_SCOUT:
            provider = routing_providers.OSMScoutServerRouting()
            provider.searchAsync(
                callback,
                waypoints,
                route_params=route_params
            )
        else:
            self.log.error("unknown routing provider ID: %s", provider_id)


    def _get_default_route_parameters(self):
        mode = self.get("mode", "car")
        route_mode = constants.ROUTE_CAR
        lang_code = self.get("directionsLanguage", "en en")
        # the (Google) language code is the second part of
        # this whitespace delimited string
        lang_code = lang_code.split(" ")[1]
        if self.modrana.gui.getIDString() == "GTK":
            if mode == "walk":
                route_mode = constants.ROUTE_PEDESTRIAN
            elif mode == "cycle":
                route_mode = constants.ROUTE_BIKE
        elif self.modrana.gui.getIDString() == "Qt5":
            # the Qt 5 GUI currently does not use an application wide
            # mode concept and sets the routing mode separately
            route_mode = self.get("routingModeQt5", constants.ROUTE_CAR)
        route_params = routing_providers.RouteParameters(
            routeMode=route_mode,
            avoidTollRoads=self.get("routingAvoidToll", False),
            avoidHighways=self.get("routingAvoidHighways", False),
            language = lang_code
        )
        return route_params

    def llRoute(self, start, destination, middlePoints=None):
        if not middlePoints: middlePoints = []

        # tuples -> Points
        start = Waypoint(*start)
        destination = Waypoint(*destination)

        # list of tuples -> list of Points
        #middlePoints = list(map(lambda x: Point(x[0], x[1]), middlePoints))
        waypoints = [start]
        for mpTuple in middlePoints:
            waypoints.append(Waypoint(mpTuple[0], mpTuple[1]))
        waypoints.append(destination)
        self.log.info("Routing %s to %s through %d waypoints",
              start, destination, len(middlePoints))
        # TODO: wait message (would it be needed when using internet routing ?)
        self._do_route(waypoints)

    def waypoints_route(self, waypoints):
        """Request a route following a list of waypoints."""
        self._do_route(waypoints)

    def addressRoute(self, start, destination):
        """Route from one address to another, and set the result as the active route
        NOTE: both address string and plaintext geographic coordinates can be used

        :param start: starting address
        :type start: str
        :param destination: destination address
        :type destination: str
        """
        # cleanup any possible previous routes
        self._go_to_initial_state()
        self.log.info("Address-routing from %s to %s", start, destination)
        waypoints = [start, destination]
        # specify that this route lookup should expect start and destination
        # specified as address strings
        params = self._get_default_route_parameters()
        params.addressRoute = True
        self.routeAsync(self._handle_routing_result_cb, waypoints, route_params=params)

    def _do_route(self, waypoints):
        """Route from one point to another"""

        # clear old addresses
        self._start_address = None
        self._destination_address = None
        # the new result would probably have different start and destination coordinates
        self._route_detail_geocoding_triggered = False

        #TODO: respect offline mode and automatically
        # use offline routing methods
        # TODO: notify user if no offline routing data is available for the current area

        # set start and destination based on waypoints
        if waypoints:
            self._start = waypoints[0]
            self._destination = waypoints[-1]

        self.routeAsync(self._handle_routing_result_cb, waypoints)

    def _handle_routing_result_cb(self, result):
        # remove any previous route description
        self._text = None
        # trigger the routing done signal
        self.routing_done(result)

        if result.route and result.returnCode == constants.ROUTING_SUCCESS:
            # process and save routing results
            self._route_lookup_duration = result.lookupDuration
            self.log.info("routing finished succesfully in %1.2f s", self._route_lookup_duration)

            # set start and destination
            start = result.route.get_point_by_index(0)
            start = Waypoint(start.lat, start.lon)
            # make sure start and destination are waypoints or else
            # rerouting will fail
            destination = result.route.get_point_by_index(-1)
            destination = Waypoint(destination.lat, destination.lon)
            # use coordinates for start dest or use first/last point from the route
            # if start/dest coordinates are unknown (None)
            if self._start is None:
                self._start = start
            if self._destination is None:
                self._destination = destination

            self._osd_menu_state = OSD_CURRENT_ROUTE

            # do the GTK GUI specific stuff only when running with GTK GUI
            if self.modrana.gui.getIDString() == "GTK":
                # save a copy of the route in projection units for faster drawing
                proj = self.m.get('projection', None)
                if proj:
                    self._pxpy_route = [proj.ll2pxpyRel(x[0], x[1]) for x in result.route.points_lle]
                self.process_and_save_directions(result.route)
                self._osd_menu_state = OSD_CURRENT_ROUTE
                self.start_navigation()

        else: # routing failed
            self.log.error("routing ended with error")
            if result.errorMessage:
                error_message = result.errorMessage
            else:
                error_message = constants.ROUTING_FAILURE_MESSAGES.get(result.returnCode, "Routing failed.")
            self.log.error("routing error message: %s", error_message)
            self.notify(error_message, 3000)

    def get_available_monav_data_packs(self):
            """Return all available Monav data packs in the main monav data folder

            :return: list of all packs in Monav data folder
            :rtype: a list of strings
            """
            # basically just list all directories in the Monav data folder
            try:
                main_monav_folder = self.modrana.paths.monav_data_path
                data_packs = os.listdir(main_monav_folder)
                data_packs = filter(lambda x: os.path.isdir(os.path.join(main_monav_folder, x)), data_packs)
                return sorted(data_packs)
            except Exception:
                self.log.exception('listing the Monav data packs failed')
                return []

    def _get_monav_data_path(self):
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
        sub_folder = modeFolders.get(mode, 'routing_car')
        data_packs = self.get_available_monav_data_packs()
        if data_packs:
            # TODO: bounding box based pack selection
            preferred_pack = self.get('preferredMonavDataPack', None)
            if preferred_pack in data_packs:
                pack_name = preferred_pack
            else:
                # just take the first (and possibly only) pack
                pack_name = sorted(data_packs)[0]
                self.log.info("monav: no preferred pack set, "
                      "using first available:\n%s", preferred_pack)
            main_monav_folder = self.modrana.paths.monav_data_path
            monav_data_folder = os.path.abspath(os.path.join(main_monav_folder, pack_name, sub_folder))
            self.log.info('Monav data folder:\n%s', monav_data_folder)
            return monav_data_folder
        else:
            return None

    def start_navigation(self):
        """handle navigation autostart"""
        autostart = self.get('autostartNavigationDefaultOnAutoselectTurn', 'enabled')
        if autostart == 'enabled':
            self.sendMessage('ms:turnByTurn:start:%s' % autostart)

    def process_and_save_directions(self, route):
        """process and save directions"""

        # apply filters
        route = self.filter_directions(route)

        # add a fake destination step, so there is a "destination reached" message
        if route.point_count > 0:
            (lat, lon) = route.get_point_by_index(-1).getLL()
            dest_step = TurnByTurnPoint(lat, lon)
            dest_step.ssml_message = '<p xml:lang="en">you <b>should</b> be near the destination</p>'
            dest_step.description ='you <b>should</b> be near the destination'
            dest_step.distance_from_start = route.length
            # TODO: make this multilingual
            # add it to the end of the message point list
            route.add_message_point(dest_step)

        # save
        self._directions = route

    def get_directions(self):
        return self._directions

    def filter_directions(self, directions):
        """
        filter directions according to substitution rules (specified by a CSV file)
        -> mostly used to replace abbreviations by full words in espeak output
        -> also assure Pango compatibility (eq. get rid of  <div> and company)
        """
        steps = directions.message_points

        for step in steps:
            original_message = "".join(str(step.description))
            message = ""
            try:
                message = step.description #TODO: make a method for this
                message = re.sub(r'<div[^>]*?>', '\n<i>', message)
                message = re.sub(r'</div[^>]*?>', '</i>', message)
                message = re.sub(r'<wbr/>', ', ', message)
                message = re.sub(r'<wbr>', ', ', message)
                step.description = message
                # special processing of the original message for Espeak
                message = original_message

                # check if cyrillic -> russian voice is enabled
                cyrillic_voice = self.get('voiceNavigationCyrillicVoice', 'ru')
                if cyrillic_voice:
                    message = self._process_cyrillic_string(message, cyrillic_voice)

                message = re.sub(r'<div[^>]*?>', '<br>', message)
                message = re.sub(r'</div[^>]*?>', '', message)
                message = re.sub(r'<b>', '<emphasis level="strong">', message)
                message = re.sub(r'</b>', '</emphasis>', message)

                # apply external rules from a CSV file
                for (regex, replacement) in self.directions_filter_rules:
                    # replace strings according to the csv file
                    message = regex.sub(replacement, message, re.UNICODE)
                step.ssml_message = message
            except Exception:
                self.log.exception("error during direction filtering")
                step.ssml_message = message

        # replace old message points with new ones
        directions.clear_message_points()
        directions.add_message_points(steps)

        return directions

    def _process_cyrillic_string(self, inputString, voiceCode):
        """test if a given string contains any words with cyrillic characters
        if it does, tell espeak (by adding a sgml tag) to speak such words
        using voiceCode"""
        substrings = inputString.split(' ')
        output_string = ""
        cyrillic_string_temp = ""
        for substring in substrings: # split the message to words
            cyrillic_char_found = False
            # test if the word has any cyrillic characters (a single one is enough)
            for character in substring:
                try: # there are probably some characters that dont have a known name
                    unicode_name = unicodedata.name(u(character))
                    if unicode_name.find('CYRILLIC') != -1:
                        cyrillic_char_found = True
                        break
                except Exception:
                    import sys
                    # just skip this as the character is  most probably unknown
                    pass
            if cyrillic_char_found: # the substring contains at least one cyrillic character
                if cyrillic_string_temp: # append to the already "open" cyrillic string
                    cyrillic_string_temp += ' ' + substring
                else: # create a new cyrillic string
                    # make espeak say this word in russian (or other voiceCode),
                    # based on Cyrillic being detected in it
                    cyrillic_string_temp = '<p xml:lang="%s">%s' % (voiceCode, substring)

            else: # no cyrillic found in this substring
                if cyrillic_string_temp: # is there an "open" cyrillic string ?
                    cyrillic_string_temp += '</p>'# close the string
                    # store it and the current substring
                    output_string += ' ' + cyrillic_string_temp + ' ' + substring
                    cyrillic_string_temp = ""
                else: # no cyrillic string in progress
                    # just store the current substring
                    output_string = output_string + ' ' + substring
                    # cleanup
        if cyrillic_string_temp: #is there an "open" cyrillic string ?
            cyrillic_string_temp += '</p>' # close the string
            output_string += ' ' + cyrillic_string_temp
        return output_string

    def get_current_directions(self):
        """return the current route"""
        return self._directions


    def _geocodeStartAndDestination(self):
        """Get the address of start and destination coordinates by using geocoding"""
        online_module = self.m.get('onlineServices', None)
        connectivity = (self.modrana.dmod.connectivity_status in (constants.ONLINE, constants.CONNECTIVITY_UNKNOWN))
        if connectivity and online_module:
            # set that address lookups are in progress
            # (this function should be called from "inside" the address lookup lock)
            self._startLookup = True
            self._destinationLookup = True

            # start coordinates
            if self._start:
                start = self._start
            else:
                start = self._directions.get_point_by_index(0)
                # geocode start
            online_module.reverseGeocodeAsync(start, self._setStartAddressCB)

            # destination coordinates
            if self._destination:
                destination = self._destination
            else:
                destination = self._directions.get_point_by_index(-1)
            online_module.reverseGeocodeAsync(destination, self._set_destination_address_cb)

    def _setStartAddressCB(self, results):
        """Set start address based on result from reverse geocoding

        :param results: list of results from reverse encoding
        :type results: a list of Point instances
        """
        if results:
            self._start_address = results[0].description
        with self._addressLookupLock:
            self._startLookup = False
        # trigger route text update
        self._text = None

    def _set_destination_address_cb(self, results):
        """Set destination address based on result from reverse geocoding

        :param results: list of results from reverse encoding
        :type results: a list of Point instances
        """
        if results:
            self._destination_address = results[0].description
        with self._addressLookupLock:
            self._destinationLookup = False
        # trigger route text update
        self._text = None
