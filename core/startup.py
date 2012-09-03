#!/usr/bin/python
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

import core.argparse as argparse

LOCAL_SEARCH_LOCATION_TIMEOUT = 30 # in seconds

# error codes
SYNTAX_ERROR = 2
SEARCH_NO_RESULTS_FOUND = 3
SEARCH_PROVIDER_TIMEOUT_ERROR = 4
SEARCH_PROVIDER_ERROR = 5
LOCAL_SEARCH_CURRENT_POSITION_UNKNOWN_ERROR = 6

USE_LAST_KNOWN_POSITION_KEYWORD = "LAST_KNOWN_POSITION"

class Startup:
  def __init__(self, modrana):
    self.modrana = modrana
    self.originalStdout = None
    parser = argparse.ArgumentParser(description="A flexible GPS navigation system.")
    # device
    parser.add_argument(
      '-d', metavar="device ID", type=str,
      help="specify device type",
      default=None, action="store",
      choices=["neo","pc", "n900", "n9", "q7", "android_chroot"]
    )
    # GUI
    parser.add_argument(
      '-u', metavar="GUI ID", type=str,
      help='specify user interface type (GTK or QML)',
      default=None,
      action="store",
      choices=["GTK", "QML"]
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
           'EXAMPLE: "London" or "geo:50.083333,14.416667" or "%s"' % (USE_LAST_KNOWN_POSITION_KEYWORD, USE_LAST_KNOWN_POSITION_KEYWORD)
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
      metavar = 'search query',
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
      help='focus on given coordinates, NOTE you can use --set-zl to set zoom level, EXAMPLE: "geo:50.083333,14.416667"',
      metavar="geographic coordinates with the geo: prefix",
      type=str,
      default=None,
      action="store"
    )

    self.args = parser.parse_args()


  def getArgs(self):
    """return parsed CLI arguments"""
    return self.args

  def handleEarlyTasks(self):
    """
    handle CLI arguments that can be handled before the general modRana startup
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
    print("startup: focusing on CLI-provided coordinates")

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
          print("startup: focusing on %f %f" % (lat, lon))
          # disable centering & show the map screen
          self.modrana.set("menu", None)
          self.modrana.set("centred", False)
          # send the map focusing message
          message = "mapView:recentre %f %f" % (lat, lon)
          self._sendMessage(message)
          self.m.get("messages")
        else:
          print("startup: parsing coordinates for the --focus-on-coordinates option failed")
          print("unknown coordinate format: %s" % split1[1])

      else:
        print("startup: parsing coordinates for the --focus-on-coordinates option failed")
        print("missing geo: prefix")

      # make sure centering is disabled
      self.modrana.set("centred", False)
    except Exception, e:
      print("startup: parsing coordinates for the --focus-on-coordinates option failed")
      print(e)

  def _earlyLocalSearch(self):
    """handle CLI initiated local search that returns a static map URL"""
    """for local search, we need to know our position, so we need at least the
    location module and of also of course the online services module to do the search
    """
    self._disableStdout()

    # load the online services module
    online = self.modrana._loadModule("mod_onlineServices", "onlineServices")

    query = self.args.local_search
    points = [] # points defining the result/s

    # now check if a location for the local search was provided from CLI or if we need to find our location
    # using GPS or equivalent

    if self.args.local_search_location is not None:
      # we use the location provided from CLI, no need to load & start location
      location = self.args.local_search_location
      if self._useLastKnownPos(location):
        pos = self._getCurrentPosition(loadLocationModule=True, useLastKnown=True)
        if pos is None:
          self._enableStdout()
          print("no last known position available")
          # done - no position found
          self._exit(LOCAL_SEARCH_CURRENT_POSITION_UNKNOWN_ERROR)
        else:
          lat, lon = pos
          points = online.localSearchLL(query, lat, lon)
      else:
        points = online.localSearch(query, location)

    else:
      # we need to determine our current location - the location module needs to be loaded & used
      pos = self._getCurrentPosition(loadLocationModule=True)
      if pos is not None:
        lat, lon = pos
        points = online.localSearchLL(query, lat, lon)
      else:

        # done - no position found
        self._exit(LOCAL_SEARCH_CURRENT_POSITION_UNKNOWN_ERROR)

    # local search results processing
    self._returnStaticMapUrl(points, online)

  def _earlyAddressSearch(self):
    """search for address and return a static map URL for the result/s"""
    self._disableStdout()
    query = self.args.address_search
    # load the online services module
    online = self.modrana._loadModule("mod_onlineServices", "onlineServices")
    results = online.geocode(query)
    self._returnStaticMapUrl(results, online)

  def _earlyWikipediaSearch(self):
    """search Wikipedia and return a static map URL for the result/s"""
    self._disableStdout()
    query = self.args.wikipedia_search
    # load the online services module
    online = self.modrana._loadModule("mod_onlineServices", "onlineServices")
    results = online.wikipediaSearch(query)
    self._returnStaticMapUrl(results, online)

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
      print url
      # done - success
      self._exit(0)
    else:
      self._enableStdout()
      print("search returned no results")
      self._exit(SEARCH_NO_RESULTS_FOUND)

  def _localSearch(self):
    """CLI initiated online local search that displays the result inside modRana"""
    print("startup: searching for CLI-provided query")
    query = self.args.local_search

    # try to make sure Internet connectivity is available
    # -> Internet is needed for a quick fix & the search itself
    # -> if the device is offline, it might need this "nudge"
    # to reconnect
    self.modrana.dmod.enableInternetConnectivity()

    # check if location was provided from CLI
    if self.args.local_search_location is not None:
      location = self.args.local_search_location
      if self._useLastKnownPos(location):
        pos = self._getCurrentPosition(useLastKnown=True)
        if pos is None:
          print("startup: no last known position")
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
    self.modrana.dmod.enableInternetConnectivity()

    print("startup: searching where is the CLI-provided address")
    query = self.args.address_search
    message = "ml:search:search:address;%s" % query
    self._sendMessage(message)

  def _wikipediaSearch(self):
    """CLI initiated online Wikipedia search, that shows results inside modRana"""
    # try to make sure Internet connectivity is available
    # -> Internet is needed for a quick fix & the search itself
    # -> if the device is offline, it might need this "nudge"
    # to reconnect
    self.modrana.dmod.enableInternetConnectivity()

    print("startup: searching Wikipedia for CLI-provided query")
    query = self.args.wikipedia_search
    message = "ml:search:search:wikipedia;%s" % query
    self._sendMessage(message)

  def _sendMessage(self, message):
    m = self.modrana.m.get("messages")
    if m:
      m.sendMessage(message)

  def _getCurrentPosition(self, loadLocationModule=False, useLastKnown = False):
    """get current position on a system in early startup state"""

    # do we need to load the location module ?
    # we usually need to if we handle an early task that happens before regular startup
    if loadLocationModule:
      # the location module might need the device module to handle location on some devices
      self.modrana._loadDeviceModule()
      # load the location module
      l = self.modrana._loadModule("mod_location", "location")
      # start location
      l.startLocation()
    else:
      l = self.modrana.m.get("location", None)

    pos = None
    if l and not useLastKnown:
      timeout = 0
      checkInterval = 0.1 # in seconds
      print("startup: trying to determine current position for at most %d s" % LOCAL_SEARCH_LOCATION_TIMEOUT)
      while timeout <= LOCAL_SEARCH_LOCATION_TIMEOUT:
        if l.provider:
          if self.modrana.dmod.getLocationType() in ("gpsd", "liblocation"):
            # GPSD and liblocation need a nudge
            # to update the fix when the GUI mainloop is not running
            l.provider._updateGPSD()
          pos = l.provider.getFix().position
          if pos is not None:
            break

        timeout+=checkInterval
        time.sleep(checkInterval)
      if loadLocationModule:
      # properly stop location when done (for early tasks)
        l.stopLocation()

    if pos is None: # as a last resort, try last known position, if available
      if not useLastKnown:
        print "startup: current position unknown"
      print "startup: using last known position"
      # we might need to load options "manually" if run early
      if not self.modrana.optLoadingOK:
        self._loadOptions()

      pos = self.modrana.get("pos", None)
      if pos is None:
        print("startup: no last known position")

    return pos


  def _enableStdout(self):
    """enable stdout output"""
    sys.stdout = self.originalStdout
    self.originalStdout = None

  def _disableStdout(self):
    """disable stdout output
    -> this is mainly used for CLI processing so that modRanas status messages don't get into the output
    that will be parsed by outside programs or scripts
    """
    self.originalStdout = sys.stdout
    sys.stdout = self

  def write(self, s):
    """a write function that does nothing for stdout redirection"""
    pass

  def _loadOptions(self):
    """load the persistent options (for usage by early tasks)"""
    from core import paths
    # options needs the paths class to know from where to load the options
    self.modrana.paths = paths.Paths(self.modrana)
    self.modrana._loadOptions()

  def _useLastKnownPos(self, location):
    return str.strip(location) == USE_LAST_KNOWN_POSITION_KEYWORD

  def _exit(self, errorCode=0):
    sys.exit(errorCode)

