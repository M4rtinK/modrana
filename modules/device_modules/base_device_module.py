#!/usr/bin/python
#----------------------------------------------------------------------------
# Base class for Rana device-specific modules
# * it inherits everything in the base module
# * ads some default functions and handling,
#   that can be overriden for specific devices
#----------------------------------------------------------------------------
# Copyright 2007, Oliver White
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

class deviceModule(ranaModule):
  """A sample pyroute module"""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    
  def getDeviceName(self):
    return "unknown device"

  def getLogFolderPath(self):
    return "data/log/" # default log folder

  def getPOIFolderPath(self):
    return "data/poi/" # default log folder

  def screenBlankingControlSupported(self):
    """ there is no universal way to control screen blanking,
    so its off by default
    -> it can be implemented and enabled in the coresponding device module"""
    return False

#  def getAutorotationSupported(self):
#    return False
#
#  def getAutorotationenabled(self):
#    pass
#
#  def getAutorotationState(self):
#    pass
#
#  def enableAutorotation(self):
#    pass
#
#  def disableAutorotation(self):
#    pass



if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
