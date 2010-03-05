#!/usr/bin/python
#---------------------------------------------------------------------------
# Allows notification of data-changes
#---------------------------------------------------------------------------
# Copyright 2008, Oliver White
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
  return(watchlist(m,d))

class watchlist(ranaModule):
  """Allows notification of data-changes"""
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)


  def notify(self,name, value, oldValue=None):

    # Position seen for first time, centering
    if(name == "pos" and oldValue == None):
      self.set("centreOnce", True)

    # zoom changed
    if(name == "z"):
      m = self.m.get("projection", None)
      if(m):
        m.setZoom(value)
      
    # Menu changed, so redraw
    if(name == "menu"):
      m = self.m.get("menu", None)
      if(m):
        m.resetMenu(value)
      self.set("needRedraw", True)

