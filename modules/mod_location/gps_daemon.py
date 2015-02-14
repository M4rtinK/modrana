# -*- coding: utf-8 -*-
# Supplies position info from the GPS daemon
#---------------------------------------------------------------------------
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
from __future__ import with_statement # for python 2.5
import threading
import socket
from time import sleep

from .base_position_source import PositionSource
from core.fix import Fix
from core import threads
from core import constants

MAX_CONSECUTIVE_GPSD_WARNINGS = 5

import logging
log = logging.getLogger("mod.location.gpsd")

class GPSD(PositionSource):
    def __init__(self, location):
        PositionSource.__init__(self, location)
        self.connected = False
        self.GPSDConsumer = None
        self.status = "not connected"

    def start(self, startMainLoop=False):
        """start the GPSD based location update method"""
        self.connected = False
        try:
            self.GPSDConsumer = GPSDConsumer()
            t = threads.ModRanaThread(name=constants.THREAD_GPSD_CONSUMER,
                                      target = self.GPSDConsumer._start)
            threads.threadMgr.add(t)
            self.connected = True
            self.setGPSDDebug(self.debug) # check if verbose debugging is enabled
        except Exception:
            log.exception("connecting to GPSD failed")
            self.status = "No GPSD running"

    def stop(self):
        """stop the GPSD based location update method"""
        if self.GPSDConsumer:
            self.GPSDConsumer.shutdown()
        self.GPSDConsumer = None
        self.connected = False
        self.status = "No GPSD running"

    def _updateGPSD(self):
        # only update if connected to GPSD
        if self.connected:
            fix, sats = self.GPSDConsumer.getBoth()
            if fix:
                # as the GPSD consumer updates its values very often, it probably better to use a simple
                # tuple instead of a Fix object and only convert to the Fix object once the position data
                # is actually requested
                #        (lat,lon,elevation,bearing,speed,timestamp) = fix
                satCount = len(sats)
                inUseSatCount = len([x for x in sats if x.used])

                modRanaFix = Fix((fix.latitude, fix.longitude),
                                 fix.altitude,
                                 fix.track,
                                 fix.speed,
                                 mode=fix.mode,
                                 climb=fix.climb,
                                 sats=satCount,
                                 sats_in_use=inUseSatCount,
                                 horizontal_accuracy=fix.epx * fix.epy,
                                 # TODO: separate x y accuracy support ?
                                 vertical_accuracy=fix.epv,
                                 speed_accuracy=fix.eps,
                                 climb_accuracy=fix.epc,
                                 bearing_accuracy=fix.epd,
                                 time_accuracy=fix.ept,
                                 gps_time=fix.time
                )
                self.fix = modRanaFix

    def setDebug(self, value):
        self.debug = value
        self.setGPSDDebug(value)

    def setGPSDDebug(self, verbose):
        if self.GPSDConsumer:
            if verbose:
                self.GPSDConsumer.setVerbose(True)
                log.info("gpsd debugging output turned ON")
            else:
                self.GPSDConsumer.setVerbose(False)
                log.info("gpsd debugging output turned OFF")
        else:
            log.info("location: gpsd not used, so there is no debug output to enable")

class GPSDConsumer(object):
    """consume data as they come in from the GPSD and store last known fix"""

    def __init__(self):
        self.lock = threading.RLock()
        self.stop = False

        from .gps_module import gps
        from .gps_module import client
        try:
            self.session = gps(host="localhost", port="2947")
            self.session.stream(flags=client.WATCH_JSON)
        except socket.error:
            self.session = None
            log.warning("GPS daemon refused initial connection")
        self.verbose = False
        self.fix = None
        self.satellites = []
        self._consecutiveGPSDErrors = 0

    def _start(self):
        if self.session is None:
            # connection to GPS daemon not established
            log.debug("GPSDConsumer: could not connect to GPSD session")
            return
        log.info("GPSDConsumer: starting")
        while True:
            if self.stop == True:
                log.info("GPSDConsumer: breaking")
                break
            try:
                self.session.next() # this function blocks until a new fix is available

            except socket.error:
                log.warning("GPS daemon connection refused")
            except socket.timeout:
                self._consecutiveGPSDErrors+=1
                if self._consecutiveGPSDErrors <= MAX_CONSECUTIVE_GPSD_WARNINGS:
                    log.warning("GPS daemon not running (%d/%d",
                                self._consecutiveGPSDErrors, MAX_CONSECUTIVE_GPSD_WARNINGS)
                else:
                    log.warning("ignoring further GPSD-not-running warnings")
            except Exception:
                log.exception("GPS daemon connection failed")

            # connection successful, clear the error count
            self._consecutiveGPSDErrors = 0

            sf = self.session.fix
            if sf.mode > 1: # 0 & 1 -> no fix
                with self.lock:
                    self.fix = sf
                    self.satellites = self.session.satellites
                    if self.verbose:
                        try:
                            log.debug('GPSD fix debug')
                            log.debug(
                                'mode:' + str(sf.mode) + ' lat,lon:' + str(
                                    (sf.latitude, sf.longitude)) + ' elev:' + str(sf.altitude))
                        except Exception:
                            log.exception('ERROR debugging GPSD fix')
            else:
                if self.verbose:
                    log.debug("GPSDConsumer: NO FIX, will retry in 1 s")
                sleep(1)
        log.info("GPSDConsumer: stopped")

    def shutdown(self):
        log.info("GPSDConsumer: stopping")
        self.stop = True

    def getFix(self):
        with self.lock:
            return self.fix

    def getSatellites(self):
        with self.lock:
            return

    def getBoth(self):
        with self.lock:
            return self.fix, self.satellites

    def setVerbose(self, value):
        with self.lock:
            self.verbose = value