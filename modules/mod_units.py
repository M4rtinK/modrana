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

def getModule(m,d):
  return(units(m,d))

class units(ranaModule):
  """A module handling unit conversions and dispplaying correct units acording to current settings."""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    
  def update(self):
    # Get and set functions are used to access global data
    self.set('num_updates', self.get('num_updates', 0) + 1)
    #print "Updated %d times" % (self.get('num_updates'))

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

  def km2CurrentUnitString(self, km):
    """return current unit in string with unit descriptor, rounded to two decimal places"""
    unitType = self.get("unitType", "km")
    if unitType == 'km':
      if km >= 1:
        return "%1.2f km" % km
      else:
        return "%000.0f m" % (km * 1000.0)
    else:
      return "%1.2f miles" % (km * 0.621371192)  # km to miles
    
  def km2CurrentUnitPerHourString(self, km):
    """return a string with the speed rouded to the current unit
       %f1.2 speed_unit_per_hour
       example: 5.25 kmh
       """
    unitType = self.get("unitType", "km")
    if unitType == 'km':
      return "%1.0f kmh" % km
    else:
      return "%1.0f mph" % (km * 0.621371192) #  km to miles

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


if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
