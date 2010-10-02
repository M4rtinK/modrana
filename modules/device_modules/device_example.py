#!/usr/bin/python
#----------------------------------------------------------------------------
# Sample of a modRana device-specific module.
# It is a basic modRana module, that has some special features
# and is loaded only on the correpsponding device.
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
from base_device_module import deviceModule

def getModule(m,d):
  return(device_example(m,d))

class device_example(deviceModule):
  """A sample modRana device-specific module"""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    

if(__name__ == "__main__"):
  a = device_example({}, {})
  a.update()
  a.update()
  a.update()
