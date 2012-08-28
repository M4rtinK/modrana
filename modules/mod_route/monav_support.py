#!/usr/bin/python
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Handles offline routing with Monav
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
import time
import subprocess
import signal
import os

import monav

# Marble stores monav data like this on the N900:
# /home/user/MyDocs/.local/share/marble/maps/earth/monav/motorcar/europe/czech_republic

MONAV_BINARY_PATH = 'modules/mod_route/monav_arm7/monav-server'
# TODO: other architectures

class Monav:
  def __init__(self):
    self.monavServer = None
    self.connection = None

  def startServer(self, port=None):
    print('monav_support: starting Monav server')
    try:
      # first check if monav server is already running
      try:
        self.connection = monav.TcpConnection()
        print('monav_support: server already running')
      except Exception, e:
        print('monav_support: server not yet running')
        self.monavServer = subprocess.Popen(
          "%s" % MONAV_BINARY_PATH
        )
        self.connection = monav.TcpConnection()
        # TODO: use other port than 8040 ?, check out tileserver code
    except Exception, e:
      print('monav_support: starting Monav server failed')
      print(e)
    print('monav_support: Monav server started')

  def stopServer(self):
    print('monav_support: stopping Monav server')
    try:
      if self.monavServer:
        os.kill(self.monavServer.pid, signal.SIGKILL)
      else:
        print('monav_support: no Monav server process found')
    except Exception, e:
      print('monav_support: stopping Monav server failed')
      print(e)
    self.monavServer = None
    self.connection = None
    print('monav_support: Monav server stopped')

  def serverRunning(self):
    if self.monavServer:
      return True
    else:
      return False

  def monavDirections(self, dataDirectory, waypoints):
    """search ll2ll route using Monav"""
    # check if Monav server is running
    if not self.serverRunning():
      self.startServer() # start the server

    print('monav: starting route search')
    start = time.clock()
    result = monav.get_route(dataDirectory,
                             waypoints,
                             connection=self.connection)
    print('monav: search finished in %1.2 ms'  % (1000 * (time.clock() - start)) )
    return result

  def monavDirectionsAsync(self, start, destination, callback, key):
    """search ll2ll route asynchronously using Monav"""
    pass




