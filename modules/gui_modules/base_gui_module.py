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
    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
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

    def handleMessage(self, message, messageType, args):
        if message == "fullscreen" and messageType == "ms":
            if args == "toggle":
                self.toggleFullscreen()
            elif args == "enable":
                self.setFullscreen(True)
            elif args == "disable":
                self.setFullscreen(False)
            else:
                self.log.error("incorrect fullscreen message argument: %s", args)

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
            deviceType = self.modrana.dmod.device_type
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
                "multiplier" : (1, 1.5)[i],
                "spacing" : (8, 12)[i],
                "spacingBig" : (16, 24)[i]
            },
            "button" : {
                "selector" : {
                    "width" : (200, 300)[i],
                    "height" : (80, 120)[i],
                },
                "icon" : {
                    "size" : (80, 120)[i]
                },
                "iconGrid" : {
                    "size" : (100, 150)[i],
                    "radius" : (10, 15)[i],
                    "textSizePortrait" : (42, 60)[i],
                    "textSizeLandscape" : (36, 54)[i]
                },
                "generic" : {
                    "height" : (60, 90)[i]
                }
            },
            "dialog" : {
                "item" : {
                    "height" : (80, 120)[i]
                }
            },

            "map": {
                "button": {
                    "size": (72, 108)[i],
                    "margin": (16, 24)[i],
                    "spacing": (16, 24)[i],
                },
                "scaleBar" : {
                    "border" : (2, 3)[i],
                    "height" : (4, 6)[i],
                    "fontSize" : (24, 36)[i],
                },
                "tracklogTrace" : {
                    "width" : (10, 15)[i],
                    "color" : "blue",
                },
            },
            "listView" : {
                "spacing" : (8, 24)[i],
                "cornerRadius" : (8, 12)[i],
                "itemBorder" : (20, 30)[i],
            }
        }
        return style

    def getConstants(self):
        if self.modrana.dmod.device_id == "jolla":
            defaultTheme = "silica"
        else:
            defaultTheme = "default"

        C = {
            "style": self._getStyleConstants(),
            "default" : {
                "theme" : defaultTheme,
                "routingProvider" : constants.DEFAULT_ROUTING_PROVIDER,
                "autoDownloadThreadCount" : constants.DEFAULT_THREAD_COUNT_AUTOMATIC_TILE_DOWNLOAD
            }
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

    def shouldStartInFullscreen(self):
        """Report if the GUI should start in fullscreen
        * could be required by device module
        * could be requested by CLI flag
        * could be enabled in options

        :returns: if GUI should start in fullscreen or not
        :rtype: bool
        """
        return any(
            (self.modrana.dmod.start_in_fullscreen,
               self.modrana.args.fullscreen,
               self.get("start_in_fullscreen", False))
        )

    def showQuitButton(self):
        """Report if the GUI should show a quit button
        * could be required by device module
        * could be enabled in options

        :returns: if GUI should show quit button or not
        :rtype: bool
        """
        return any((self.dmod.needs_quit_button, self.get("showQuitButton", False)))
