# -*- coding: utf-8 -*-
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
from modules.base_module import ranaModule

# only import GKT libs if GTK GUI is used
from core import gs
if gs.GUIString == "GTK":
  import gtk


def getModule(m,d,i):
  return(keys(m,d,i))

class keys(ranaModule):
  """A keyboard input handling module"""
  
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)

  def firstTime(self):
    # connect the key press handler
    # TODO: make this toolkit independent
    gui = self.modrana.gui
    if gui:
      if gui.getIDString() == "GTK":
        gui.topWindow.connect('key-press-event', self.on_key_press_event)
      elif gui.getIDString() == "QML":
        pass
      else:
        print("keys: WARNING, unhandled GUI toolkit, most key shortcuts would not work")
    else:
      print("keys: GUI module not available")

  def on_key_press_event(self, widget, event):
    keyName = gtk.gdk.keyval_name(event.keyval)
    if keyName == 'F8':
      """zoom out"""
      self.sendMessage('mapView:zoomOut')
    elif keyName == 'F7':
      """zoom in"""
      self.sendMessage('mapView:zoomIn')
    print "unassigned key pressed: %s" % keyName