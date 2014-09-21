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
import os
from threading import Thread
import time
import subprocess
import traceback
import sys
import signal
from . import monav

RETRY_COUNT = 3 # if routing fails, try RETRY_COUNT more times
# there might be some situations where the Monav server might fail
# to return a route even if it exists - it seems to be prone to these
# errors especially at startup, even though it is possible to
# succesfully initiate a connection with it & query its version
#
# Monav routing is also very fast, so doing more tries is not a problem

from .signals_pb2 import RoutingResult

import logging
log = logging.getLogger("mod.routing.monav_support")

# Marble stores monav data like this on the N900:
# /home/user/MyDocs/.local/share/marble/maps/earth/monav/motorcar/europe/czech_republic

class Monav(object):
    def __init__(self, monavBinaryPath):
        self.monavServer = None
        self.monavServerBinaryPath = monavBinaryPath
        # make return codes easily accessible
        self.returnCodes = RoutingResult
        self._dataPath = None

        self.result2turns = None
        # a method "slot" to be replaced by concrete
        # implementation after the object is instantiated

    @property
    def dataPath(self):
        return self._dataPath

    @dataPath.setter
    def dataPath(self, value):
        self._dataPath = value

    def startServer(self, port=None):
        log.info('starting Monav server')
        started = False
        try:
            # first check if monav server is already running
            try:
                monav.TcpConnection()
                log.error('server already running')
            except Exception:
                import sys

                if not self.monavServerBinaryPath:
                    log.error("can't start monav server - monav server binary missing")
                    return
                log.info('using monav server binary in:')
                log.info(self.monavServerBinaryPath)

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
                        try:
                            # test if the server is up and accepting connections
                            monav.TcpConnection()
                            break
                        except Exception:
                            pass # not yet fully started
                    time.sleep(sleepTime)
                    elapsed = time.time() - startTimestamp
                started = True
                # TODO: use other port than 8040 ?, check out tileserver code
        except Exception:
            log.exception('starting Monav server failed')

        if started:
            log.info('Monav server started')

    def stopServer(self):
        log.info('stopping Monav server')
        stopped = False
        try:
            if self.monavServer:
                # Python 2.5 doesn't have POpen.terminate(),
                # so we use this
                os.kill(self.monavServer.pid, signal.SIGKILL)
                stopped = True
            else:
                log.error('no Monav server process found')
        except Exception:
            log.exception('stopping Monav server failed')

        self.monavServer = None
        if stopped:
            log.info('Monav server stopped')

    def serverRunning(self):
        if self.monavServer:
            return True
        else:
            return False

    def monavDirections(self, waypoints):
        """search ll2ll route using Monav"""
        # check if Monav server is running

        if self.dataPath is None:
            log.error("error, dataPath not set (is None)")
            return None
        if not self.serverRunning():
            self.startServer() # start the server

        # Monav works with (lat, lon) tuples so we
        # need to convert the waypoints to a list of
        # (lat,lon) tuples
        waypoints = [x.getLL() for x in waypoints]

        log.info('starting route search')
        start = time.clock()
        tryNr = 0
        result = None
        while tryNr < RETRY_COUNT:
            tryNr += 1
            try:
                result = monav.get_route(self.dataPath, waypoints)
                break
            except Exception:
                log.exception('routing failed')

                if tryNr < RETRY_COUNT:
                    log.info('retrying')
        if tryNr < RETRY_COUNT:
            log.info('monav: search finished in %1.2f ms and %d tries', 1000 * (time.clock() - start), tryNr)
            return result
        else:
            log.error('monav: search failed after %d retries', tryNr)
            return None