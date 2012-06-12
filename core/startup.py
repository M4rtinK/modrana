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

import argparse

class Startup:
  def __init__(self, modrana):
    self.modrana = modrana
    parser = argparse.ArgumentParser(description="A flexible GPS navigation system.")
    # device
    parser.add_argument(
      '-d', metavar="device ID", type=str,
      help="specify device type",
      default=None, action="store",
      choices=["neo","pc", "n900", "n9", "q7"]
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
    # local search
    parser.add_argument(
      '--local-search-location', metavar='an address or geographic coordinates', type=str,
      help='specify a geographic location for a local search query (current location is used by default), both addresses and geographic coordinates are supported EXAMPLE: "London" or "12.3,45.6"'
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
    # wikipedia search
    parser.add_argument(
      '--return-static-map-url',
      help='return static map URL for a CLI query (works for local search, address and Wikipedia search)',
      action="store_false"
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
    pass

  def handlePostFirstTimeTasks(self):
    """
    handle CLI arguments that should take effect once modrana is fully stared
    EX.: do an address search and display the results inside modRana
    """
    pass
