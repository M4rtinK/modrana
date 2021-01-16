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
import time


def getModule(*args, **kwargs):
    return Stats(*args, **kwargs)


class Stats(RanaModule):
    """Handles statistics"""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self.minimal_speed = 2 #  in kmh, we don't update the avg speed if the current speed is like this
        self.lastT = None
        self._max_speed = 0
        self.avg1 = 0
        self.avg2 = 0
        # update stats once new position info is available
        self.modrana.watch('locationUpdated', self.update_stats_cb)


    def update_stats_cb(self, *args):
        # Run scheduled_update every second
        t = time.time()
        if self.lastT is None:
            self.scheduled_update(1, True) # dt should not be 0 because we use it for division
            self.lastT = t
        else:
            dt = t - self.lastT
            if dt > 1:
                self.scheduled_update(dt)
                self.lastT = t

    def scheduled_update(self, dt, firstTime=False):
        """Called every dt seconds."""
        pos = self.get('pos', None)
        if pos is None:
            return # TODO: zero stats
        speed = self.get('speed', None)
        if speed is None or speed <= self.minimal_speed:
            # we have no data, or the speed is below the threshold (we are not moving)
            return
        average = 0
        if speed > self.max_speed:
            self.max_speed = speed
        self.avg1 += speed
        self.avg2 += dt
        average = self.avg1 / self.avg2

        self.set('max_speed', self.max_speed)
        self.set('avgSpeed', average)

    def get_current_speed_string(self):
        """Return current speed as string with the current unit.

        EXAMPLE: "88 mph" or "1000 km/h"

        :return: current speed in currently selected unit
        :rtype: str
        """
        speed_string = "speed unknown"
        units = self.m.get('units', None)
        kmh_speed = self.get('speed', None)
        if units and kmh_speed is not None:
            speed_string = units.km2CurrentUnitPerHourString(kmh_speed)
        elif units: # speed unknown, just return something like "? km/h"
            speed_string = "? %s" % units.currentUnitPerHourString()
        return speed_string

    def get_average_speed_string(self):
        """Return current average speed as string with the currently selected unit.

        :return: current average speed in selected unit
        :rtype: str
        """
        speed_string = "?"
        units = self.m.get('units', None)
        kmh_average_speed = self.get('avgSpeed', None)
        if units and kmh_average_speed is not None:
            speed_string = units.km2CurrentUnitPerHourString(kmh_average_speed, dp=0)
        elif units: # speed unknown, just return something like "? km/h"
            speed_string = "? %s" % units.currentUnitPerHourString()
        return speed_string

    def get_max_speed_string(self):
        """return current average speed as string with the currently unit"""
        speed_string = "?"
        units = self.m.get('units', None)
        kmh_max_speed = self.get('max_speed', None)
        if units and kmh_max_speed is not None:
            speed_string = units.km2CurrentUnitPerHourString(kmh_max_speed, dp=0)
        elif units: # speed unknown, just return something like "? km/h"
            speed_string = "? %s" % units.currentUnitPerHourString()
        return speed_string

    @property
    def current_speed(self):
        """Return current speed in kmh.

        :return: current speed in kmh
        :rtype: float
        """
        return self.get('speed', -1)

    @property
    def average_speed(self):
        """Return average speed in kmh.

        :return: average speed in kmh
        :rtype: float
        """
        return self.get('avgSpeed', -1)

    @property
    def max_speed(self):
        """Return maximum recorded speed in kmh for this modRana session.

        The maximum recorded speed is not stored, so a new value is
        continuously established once modRana is started.

        :return: maximum speed in kmh
        :rtype: float
        """

        return self.get('max_speed', -1)

    @max_speed.setter
    def max_speed(self, value):
        self._max_speed = value

    def get_speed_stats_dict(self):
        """Return a dictionary with speed stats.

        Like this, speed statistics can be displayed atomically.
        We also round the values to zero decimal places.

        :returns: speed statistics dictionary
        :rtype: dict
        """
        return {
            "current": int(round(self.current_speed, 0)),
            "avg": int(round(self.average_speed, 0)),
            "max": int(round(self.max_speed, 0))
        }
