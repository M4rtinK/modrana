# -*- coding: utf-8 -*-
# supplies position info from the GPS daemon
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
from __future__ import with_statement # for python 2.5
from modules.base_module import RanaModule
from time import *
from core import gs
from core.signal import Signal


def getModule(*args, **kwargs):
    return Location(*args, **kwargs)


class Location(RanaModule):
    """Supplies position info from a position source"""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self.tt = 0
        self.connected = False
        self.set('speed', None)
        self.set('metersPerSecSpeed', None)
        self.set('bearing', None)
        self.set('elevation', None)
        self.status = "Unknown"
        self._enabled = False
        self.provider = None
        self.startSignal = Signal()
        self.stopSignal = Signal()
        self.positionUpdate = Signal()

        # check if the device handles location by itself
        if not self.modrana.dmod.handles_location:
            method = self.modrana.dmod.location_type
            if method == "qt_mobility":
                self.log.info("using Qt Mobility")
                from . import qt_mobility

                self.provider = qt_mobility.QtMobility(self)
            elif method == "gpsd": # GPSD
                self.log.info("using GPSD")
                from . import gps_daemon

                self.provider = gps_daemon.GPSD(self)

        # watch if debugging needs to be enabled
        self.modrana.watch("gpsDebugEnabled", self._debugCB, runNow=True)

    def firstTime(self):
        # periodic screen redraw
        if self.modrana.dmod.location_type in ("gpsd", "liblocation"):
            self.log.info("starting GPSD 1 second timer")
            # start screen update 1 per second screen update
            # TODO: event based redrawing
            cron = self.m.get('cron', None)
            if cron:
                cron.addTimeout(self._screenUpdateCB, 1000, self, "screen and GPSD update")

        # start location if enabled in options
        if self.get('GPSEnabled', True): # is GPS enabled ?
            self.startLocation()

    def _screenUpdateCB(self):
        """update the screen and also GPSD location if enabled
        TODO: more efficient screen updates"""
        #    self.log.info("location: screen update")

        # only try to update position info if
        # location is enabled
        if self._enabled and self.provider:
            self.provider._updateGPSD()

            fix = self.provider.getFix()
            if fix:
                self.updatePosition(fix)
            else:
                self.log.warning("fix not valid")
                self.log.info(fix)

    def _debugCB(self, key, oldValue, newValue):
        if self.provider:
            self.provider.setDebug(newValue)

    def handleMessage(self, message, messageType, args):
        if message == "setPosLatLon" and messageType == "ml":
            if args and len(args) == 2:
                lat = float(args[0])
                lon = float(args[1])
                self.log.info("setting current position to: %f,%f", lat, lon)
                self.set('pos', (lat, lon))
        elif message == "checkGPSEnabled":
            state = self.get('GPSEnabled', True)
            if state == True:
                self.startLocation()
            elif state == False:
                self.stopLocation()
        elif message == "gpsdCheckVerboseDebugEnabled":
            self._checkVerbose()

    def updatePosition(self, fix):
        """
        update position info with new Fix data
        """
        if fix.position is None:
            # set fix class to 0 - nothing yet
            self.set('fix', 0)
            # wait for valid data
            return
        (lat, lon) = fix.position
        fixClass = 2 # 2D data

        # position
        self.set('pos', (lat, lon))
        self.set('pos_source', 'GPSD')
        # bearing
        self.set('bearing', float(fix.bearing))
        # speed
        #    if speed != None:
        #      # normal gpsd reports speed in knots per second
        #      gpsdSpeed = self.get('gpsdSpeedUnit', 'knotsPerSecond')
        #      if gpsdSpeed == 'knotsPerSecond':
        #        # convert to meters per second
        #        speed = float(speed) * 0.514444444444444 # knots/sec to m/sec
        if fix.speed is not None:
            self.set('metersPerSecSpeed', fix.speed)
            self.set('speed', fix.speed * 3.6)
        else:
            self.set('metersPerSecSpeed', None)
            self.set('speed', None)
            # elevation
        if fix.altitude is not None:
            self.set('elevation', fix.altitude)
            fixClass = 3
        else:
            self.set('elevation', None)

        # set fix class
        # NOTE:
        # 0 - no sats
        # 1 - no fix
        # 2 - 2D
        # 3 - 3D
        self.set("fix", fixClass)
        # always set this key to current epoch once the location is updated
        # so that modules can watch it and react on position updates
        self.positionUpdate(fix)
        self.set('locationUpdated', time())

    def getFix(self):
        return self.provider.getFix()

    def startLocation(self, startMainLoop=False):
        """start location - device based or gpsd"""
        # send the location start signal
        self.startSignal()
        if not self._enabled:
            if self.modrana.dmod.handles_location:
                locationType = self.modrana.dmod.location_type
                if locationType != "QML":
                    # location startup is handled by the
                    # GUI module in if QML location
                    # type is used
                    self.log.info("enabling device module location")
                    self.modrana.dmod.start_location(start_main_loop=startMainLoop)
            elif gs.GUIString == "qt5" and self.modrana.dmod.device_id != "pc":
                self.log.info("location is handled by Qt5 when using Qt5 GUI")
            elif self.provider:
                self.log.info("enabling location")
                self.provider.start(startMainLoop=startMainLoop)
            self._enabled = True
        else:
            self.log.error('location already enabled')

    def stopLocation(self):
        """stop location - device based or gpsd"""
        # send the location stop signal
        self.stopSignal()
        self.log.info("location: disabling location")
        if self.modrana.dmod.handles_location:
            self.modrana.dmod.stop_location()
        # check if location provider is available,
        # if it is available, stop location
        elif self.provider:
            self.provider.stop()
        self._enabled = False

    @property
    def enabled(self):
        """Report if location is enabled"""
        return self._enabled

    def shutdown(self):
        try:
            self.stopLocation()
        except Exception:
            self.log.exception("location: stopping location failed")

    def _checkVerbose(self):
        if self.provider:
            self.provider._checkVerbose()
