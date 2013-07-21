# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Calculate speed, time, etc. from position
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
from core import geo
from time import *


def getModule(m, d, i):
    return Stats(m, d, i)


class Stats(RanaModule):
    """Handles statistics"""

    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)
        self.minimalSpeed = 2 #  in kmh, we don't update the avg speed if the current speed is like this
        self.lastT = None
        self.maxSpeed = 0
        self.avg1 = 0
        self.avg2 = 0
        # update stats once new position info is available
        self.modrana.watch('locationUpdated', self.updateStatsCB)


    def updateStatsCB(self, *args):
        # Run scheduledUpdate every second
        t = time()
        if self.lastT is None:
            self.scheduledUpdate(t, 1, True) # dt should not be 0 because we use it for division
            self.lastT = t
        else:
            dt = t - self.lastT
            if dt > 1:
                self.scheduledUpdate(t, dt)
                self.lastT = t

    def scheduledUpdate(self, t, dt, firstTime=False):
        """Called every dt seconds"""
        pos = self.get('pos', None)
        if pos is None:
            return # TODO: zero stats
        speed = self.get('speed', None)
        if speed is None or speed <= self.minimalSpeed:
            # we have no data, or the speed is below the threshold (we are not moving)
            return
        average = 0
        if speed > self.maxSpeed:
            self.maxSpeed = speed
        self.avg1 += speed
        self.avg2 += dt
        average = self.avg1 / self.avg2

        self.set('maxSpeed', self.maxSpeed)
        self.set('avgSpeed', average)

    def getCurrentSpeedString(self):
        """return current speed as string with the current unit
        EXAMPLE: "88 mph" or "1000 km/h" """
        speedString = "speed unknown"
        units = self.m.get('units', None)
        metersPerSecSpeed = self.get('speed', None)
        if units and metersPerSecSpeed is not None:
            speedString = units.km2CurrentUnitPerHourString(metersPerSecSpeed)
        elif units: # speed unknown, just return something like "? km/h"
            speedString = "? %s" % units.currentUnitPerHourString()
        return speedString

    def getAverageSpeedString(self):
        """return current average speed as string with the currently unit"""
        speedString = "?"
        units = self.m.get('units', None)
        kmhAverageSpeed = self.get('metersPerSecSpeed', None)
        if units and kmhAverageSpeed is not None:
            speedString = units.km2CurrentUnitPerHourString(kmhAverageSpeed, dp=0)
        elif units: # speed unknown, just return something like "? km/h"
            speedString = "? %s" % units.currentUnitPerHourString()
        return speedString

    def getMaxSpeedString(self):
        """return current average speed as string with the currently unit"""
        speedString = "?"
        units = self.m.get('units', None)
        kmhMaxSpeed = self.get('maxSpeed', None)
        if units and kmhMaxSpeed is not None:
            speedString = units.km2CurrentUnitPerHourString(kmhMaxSpeed, dp=0)
        elif units: # speed unknown, just return something like "? km/h"
            speedString = "? %s" % units.currentUnitPerHourString()
        return speedString
