#!/usr/bin/python
#----------------------------------------------------------------------------
# A module handling unit conversions and dispplaying correct units acording to current settings.
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
from base_module import ranaModule
import time

def getModule(m,d):
  return(units(m,d))

class units(ranaModule):
  """A module handling unit conversions and dispplaying correct units acording to current settings."""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    
  def m2km(self, m):
    return (m / 1000.0) # m to km

  def km2m(self, km):
    return (km * 1000) # km to m

  def km2Miles(self, km):
    return (km * 0.621371192)  # km to miles
  
  def km2CurrentUnit(self, km):
    unitType = self.get("unitType", "km")
    if unitType == 'km':
      return km
    else:
      return (km * 0.621371192)  # km to miles

  def m2CurrentUnitString(self, m):
    km = self.m2km(m)
    return self.km2CurrentUnitString(km)

  def km2CurrentUnitString(self, km, dp=None, short=True):
    """return current unit in string with unit descriptor, rounded to two decimal places"""
    unitType = self.get("unitType", "km")
    small = False
    if unitType == 'km':
      if km <= 1: # we now count in meters
        dp = 0 # no need to count the odd centimeter with current GPS accuracy
        small = True
        distance = km*1000
      else:
        distance = km
    else:
      distance = km *  0.621371192

    # rounding
    if dp==None:
      numberString = "%f" % distance
    elif dp==0:
      n = int(round(distance, 0))
      numberString = "%d" % n
    else:
      n = round(distance, dp)
      numberString = "%f" % n

    # strip trailing zeroes

    #is it a string float representation ?
    if len(numberString.split('.')) > 1: # strip possible trailing zeroes
      numberString = numberString.rstrip('.0')

    # short/lon unit name
    if unitType == 'km':
      if short:
        unitString = "km"
        smallUnitString = "m"
      else:
        unitString = "kilometers"
        smallUnitString = "meters"

      if small:
        return "%s %s" % (numberString, smallUnitString)
      else:
        return "%s %s" % (numberString, unitString)
    else:
      return "%s miles" % numberString  # km to miles

  def km2CurrentUnitStringFullName(self, km):
    """return current unit in string with unit descriptor, rounded to two decimal places"""
    unitType = self.get("unitType", "km")
    if unitType == 'km':
      if km >= 1:
        return "%1.2f kilometers" % km
      else:
        return "%000.0f meters" % (km * 1000.0)
    else:
      return "%1.2f miles" % (km * 0.621371192)  # km to miles
    
  def km2CurrentUnitPerHourString(self, km, dp=None, short=True):
    """return a string with the speed rouded to the current unit
       %f1.2 speed_unit_per_hour
       example: 5.25 kmh
       """

    unitType = self.get("unitType", "km")

    # unit conversion
    if unitType == km:
      speed = km
    else:
      speed = km * 0.621371192

    # rounding
    if dp==None:
      numberString = "%1.0f" % speed
    elif dp==0:
      n = int(round(speed, 0))
      numberString = "%d" % n
    else:
      n = round(speed, dp)
      numberString = "%f" % n

    # short/long unit description
    if unitType == 'km':
      if short:
        unitString = "kmh"
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
    """return a string with the speed rouded to two decimal places with the current unit
       %f1.2 speed_unit_per_hour
       example: 5.25 kmh
       """
    unitType = self.get("unitType", "km")
    if unitType == 'km':
      return "%1.0f kmh" % km
    else:
      return "%1.0f mph" % (km * 0.621371192) #  km to miles

  def currentUnitPerHourString(self):
    unitType = self.get("unitType", "km")
    if unitType == 'km':
      return "kmh"
    else:
      return "mph"


  def currentUnitString(self):
    unitType = self.get("unitType", "km")
    if unitType == 'km':
      return "km"
    else:
      return "miles"

  def currentUnitStringFullName(self):
    unitType = self.get("unitType", "km")
    if unitType == 'km':
      return "kilometers"
    else:
      return "miles"

  def currentSpeedUnitToMS(self, currentSpeedUnit):
    "convert current speed unit to meters per second"
    unitType = self.get("unitType", "km")
    if unitType == 'km':
      return currentSpeedUnit * 0.277778
    else:
      return currentSpeedUnit * 0.44704

  def getCurrentTimeString(self, timeFormat=None):
    """return a string with current time, the format can be set or a system defined one is used"""
    if timeFormat == None:
      timeFormat = self.get('currentTimeFormat', '24h')
    if timeFormat == "12h":
      return time.strftime("%I:%M %p")
    else:
      return time.strftime("%H:%M")


if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
