#!/usr/bin/python
#----------------------------------------------------------------------------
# A module handling input from keyboard, hardware buttons, sensors, etc.
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
import gtk

def getModule(m,d,i):
  return(keys(m,d,i))

class keys(ranaModule):
  """A keyboard input handling module"""
  
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    # connect the key press handler
    # TODO: do this more elegantly, eq make modRana/mapWidget catch keypress events
    self.modrana.topWindow.connect('key-press-event', self.on_key_press_event)


  def on_key_press_event(self, widget, event):
    keyName = gtk.gdk.keyval_name(event.keyval)
    print keyName
    

if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
