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
class RanaModule(object):
    def __init__(self, modules=None, data=None, initInfo=None):
        if not initInfo: initInfo = {}
        if not data: data = {}
        if not modules: modules = {}
        self.m = modules
        self.d = data
        self.status = ''
        self.modrana = initInfo.get('modrana') # this is modRana
        # bind the get set and watch methods to the "kernel" :D
        self.get = self.modrana.get
        self.set = self.modrana.set
        self.optionsKeyExists = self.modrana.optionsKeyExists
        self.watch = self.modrana.watch
        self.removeWatch = self.modrana.removeWatch

        self.moduleName = initInfo.get('name', "")
        self.device = initInfo.get('device', "")
        self.mainWindow = None # will be provided by modrana.py (a gdk.Window) -> the Widget main window
        self.topWindow = None # will be provided by modrana.py (a gdk.Window) -> the modRana top window
        self.dmod = None # will be provided by modrana.py (a device specific module) -> current device specific module instance

    def module_exists(self, module):
        """Test whether a named module is loaded"""
        return self.m.get(module, None) is not None

    def notify(self, message, msTimeout=0, icon=""):
        notify = self.m.get('notification')
        if notify:
            # the notification module counts timeout in seconds
            sTimeout = msTimeout / 1000.0
            notify.handleNotification(message, sTimeout, icon)

    def getStatus(self):
        return self.status

    # Following can be overridden
    def firstTime(self):
        """Runs on application start (after all other modules are loaded)"""
        pass

    def update(self):
        """Regular updates (several per second)"""
        pass

    def beforeDraw(self):
        """Before a screen is redrawn (don't use this for regular updates)"""
        pass

    def drawMenu(self, cr, menuName, args=None):
        """Drawing, in menu mode.  Only handle this if you know your menu is active"""
        pass

    def drawMap(self, cr):
        """Draw the base map"""
        pass

    def drawMapOverlay(self, cr):
        """Draw overlay that's part of the map"""
        pass

    def drawScreenOverlay(self, cr):
        """Draw overlay that's on top of all maps"""
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
            print("Sending message: " + message)
            m.routeMessage(message)
        else:
            print("No message handler, cant send message.")

    def shutdown(self):
        """
        Program is about to shutdown
        (don't rely solely on this for anything important like saving someone's tracklog!)
        """
        pass
