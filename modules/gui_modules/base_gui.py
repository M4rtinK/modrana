#!/usr/bin/python
#----------------------------------------------------------------------------
# Base class for Rana GUI modules
# * it inherits everything in the base module
# * ads some default functions and handling,
#   that can be overridden for specific devices
#----------------------------------------------------------------------------
# Copyright 2012, Martin Kolman
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

class GUIModule:
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)

  def resize(self, mrw, h):
    """resize the GUI to given width and height"""
    pass

  def getWindow(self):
    """return the main window"""
    pass

  def getViewport(self):
    """return a (x,y,w,h) tupple"""
    pass

  def setWindowTitle(self, title):
    """set the window title to a given string"""
    pass

  def getToolkit(self):
    """report which toolkit the current GUI uses"""
    return

  def getAccel(self):
    """report if current GUI supports acceleration"""
    pass

  def toggleFullscreen(self):
    pass

  def startMainLoop(self):
    """start the main loop or its equivalent"""
    pass

  def stopMainLoop(self):
    """stop the main loop or its equivalent"""
    pass


#  def getPage(self, flObject, name="", fitOnStart=True):
#    """create a page from a file like object"""
#    pass
#
#  def showPage(self, page, mangaInstance=None, id=None):
#    """show a page on the stage"""
#    pass

#  def getCurrentPage(self):
#    """return the page that is currently shown
#    if there is no page, return None"""
#    pass


  def statusReport(self):
    """report current status of the gui"""
    return "It works!"

#  def _destroyed(self):
#    self.mieru.destroy()
#
#  def _keyPressed(self, keyName):
#    self.mieru.keyPressed(keyName)


#def getGui(mieru, type="gtk",accel=True, size=(800,480)):
#  """return a GUI object"""
#  if type=="gtk" and accel:
#    import cluttergtk
#    import clutter_gui
#    return clutter_gui.ClutterGTKGUI(mieru, type, size)
#  elif type=="QML" and accel:
#    import qml_gui
#    return qml_gui.QMLGUI(mieru, type, size)







