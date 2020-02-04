# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# ModRana startup handling
# * parse startup arguments
# * load device module
# * load GUI module
#----------------------------------------------------------------------------
# Copyright 2012, Martin Kolman
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
import sys
import time

import logging
log = logging.getLogger("core.startup")

from core import modrana_log

try:
    import argparse
except ImportError:
    import core.backports.argparse as argparse

LOCAL_SEARCH_LOCATION_TIMEOUT = 30 # in seconds

# error codes
SYNTAX_ERROR = 2
SEARCH_NO_RESULTS_FOUND = 3
SEARCH_PROVIDER_TIMEOUT_ERROR = 4
SEARCH_PROVIDER_ERROR = 5
LOCAL_SEARCH_CURRENT_POSITION_UNKNOWN_ERROR = 6
CURRENT_POSITION_UNKNOWN_ERROR = 7
COORDINATE_PARSING_ERROR = 8

USE_LAST_KNOWN_POSITION_KEYWORD = "LAST_KNOWN_POSITION"

POI_SUBCOMMAND = "poi"

SUBCOMMAND_LIST = [POI_SUBCOMMAND]

SUBCOMMANDS = set(SUBCOMMAND_LIST)

class Startup(object):
    def __init__(self, modrana):
        self.modrana = modrana
        self.originalStdout = None
        self.originalStderr = None
        self._subcommand_present = len(sys.argv) >= 2 and sys.argv[1] in SUBCOMMANDS
        self._poi_subcommand_present = False
        current_subcommands = ",".join(SUBCOMMAND_LIST)
        parser = argparse.ArgumentParser(description="A flexible GPS navigation system.",
                                         epilog="You can also use the following subcommands: [%s] \
                                                 To see what a subcommand does use <subcommand> --help, \
                                                 EXAMPLE: poi --help" % current_subcommands)
        # device
        parser.add_argument(
            '-d', metavar="device ID", type=str,
            help="specify device type",
            default=None, action="store",
            choices=self.modrana._list_available_device_modules_by_id()
        )
        # GUI
        parser.add_argument(
            '-u', metavar="GUI ID", type=str,
            help='specify user interface type (qt5)',
            default=None,
            action="store"
        )
        # local search
        parser.add_argument(
            '--local-search', metavar='search query', type=str,
            help='specify a local search query EXAMPLE: "pizza"',
            default=None,
            action="store"
        )
        # local search location
        parser.add_argument(
            '--local-search-location', metavar='an address or geographic coordinates', type=str,
            help='specify a geographic location for a local search query '
                 '(current location is used by default), both addresses and'
                 ' geographic coordinates with the geo: prefix are supported;'
                 ' use "%s" to use last known position '
                 'EXAMPLE: "London" or "geo:50.083333,14.416667" or "%s"' % (
                     USE_LAST_KNOWN_POSITION_KEYWORD, USE_LAST_KNOWN_POSITION_KEYWORD)
            ,
            default=None,
            action="store"
        )
        # address search
        parser.add_argument(
            '--address-search', metavar='an address', type=str,
            help='specify an address search query EXAMPLE: "Baker Street 221b, London"',
            default=None,
            action="store"
        )
        # wikipedia search
        parser.add_argument(
            '--wikipedia-search',
            metavar='search query',
            type=str,
            help='specify a local search query EXAMPLE: "Prague castle"',
            default=None,
            action="store"
        )


        # return static map url & shutdown
        parser.add_argument(
            '--return-static-map-url',
            help='return static map URL for a CLI query (works for local search, address and Wikipedia search)',
            action="store_true"
        )
        # return current coordinates
        parser.add_argument(
            '--return-current-coordinates',
            help='return current coordinates: latitude,longitude[,elevation] EXAMPLE: 1.23,4.5,600 or 1.23,4.5',
            default=None,
            action="store_true"
        )
        # enable centering on startup
        parser.add_argument(
            '--center-on-position',
            help='focus on the current position & enable centering',
            default=None,
            action="store_true"
        )
        # set zoom level
        parser.add_argument(
            '--set-zl',
            help='set a zoom level EXAMPLE: 15',
            metavar="zoom level number",
            type=int,
            default=None,
            action="store"
        )
        # enable centering and set zoom level
        parser.add_argument(
            '--center-on-position-on-zl',
            help='focus on current position on a given zoom level EXAMPLE: 15',
            metavar="zoom level number",
            type=int,
            default=None,
            action="store"
        )
        # enable centering and set zoom level
        parser.add_argument(
            '--focus-on-coordinates',
            help='focus on given coordinates, NOTE you can use --set-zl to set zoom level, EXAMPLE: "geo:50.083333,14.416667"'
            ,
            metavar="geographic coordinates with the geo: prefix",
            type=str,
            default=None,
            action="store"
        )
        # startup debugging - don't disable stdout
        parser.add_argument(
            '--debug-startup',
            help="startup debugging - don't disable stdout",
            default=None,
            action="store_true"
        )
        # start in fullscreen
        parser.add_argument(
            '--fullscreen',
            help="start in fullscreen",
            default=None,
            action="store_true"
        )

        # subcommands
        #
        # As argparse does not support support optional subcommands
        # (non-optional subcommands would preclude running modrana without arguments
        #  or with the current optional arguments), so only register subcommands if
        # they are spotted in sys.argv. Like this the subcommands don't show up in the
        # automatically generated help, which we workaround by mentioning the available
        # subcommands in the epilog.
        # Handling subcommands like this also has the benefit of skipping all the subcommand
        # setup code when the subcommand is not actually needed a even if a subcommand is
        # spotted only a single subcommand is setup, not all of them.

        if self._subcommand_present:
            subcommand = sys.argv[1]
            if subcommand == POI_SUBCOMMAND:
                # poi subcommand
                self._poi_subcommand_present = True
                subcommands = parser.add_subparsers()
                poi = subcommands.add_parser("poi", help="Points of Interest handling")
                poi.required = False
                poi_subcommands = poi.add_subparsers(dest="poi_subcommand")
                # add
                poi_add = poi_subcommands.add_parser("add", help='add a POI to the database')
                poi_add.add_argument(type=str, dest="poi_add_coords", default=None, nargs="?",
                                     help='geographic coordinates with the geo: prefix, EXAMPLE: "geo:50.083333,14.416667"')
                poi_add.add_argument("--name", type=str, dest="poi_name",
                                     help='POI name, EXAMPLE: "Baker Street 221b, London"')
                poi_add.add_argument("--description", type=str,  dest="poi_description",
                                     help='POI name, EXAMPLE: "The house of Sherlock Holmes."')
                poi_add.add_argument("--category", type=str, dest="poi_category", default="Other",
                                         help='POI category name or index (default: 11/Other), EXAMPLE: "Landmark" or "10"')
                # list-categories
                poi_subcommands.add_parser("list-categories", help='list POI database categories')

        self.args, _unknownArgs = parser.parse_known_args()


    def getArgs(self):
        """return parsed CLI arguments"""
        return self.args

    def handleEarlyTasks(self):
        """Handle CLI arguments that can be handled before the general modRana startup
        -> this usually means some "simple" tasks that return some results to
            standard output and then shut-down modRana
        EX.: do an address search, return static map URL and quit
        """
        # if any of those argument combinations are specified,
        # we need to disable stdout, or else regular modRana
        # startup will spam the CLI output
        if self.args.return_static_map_url:
            if self.args.local_search or \
            self.args.address_search is not None or \
            self.args.wikipedia_search is not None:
                self._disableStdout()
        elif self.args.return_current_coordinates:
            self._disableStdout()
        elif self._poi_subcommand_present:
            self._disableStdout()

    def handle_non_gui_tasks(self):
        """Handle CLI arguments that can be handled before the general modRana startup,
        but require a loaded device module
        -> this usually means some "simple" tasks that return some results to
            standard output and then shut-down modRana
        EX.: do an address search, return static map URL and quit
        """
        if self.args.return_static_map_url:
            # the early local search only quickly returns a static map url without loading most of modRana
            if self.args.local_search is not None:
                self._earlyLocalSearch()
            elif self.args.address_search is not None:
                self._earlyAddressSearch()
            elif self.args.wikipedia_search is not None:
                self._earlyWikipediaSearch()
        elif self.args.return_current_coordinates:
            self._earlyReturnCoordinates()
        elif self._poi_subcommand_present:
            if self.args.poi_subcommand == "add":
                self._addPOI()
            elif self.args.poi_subcommand == "list-categories":
                self._listCategories()

    def handlePostFirstTimeTasks(self):
        """
        handle CLI arguments that should take effect once modrana is fully stared
        EX.: do an address search and display the results inside modRana
        """
        # set zoom level
        if self.args.set_zl is not None:
            self.modrana.set("z", self.args.set_zl)

        #** following options are mutually exclusive **

        # center on current position on a zoom-level
        if self.args.center_on_position_on_zl is not None:
            z = self.args.center_on_position_on_zl
            self.modrana.set("z", z)
            self.modrana.set("centred", True)
            # make sure the map screen is displayed
            self.modrana.set("menu", None)
        elif self.args.focus_on_coordinates is not None:
            self._focusOnCoords()
        elif self.args.local_search is not None:
            self._localSearch()
        elif self.args.address_search is not None:
            self._addressSearch()
        elif self.args.wikipedia_search is not None:
            self._wikipediaSearch()


    def _focusOnCoords(self):
        """focus on coordinates provided by CLI"""
        log.info("focusing on CLI-provided coordinates")

        # try to parse the coordinates
        try:
            coords = self.args.focus_on_coordinates
            # split off the geo prefix
            split1 = str.lower(coords).split("geo:")
            if len(split1) >= 2:
                # split to coordinates:
                split2 = split1[1].split(",")
                if len(split2) >= 2:
                    lat = float(split2[0])
                    lon = float(split2[1])
                    log.info("focusing on %f %f", lat, lon)
                    # disable centering & show the map screen
                    self.modrana.set("menu", None)
                    self.modrana.set("centred", False)
                    # send the map focusing message
                    message = "mapView:recentre %f %f" % (lat, lon)
                    self._sendMessage(message)
                else:
                    log.error("parsing coordinates for the --focus-on-coordinates option failed")
                    log.error("unknown coordinate format: %s", split1[1])
            else:
                log.error("parsing coordinates for the --focus-on-coordinates option failed")
                log.error("missing geo: prefix")

            # make sure centering is disabled
            self.modrana.set("centred", False)
        except Exception:
            log.exception("parsing coordinates for the --focus-on-coordinates option failed with exception")

    def _getLocalSearchLocation(self):
        location = self.args.local_search_location
        if location is not None:
            return location.strip() # remove leading & trailing whitespace
        else:
            return location

    def _earlyLocalSearch(self):
        """handle CLI initiated local search that returns a static map URL"""
        # for local search, we need to know our position, so we need at least the
        # location module and of also of course the online services module to do the search

        self._disableStdout()

        # local search need Internet connectivity, trigger
        # Internet initialization now, the search function decorator
        # will wait for it to finish
        self.modrana.dmod.enable_internet_connectivity()

        # load the online services module
        online = self.modrana._load_module("mod_onlineServices", "onlineServices")

        query = self.args.local_search
        points = [] # points defining the result/s

        # now check if a location for the local search was provided from CLI or if we need to find our location
        # using GPS or equivalent

        from core.point import Point

        location = self._getLocalSearchLocation()
        if location is not None:
            # we use the location provided from CLI, no need to load & start location
            if self._useLastKnownPos(location):
                # get last known position (if any)
                pos = self._getCurrentPosition(loadLocationModule=True, useLastKnown=True)
                if pos is None:
                    self._enableStdout()
                    log.error("no last known position available")
                    # done - no position found
                    self._exit(LOCAL_SEARCH_CURRENT_POSITION_UNKNOWN_ERROR)
                else:
                    lat, lon = pos
                    # replace the use-last-known flag with the actual location
                    location = Point(lat, lon)
        else:
            # we need to determine our current location - the location module needs to be loaded & used
            pos = self._getCurrentPosition(loadLocationModule=True)
            if pos is not None:
                lat, lon = pos
                location = Point(lat, lon)
            else:
                # done - no position found
                self._exit(LOCAL_SEARCH_CURRENT_POSITION_UNKNOWN_ERROR)

        # do the search
        points = online.localSearch(query, location)

        # local search results processing
        self._returnStaticMapUrl(points, online)

    def _earlyAddressSearch(self):
        """search for address and return a static map URL for the result/s"""
        self._disableStdout()
        query = self.args.address_search
        # load the online services module
        online = self.modrana._load_module("mod_onlineServices", "onlineServices")
        results = online.geocode(query)
        self._returnStaticMapUrl(results, online)

    def _earlyWikipediaSearch(self):
        """search Wikipedia and return a static map URL for the result/s"""
        self._disableStdout()
        query = self.args.wikipedia_search
        # load the online services module
        online = self.modrana._load_module("mod_onlineServices", "onlineServices")
        results = online.wikipediaSearch(query)
        self._returnStaticMapUrl(results, online)

    def _earlyReturnCoordinates(self):
        """return current coordinates (latitude, longitude, elevation) & exit"""
        self._disableStdout()
        # we need to determine our current location - the location module needs to be loaded & used
        pos = self._getCurrentPosition(loadLocationModule=True, useLastKnown=False)
        if pos is not None:
            lat, lon = pos
            elev = self.modrana.get('elevation', None)
            if self.modrana.get('fix', None) == 3 and elev:
                output = "%f,%f,%f" % (lat, lon, elev)
            else:
                output = "%f,%f" % (lat, lon)
            self._enableStdout()
            print(output)
            self._exit(0)
        else:
            # done - no position found
            self._exit(CURRENT_POSITION_UNKNOWN_ERROR)

    # POI

    def _find_category(self, store_poi, cat_spec):
        """Try to match the cat_spec to a POI category.
           The category specification is expected to be either an integer index
           or a category name.

           :param str cat_cat_spec: category specification
           :returns: category index, category name or None, None if cat_spec can't be matched to a category
           :rtype: tuple
        """
        try:
            # first try converting the spec to the integer index
            result = store_poi.db.get_category_from_index(int(cat_spec))
        except ValueError:
            # next try to fetch category for the name
            result = store_poi.db.get_category_from_name(cat_spec)
        if result:  # category found
            cat_id, cat_name, _desc, _enabled = result
            return cat_id, cat_name
        else:  # category not found
            return None, None

    def _addPOI(self):
        """Add a poi to the database"""
        self._disableStdout()
        from core import geo
        coords = geo.parse_geo_coords(self.args.poi_add_coords)
        if coords is None:
            self._enableStdout()
            print("coordinate format parsing failed, should be: geo:latitude,longitude")
            self._exit(COORDINATE_PARSING_ERROR)
        else:
            from core.point import POI
            lat, lon = coords
            store_poi = self.modrana._load_module("mod_storePOI", "storePOI")
            cat_id, cat_name = self._find_category(store_poi, self.args.poi_category)
            if cat_id is None:
                self._enableStdout()
                print("invalid category specification (%s), falling back to default (%s)" %
                      (self.args.poi_category, "Other"))
                self._disableStdout()
                cat_id = 11
                cat_name = "Other"

            poi = POI(lat=lat, lon=lon, name=self.args.poi_name,
                      description=self.args.poi_description,
                      db_cat_id=cat_id)
            store_poi.db.store_poi(poi)
            self._enableStdout()
            print("point added to the modRana POI database (category: %d/%s)" % (cat_id, cat_name))
            self._exit(0)

    def _listCategories(self):
        """List POI database categories"""
        self._disableStdout()
        store_poi = self.modrana._load_module("mod_storePOI", "storePOI")
        categories = store_poi.db.list_categories()
        self._enableStdout()
        for name, description, index in categories:
            print("%d, %s, %s" % (index, name, description))
        self._exit(0)

    def _returnStaticMapUrl(self, results, online):
        """return static map url for early search methods & exit"""
        if results:
            if self.args.set_zl is not None:
                zl = self.args.set_zl
            else:
                zl = 15 # sane default ?
                # for now we just take the first result
            result = results[0]
            lat, lon = result.getLL()
            markerList = [(lat, lon)]
            url = online.getOSMStaticMapUrl(lat, lon, zl, markerList=markerList)
            self._enableStdout()
            print(url)
            # done - success
            self._exit(0)
        else:
            self._enableStdout()
            log.info("search returned no results")
            self._exit(SEARCH_NO_RESULTS_FOUND)

    def _localSearch(self):
        """CLI initiated online local search that displays the result inside modRana"""
        log.info("searching for CLI-provided query")
        query = self.args.local_search

        # try to make sure Internet connectivity is available
        # -> Internet is needed for a quick fix & the search itself
        # -> if the device is offline, it might need this "nudge"
        # to reconnect
        self.modrana.dmod.enable_internet_connectivity()

        # check if location was provided from CLI
        if self.args.local_search_location is not None:
            location = self.args.local_search_location
            if self._useLastKnownPos(location):
                pos = self._getCurrentPosition(useLastKnown=True)
                if pos is None:
                    log.warning("no last known position")
                    self._sendMessage("ml:notification:m:No last known position;5")
                else:
                    lat, lon = pos
                    self._sendMessage("ml:search:localSearch:coords;%f;%f;%s" % (lat, lon, query))
            else:
                self._sendMessage("ml:search:localSearch:location;%s;%s" % (location, query))
        else: # determine current location and then do the search
            self._sendMessage("ml:search:localSearch:position;%s" % query)

    def _addressSearch(self):
        """CLI initiated online address search, that shows results inside modRana"""
        # try to make sure Internet connectivity is available
        # -> Internet is needed for a quick fix & the search itself
        # -> if the device is offline, it might need this "nudge"
        # to reconnect

        log.info("searching where is the CLI-provided address")
        query = self.args.address_search
        message = "ml:search:search:address;%s" % query
        self._sendMessage(message)

    def _wikipediaSearch(self):
        """CLI initiated online Wikipedia search, that shows results inside modRana"""
        # try to make sure Internet connectivity is available
        # -> Internet is needed for a quick fix & the search itself
        # -> if the device is offline, it might need this "nudge"
        # to reconnect

        log.info("searching Wikipedia for CLI-provided query")
        query = self.args.wikipedia_search
        message = "ml:search:search:wikipedia;%s" % query
        self._sendMessage(message)

    def _sendMessage(self, message):
        m = self.modrana.m.get("messages")
        if m:
            m.sendMessage(message)

    def _fixCB(self, key, newValue, oldValue, startTimestamp, location):
        """checks for fix and terminates the location & mainloop once
        either a valid fix is established or once the timeout is reached"""
        log.info('fix value: %d', newValue)
        stop = False
        # wait for 3D lock for up to 30 seconds
        if time.time() - startTimestamp > 30:
            log.error('fix timed out')
            stop = True
        elif newValue == 3: # 3 = 3D lock
            log.info("3D fix established")
            stop = True
        if stop:
        # quite the main loop so that _getCurrentPosition can finish
        #      main.quit()
            location.stop_location()

    def _getCurrentPosition(self, loadLocationModule=False, useLastKnown=False):
        """get current position on a system in early startup state"""

        # do we need to load the location module ?
        # we usually need to load it if we handle an early task that happens before regular startup
        if loadLocationModule:
            # load the location module
            l = self.modrana._load_module("mod_location", "location")
            # register fix CB
            self.modrana.watch('fix', self._fixCB, [time.time(), l])
            log.info('location module loaded')
            # start location
            l.start_location(start_main_loop=True)
            log.info('location started')
        else:
            l = self.modrana.m.get("location", None)

        # calling l.start_location(startMainLoop=True) will start the
        # main loop and block the execution of this function until the
        # main loop is killed by the fix watch
        #
        # the fix watch will kill the main loop once a 3D fix is
        # established or once it times out,
        # then the rest of the code in this function will be executed

        fix = self.modrana.get('fix', None)
        if fix in (2, 3):
            pos = self.modrana.get('pos', None)
        else:
            pos = None # timed out without finding position

        #    pos = None
        #    if l and not useLastKnown:
        #      timeout = 0
        #      checkInterval = 0.1 # in seconds
        #      print("startup: trying to determine current position for at most %d s" % LOCAL_SEARCH_LOCATION_TIMEOUT)
        #      while timeout <= LOCAL_SEARCH_LOCATION_TIMEOUT:
        #        if self.modrana.dmod.location_type() in ("gpsd", "liblocation"):
        #          # GPSD and liblocation need a nudge
        #          # to update the fix when the GUI mainloop is not running
        #          #self.modrana.dmod._libLocationUpdateCB()
        #          print(self.modrana.dmod.lDevice.online)
        #          print(self.modrana.dmod.lDevice.status)
        #          print(self.modrana.dmod.lDevice.satellites_in_view)
        #          print(self.modrana.dmod.lDevice.fix)
        #        if l.provider:
        #          pos = l.provider.getFix().position
        #        else:
        #          pos = self.modrana.get('pos', None)
        #        print(pos)
        #        if pos is not None:
        #          break
        #
        #        timeout+=checkInterval
        #        time.sleep(checkInterval)

        if loadLocationModule:
        # properly stop location when done (for early tasks)
            l.stop_location()

        if pos is None: # as a last resort, try last known position, if available
            if not useLastKnown:
                log.warning("current position unknown")
            else:
                log.info("using last known position")
                # we might need to load options "manually" if run early
                if not self.modrana.optLoadingOK:
                    self._loadOptions()

                pos = self.modrana.get("pos", None)
                if pos is None:
                    log.warning("no last known position")

        return pos


    def _enableStdout(self):
        """enable stdout output"""
        if self.originalStdout:
            sys.stdout = self.originalStdout
            self.originalStdout = None

        if self.originalStderr:
            sys.stderr = self.originalStderr
            self.originalStderr = None

        # re-enable logging to stdout
        modrana_log.log_manager.enableStdoutLog()

    def _disableStdout(self):
        """disable stdout output
        -> this is mainly used for CLI processing so that modRanas status messages don't get into the output
        that will be parsed by outside programs or scripts
        """
        # if startup debugging is enabled, don't disable stdout
        if self.args.debug_startup:
            return

        if self.originalStdout is None:
            self.originalStdout = sys.stdout
            sys.stdout = self

        if self.originalStderr is None:
            self.originalStderr = sys.stderr
            sys.stdout = self

        # also disable output to stdout from our logging infrastructure
        modrana_log.log_manager.disableStdoutLog()

    def write(self, s):
        """a write function that does nothing for stdout redirection"""
        pass

    def _loadOptions(self):
        """load the persistent options (for usage by early tasks)"""
        from core import paths
        # options needs the paths class to know from where to load the options
        self.modrana.paths = paths.Paths(self.modrana)
        self.modrana._load_options()

    def _useLastKnownPos(self, location):
        return str.strip(location) == USE_LAST_KNOWN_POSITION_KEYWORD

    def _exit(self, errorCode=0):
        sys.exit(errorCode)

