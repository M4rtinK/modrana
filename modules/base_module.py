# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Base class for Rana modules
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
import logging

class RanaModule(object):
    def __init__(self, modrana, moduleName, importName):
        self.modrana = modrana # this is modRana
        # bind the persistent dictionary
        self.d = self.modrana.d
        # bind the module dictionary
        self.m = self.modrana.m
        self.status = ''
        # and also bind the get set and watch methods to the "kernel" :D
        self.get = self.modrana.get
        self.set = self.modrana.set
        self.optionsKeyExists = self.modrana.optionsKeyExists
        self.watch = self.modrana.watch
        self.removeWatch = self.modrana.removeWatch
        self._moduleName = moduleName
        self._importName = importName
        self.mainWindow = None # will be provided by modrana.py (a gdk.Window) -> the Widget main window
        self.topWindow = None # will be provided by modrana.py (a gdk.Window) -> the modRana top window
        self.dmod = self.modrana.dmod # will be provided by modrana.py (a device specific module) -> current device specific module instance
        self._log = self._getLog()

    @property
    def moduleName(self):
        return self._moduleName

    @property
    def log(self):
        return self._log

    def module_exists(self, module):
        """Test whether a named module is loaded"""
        return self.m.get(module, None) is not None

    def notify(self, message, msTimeout=0, icon=""):
        # forward the notification to the main singleton modRana class
        self.modrana.notify(message, msTimeout, icon)

    def getStatus(self):
        return self.status

    # Following can be overridden
    def firstTime(self):
        """Runs on application start (after all other modules are loaded)"""
        pass

    def handleMessage(self, message, messageType, args):
        """Handles a message from another module, or in response to user action"""
        pass

    def dragEvent(self, startX, startY, dx, dy, x, y):
        """Handles notification of a drag event"""
        pass

    def handleResize(self, newW, newH):
        """Handles notification of a window resize (also fullscreen/unfullscreen)"""
        pass

    def handleTextEntryResult(self, key, result):
        """Handle a text returned from text input interface"""
        pass

    def sendMessage(self, message):
        m = self.m.get("messages", None)
        if m is not None:
            self.log.info("Sending message: " + message)
            m.routeMessage(message)
        else:
            self.log.error("No message handler, cant send message.")

    def _getLog(self):
        """Return module specific logger instance

        NOTE: This method can be overridden by subclasses
              to customize logger behavior

        :returns: logging.Logger instance
        :rtype: logging.Logger
        """
        return logging.getLogger("mod.%s" % self.moduleName)

    def shutdown(self):
        """
        Program is about to shutdown
        (don't rely solely on this for anything important like saving someone's tracklog!)
        """
        pass
