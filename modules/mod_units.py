# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# A module handling unit conversions and displaying correct units according to current settings.
#----------------------------------------------------------------------------
# Copyright 2010, Martin Kolman
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
    return Units(*args, **kwargs)


class Units(RanaModule):
    """a unit handling module """

    mileInMeters = 1609.344
    mileInKiloMeters = mileInMeters / 1000
    mileInFeet = 5280
    mileInYards = 1760
    footInMeters = 0.3048
    yardInMeters = 0.9144


    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        """
        # we consider 2km/h as as stationary
        (to filter out the standard GPS drift while not moving)
        """
        self.notMovingSpeed = 2
        self._updateUnitTable()

    def _updateUnitTable(self):
        # TODO: unit localization support
        # TODO: different global & routing unit localization support
        self.unitTable = {
            'km': Unit(('m', 'meter', 'meters'), ('km', 'kilometer', 'kilometers'), type='km'),
            'miles': Unit(('yd', 'yard', 'yards'), ('mi', 'mile', 'miles'), type='miles'),
            'milesFeet': Unit(('ft', 'foot', 'feet'), ('mi', 'mile', 'miles'), type='miles', subType='feet'),
        }

    def m2km(self, m):
        return m / 1000.0 # m to km

    def km2m(self, km):
        return km * 1000 # km to m

    def km2Miles(self, km):
        return km / self.mileInKiloMeters  # km to miles

    def miles2Feet(self, miles):
        return miles * self.mileInFeet

    def miles2Yards(self, miles):
        return miles * self.mileInYards

    def m2CurrentUnit(self, m):
        return self.km2CurrentUnit(m * 1000)

    def km2CurrentUnit(self, km):
        unitType = self.get("unitType", "km")
        if unitType == 'km':
            return km
        else:
            return self.km2Miles(km)

    def m2CurrentUnitString(self, m, dp=None, short=False):
        km = self.m2km(m)
        return self.km2CurrentUnitString(km, dp, short)

    def km2CurrentUnitString(self, km, dp=None, short=True):
        """return current unit in string with unit descriptor, rounded to two decimal places"""
        # get current unit
        unit = self.getCurrentUnit()

        small = False
        if unit.type == 'km':
            if km <= 1: # we now count in meters
                dp = -1 # no need to count the odd meter with current GPS accuracy
                distance = km * 1000
                small = True
            else:
                distance = km
        else: # just miles for now
            if km < self.mileInKiloMeters / 10:
                if unit.subType == 'feet':
                    distance = self.km2Miles(km) * self.mileInFeet
                else:
                    distance = self.km2Miles(km) * self.mileInYards
                dp = -1 # no need to count the odd foot with current GPS accuracy
                small = True
            else:
                distance = self.km2Miles(km)

        # rounding
        if dp is None:
            numberString = "%f" % distance
        elif dp == 0:
            n = int(round(distance, 0))
            numberString = "%d" % n
        else:
            n = round(distance, dp)
            numberString = "%f" % n

        # strip trailing zeroes

        #is it a string float representation ?
        if '.' in numberString: # strip possible trailing zeroes
            numberString = numberString.rstrip('0').rstrip('.')

        if short:
            if small:
                return "%s %s" % (numberString, unit.smallShort)
            else:
                return "%s %s" % (numberString, unit.normalShort)
        else:
            if small:
                return "%s %s" % (numberString, unit.smallP)
            else:
                return "%s %s" % (numberString, unit.normalP)

    def km2CurrentUnitStringFullName(self, km):
        """return current unit in string with unit descriptor, rounded to two decimal places"""
        unitType = self.get("unitType", "km")
        if unitType == 'km':
            if km >= 1:
                return "%1.2f kilometers" % km
            else:
                return "%000.0f meters" % (km * 1000.0)
        else:
            return "%1.2f miles" % self.km2Miles(km)

    def km2CurrentUnitPerHourString(self, km, dp=None, short=True):
        """return a string with the speed rounded to the current unit
           %f1.2 speed_unit_per_hour
           example: 5.25 km/h
           """

        unitType = self.get("unitType", "km")

        # unit conversion
        if unitType == 'km':
            speed = km
        else: # miles
            speed = self.km2Miles(km)

        # rounding
        if dp is None:
            numberString = "%1.0f" % speed
        elif dp == 0:
            n = int(round(speed, 0))
            numberString = "%d" % n
        else:
            n = round(speed, dp)
            numberString = "%f" % n

        # short/long unit description
        if unitType == 'km':
            if short:
                unitString = "km/h"
            else:
                unitString = "kilometers per hour"

            return "" + numberString + " " + unitString
        else:
            if short:
                unitString = "mph"
            else:
                unitString = "miles per hour"

            return "" + numberString + " " + unitString

    def km2CurrentUnitPerHourStringTwoDP(self, km):
        """return a string with the speed rounded to two decimal places with the current unit
           %f1.2 speed_unit_per_hour
           example: 5.25 km/h
           """
        unitType = self.get("unitType", "km")
        if unitType == 'km':
            return "%1.0f km/h" % km
        else:
            return "%1.0f mph" % self.km2Miles(km)

    def currentUnitPerHourString(self):
        unitType = self.get("unitType", "km")
        if unitType == 'km':
            return "km/h"
        else:
            return "mph"


    def currentUnitString(self):
        unitType = self.get("unitType", "km")
        if unitType == 'km':
            return "km"
        else:
            return "mi"

    def currentUnitStringFullName(self):
        unitType = self.get("unitType", "km")
        if unitType == 'km':
            return "kilometers"
        else:
            return "miles"

    def currentSmallUnitString(self, short=False):
        unitType = self.get("unitType", "km")
        if unitType == 'km':
            if short:
                return "m"
            else:
                return "meters"
        else:
            if short:
                return "ft"
            else:
                return "feet"

    def currentSpeedUnitToMS(self, currentSpeedUnit):
        """convert current speed unit to meters per second"""
        unitType = self.get("unitType", "km")
        if unitType == 'km':
            return currentSpeedUnit * 0.277778
        else:
            return currentSpeedUnit * 0.44704

    def getCurrentTimeString(self, timeFormat=None):
        """return a string with current time, the format can be set or a system defined one is used"""
        if timeFormat is None:
            timeFormat = self.get('currentTimeFormat', '24h')
        if timeFormat == "12h":
            return time.strftime("%I:%M %p")
        else:
            return time.strftime("%H:%M")

    def getTimeHashString(self):
        return time.strftime("%Y%m%d#%H-%M-%S", time.gmtime())

    def getNotMovingSpeedKM(self):
        return self.notMovingSpeed

    def moving(self):
        """return
           True if the current speed is above the not moving threshold,
           False if below the thresholds
           None if the current speed is unknown
           """

        currentSpeedKMH = self.get('speed', None)
        if currentSpeedKMH is not None:
            return currentSpeedKMH > self.notMovingSpeed
        else:
            # signalise that we can't decide this
            return None

    #
    # Descriptions of units.  Each tuple gives the short (abbreviated)
    # name of the unit, the long name in singular and plural forms, and
    # the conversion factor for turning meters into that unit (by
    # multiplication).
    #
    meters = ('m', 'meter', 'meters', 1)
    kilometers = ('km', 'kilometer', 'kilometers', 1.0 / 1000)
    feet = ('ft', 'foot', 'feet', 1.0 / footInMeters)
    yards = ('yd', 'yard', 'yards', 1.0 / yardInMeters)
    miles = ('mi', 'mile', 'miles', 1.0 / mileInMeters)
    #
    # Table of how to round.  There is one dictionary entry for each
    # unit type.  Each entry contains a sorted list of tuples
    # (see below).  The first element of the tuple is a distance in
    # METERS (even for units of mi).  The table is searched in order;
    # the first entry where tuple[0] is greater than the distance will
    # be the one used.  If tuple[0] is None, then that entry applies to
    # all distances not already handled.
    #
    # Each tuple has 4 elements.  Tuple[0] is the trigger distance, as
    # given above.  Tuple[1] is itself a tuple, one of the unit
    # descriptions from just above.  Tuple[2] and tuple[3] are used in
    # rounding, as explained below.
    #
    # Rounding is done by dividing the final distance (in the output
    # units) by tuple[2], rounding to the number of digits given in
    # tuple[3] (negative values are accepted, as in the round()
    # function), and multiplying by tuple[2] again.  However, if
    # tuple[2] is zero, the output is forced to exactly zero instead of
    # being rounded.
    #
    # All of this should become clearer from the table entries themselves.
    #
    humanRoundTable = {'km': [
        (10, meters, 0, 0), # Short distances become 0
        (100, meters, 5, 0), # 10-100 round to nearest 5
        (300, meters, 50, 0), # 100-300 round to 50
        (1000, meters, 1, -2), # Under 1 km round to 100 m
        (10000, kilometers, 1, 1), # Under 10 km round to 0.1 km
        (100000, kilometers, 1, 0), # 10-100 km round to 1 km
        (None, kilometers, 1, -1)  # Over 100 km round to 10 km
    ],
                       'mile': [
                           (30 * footInMeters, feet, 0, 0), # Short distances become 0
                           (0.1 * mileInMeters, feet, 20, 0), # 30 feet to 0.1 mile round to 20 ft
                           (10 * mileInMeters, miles, 1, 1), # Under 1 mile round to 0.1 mi
                           (100 * mileInMeters, miles, 1, 0), # 10-100 miles round to 1 mi
                           (None, miles, 1, -1)  # Over 100 mi round to 10 mi
                       ]}

    def humanRound(self, distance):
        """round a distance (given in meters) to a human-friendly form.
           returns a triple (rounded, shortUnits, longUnits) giving the rounded
           result and the short and long unit names.
        """
        unitType = self.get('unitType', 'km')
        if unitType not in self.humanRoundTable:
            unitType = 'km'
        for tuple in self.humanRoundTable[unitType]:
            if tuple[0] is None or tuple[0] > distance:
                break
        unitDescription = tuple[1]
        if tuple[2] == 0:
            distance = 0
        else:
            distance *= float(unitDescription[3])
            distance = round(distance / tuple[2], tuple[3]) * tuple[2]
        distanceString = str(distance)
        if '.' in distanceString:
            distanceString = distanceString.rstrip('0').rstrip('.')
        if distanceString == '1':
            long = unitDescription[1]
        else:
            long = unitDescription[2]
        return distanceString, unitDescription[0], long

    def getCurrentUnit(self, short=True):
        """return a dict containing unit names corresponding to the current
        unit configuration"""

        #TODO: cache the result & watch for option changes ?
        unitType = self.get("unitType", "km")
        unitTypeImperialSmall = self.get("unitTypeImperialSmall", "yards")

        if unitType == 'km':
            return self.unitTable['km']
        else: # imperial units
            if unitTypeImperialSmall == 'feet':
                return self.unitTable['milesFeet']
            else: # default - yards
                return self.unitTable['miles']


class Unit(object):
    """represents an unit of distance in several denominations and name types"""

    def __init__(self, small, normal, type=None, subType=None):
        # P = plural
        self.smallShort, self.small, self.smallP = small
        self.normalShort, self.normal, self.normalP = normal
        self.type = type
        self.subType = subType


