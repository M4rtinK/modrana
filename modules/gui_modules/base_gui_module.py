#!/usr/bin/python
# -*- coding: utf-8 -*-
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

from modules.base_module import ranaModule

class GUIModule(ranaModule):
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.msLongPress = 400

  def getIDString(self):
    """
    get a unique string identifier for a GUI module
    """
    return None

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

  def isFullscreen(self):
    """report if the application is in fullscreen mode"""
    pass

  def toggleFullscreen(self):
    """
    toggle fullscreen state
    """
    pass

  def setFullscreen(self, value):
    """
    set fullscreen state
    * True - go to fullscreen
    * False - unfullscreen
    """
    pass

  def enableDefaultDrag(self):
    """
    use the default map dragging implementation
    """
  pass

  def enableStaticMapDrag(self):
    """
    enable static map dragging
    eq. while dragging the map, only the area that is visible is dragged
    and the rest is not updated until the drag is finished
    (can lead to better dragging performance on slower devices at the cost of
    some eyecandy)
    """
    pass

  def setCDDragThreshold(self, threshold):
    """set the threshold which needs to be reached to disable centering while dragging
    basically, larger threshold = longer drag is needed to disable centering
    default value = 2048
    """
    pass

  def lockDrag(self):
    """
    lock map dragging
    """
    pass

  def unlockDrag(self):
    """
    unlock map dragging
    """
    pass

  def setRedraw(self, value):
    """
    set redrawing mode
    * True - redraw as usual
    * False - don't redraw application window
    * "minimized" - the application window is now minimized
    """
    pass

  def startMainLoop(self):
    """start the main loop or its equivalent"""
    pass

  def stopMainLoop(self):
    """stop the main loop or its equivalent"""
    pass

  def hasNotificationSupport(self):
    """handles notifications"""
    return False

  def notify(self, message, msTimeout=0, icon=""):
    """handle a notification"""
    pass

  def statusReport(self):
    """report current status of the gui"""
    return "It works!"

  def needsLocalhostTileserver(self):
    """
    report if the GUI module requires the localhost
    tileserver to run
    """
    return False

  def openUrl(self, url):
    """
    open a given URL asynchronously
    """
    # the webbrowser module should be a good default
    import webbrowser
    webbrowser.open(url)







