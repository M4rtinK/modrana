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
import logging

from core import constants

from modules.base_module import RanaModule


class GUIModule(RanaModule):
    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)
        self.msLongPress = 400
        self.subtypeId = None

    def getIDString(self):
        """
        get a unique string identifier for a GUI module
        """
        return None

    def getSubtypeId(self):
        return self.subtypeId

    def setSubtypeId(self, subtypeId):
        """the subtype id hints to the GUI module, which GUI variant to use

        The GUI module might not respect this, if it either does not support
        the given variant or it might revert to the default if the given variant fails
        to start.
        """
        self.subtypeId = subtypeId

    def resize(self, mrw, h):
        """resize the GUI to given width and height"""
        pass

    def getWindow(self):
        """return the main window"""
        pass

    def getViewport(self):
        """return a (x,y,w,h) tuple"""
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
        """report if the GUI module requires the localhost
        tileserver to run"""
        return False

    def openUrl(self, url):
        """open a given URL asynchronously"""
        # the webbrowser module should be a good default
        import webbrowser

        webbrowser.open(url)

    def getScreenWH(self):
        """In some cases, the GUI module might be able
        to get screen resolution"""
        return None

    @property
    def highDPI(self):
        """Try to guess if to show the high DPI GUI or not"""
        screenWH = self.getScreenWH()
        if screenWH:
            size = max(screenWH)
            deviceType = self.modrana.dmod.getDeviceType()
            if size > 854 and deviceType == constants.DEVICE_TYPE_SMARTPHONE:
                # high DPI smartphone
                return True
            elif size > 1024 and deviceType == constants.DEVICE_TYPE_TABLET:
                # high DPI tablet
                return True
            elif size > 1920 and deviceType == constants.DEVICE_TYPE_DESKTOP:
                # high DPI desktop
                return True
            else:
                return False
        else:
            return False

    def _getLog(self):
        guiModuleSuffix = ".".join(self._importName.split("_", 1))
        # this should turn "gui_gtk" to gui.gtk,
        # which together with the "mod" prefix should
        # result in a nice "mod.gui.gtk" logger hierarchy
        return logging.getLogger("mod.%s" % guiModuleSuffix)

    def _getStyleConstants(self):
        # as True == 1 and False == 0,
        # we use the highDPI boolean as a tuple index
        # * highDpi == False -> first value is used
        # * highDpi == True -> second value is used
        i = self.highDPI

        style = {
            "m" : (1, 2)[i], # approximate size multiplier
            "main" : {
                "multiplier" : (1, 2)[i],
                "spacing" : (8, 16)[i],
                "spacingBig" : (16, 32)[i]
            },
            "button" : {
                "selector" : {
                    "width" : (200, 400)[i],
                    "height" : (80, 160)[i],
                    },
                "icon" : {
                    "size" : (80, 160)[i]
                },
                "iconGrid" : {
                    "size" : (100, 200)[i],
                    "radius" : (10, 20)[i]
                },
                "generic" : {
                    "height" : (60, 120)[i]
                }
            },
            "dialog" : {
                "item" : {
                    "height" : (80, 160)[i]
                }
            },

            "map": {
                "button": {
                    "size": (72, 108)[i],
                    "margin": (16, 24)[i],
                    "spacing": (16, 24)[i],
                    },
                "scaleBar" : {
                    "border" : (2, 4)[i],
                    "height" : (4, 8)[i],
                    "fontSize" : (24, 48)[i],

                    },
                },
            "listView" : {
                "spacing" : (8, 16)[i],
                "cornerRadius" : (8, 16)[i],
                "itemBorder" : (20, 40)[i],
                }
        }
        return style

    def getConstants(self):
        C = {
            "style": self._getStyleConstants()
        }
        return C


    @property
    def portrait(self):
        """Report if viewport is currently in portrait
        orientation

        NOTE: square screen is considered landscape

        :returns: True if in portrait, False otherwise
        :rtype: bool
        """
        w = h = 0
        screenWH = self.getScreenWH()
        if screenWH:
            w, h = screenWH
        return w < h

    @property
    def square(self):
        """Report if viewport is a square

        NOTE: square screen is considered landscape

        :returns: True if viewport is square, False otherwise
        :rtype: bool
        """
        w = 1
        h = 0
        screenWH = self.getScreenWH()
        if screenWH:
            w, h = screenWH
        return w == h










