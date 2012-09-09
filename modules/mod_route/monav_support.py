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
from threading import Thread
import time
import subprocess
import traceback
import sys

import monav

from signals_pb2 import RoutingResult

# Marble stores monav data like this on the N900:
# /home/user/MyDocs/.local/share/marble/maps/earth/monav/motorcar/europe/czech_republic

class Monav:
  def __init__(self, monavBinaryPath):
    self.monavServer = None
    self.monavServerBinaryPath = monavBinaryPath
    # make return codes easily accessible
    self.returnCodes = RoutingResult

  def startServer(self, port=None):
    print('monav_support: starting Monav server')
    started = False
    try:
      # first check if monav server is already running
      try:
        monav.TcpConnection()
        print('monav_support: server already running')
      except Exception, e:
        print('monav_support: starting monav server in:')
        print(self.monavServerBinaryPath)

        def _startServer(self):
          self.monavServer = subprocess.Popen(
            "%s" % self.monavServerBinaryPath
          )

        t = Thread(target=_startServer, args=[self], name='asynchronous monav-server start')
        t.setDaemon(True) # we need that the thread dies with the program
        t.start()
        timeout = 5 # in s
        sleepTime = 0.1 # in s
        startTimestamp = time.time()
        elapsed = 0
        # wait up to timeout seconds for the server to start
        # and then return
        while elapsed < timeout:
          if self.monavServer:
            break
          time.sleep(sleepTime)
          elapsed = time.time() - startTimestamp
        started = True
        # TODO: use other port than 8040 ?, check out tileserver code
    except Exception, e:
      print('monav_support: starting Monav server failed')
      print(e)
    if started:
      print('monav_support: Monav server started')

  def stopServer(self):
    print('monav_support: stopping Monav server')
    stopped = False
    try:
      if self.monavServer:
        #os.kill(self.monavServer.pid, signal.SIGKILL)
        self.monavServer.terminate()
        stopped = True
      else:
        print('monav_support: no Monav server process found')
    except Exception, e:
      print('monav_support: stopping Monav server failed')
      print(e)
    self.monavServer = None
    if stopped:
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
    connection = monav.TcpConnection()
    try:
      result = monav.get_route(dataDirectory,
                                           waypoints,
                                           connection = connection)
    except Exception, e:
      print('monav_support: routing failed')
      print(e)
      traceback.print_exc(file=sys.stdout) # find what went wrong
      return None
    print('monav: search finished in %1.2f ms'  % (1000 * (time.clock() - start)) )
    return result

  def monavDirectionsAsync(self, start, destination, callback, key):
    """search ll2ll route asynchronously using Monav"""
    pass




