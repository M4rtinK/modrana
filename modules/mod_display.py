# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# A device independent display control module
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
from modules.base_module import RanaModule
import time

# only import GKT libs if GTK GUI is used
from core import gs

if gs.GUIString == "GTK":
    import gtk


def getModule(m, d, i):
    return Display(m, d, i)


class Display(RanaModule):
    """A platform independent display device control module"""

    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)

        """according to documentation on:
        (http://wiki.maemo.org/PyMaemo/Python-osso_examples#Device_State),
        every display_blanking_pause() call pauses screenblank for 60 seconds,
        to make sure, we request it every 30 seconds"""
        self.pauseScreenBlankingEnabled = False
        self.msScreenBlankPauseIntervalMs = 30000

        self.checkMethod = None
        self.checkConditions = False
        self.checkConditionsInterval = 5 # how often to check blanking conditions
        self.lastCheckConditions = time.time()

    def firstTime(self):
        if gs.GUIString.lower() == "gtk":
            gui = self.modrana.gui
            # connect to window state signals
            gui.topWindow.connect('window-state-event', self.windowStateChangedCallback)
            gui.topWindow.connect('visibility-notify-event', self.visibilityChangedCallback)
        elif gs.GUIString.lower() in ("qml", "qt5"):
            # QML (Qt4) and Qt5 handles redrawing & window state detection from inside
            # the QML context
            pass
        else:
            self.log.warning("WARNING, unhandled GUI toolkit, redraw disable if not visible might not work")

        # check the screen blanking mode on startup
        self.checkScreenBlankingMode()
        # register blanking check update
        cron = self.m.get('cron', None)
        if cron:
            # run the callback directly for the first time
            cron.addTimeout(self._updateDisplayControlCB, self.msScreenBlankPauseIntervalMs, self,
                            "screen blanking update")

    def handleMessage(self, message, messageType, args):
        if message == "blankingModeChanged":
            self.checkScreenBlankingMode() # check if screen blanking changed
        elif message == "checkShowRedrawTime":
            state = self.get('showRedrawTime', False)
            gui = self.modrana.gui
            if gui and gui.getIDString() == "GTK":
                self.modrana.gui.setShowRedrawTime(state)

    def enableRedraw(self, reason="not given"):
        """enable window redrawing"""
        self.modrana.gui.setRedraw(True)
        self.log.info("redraw ON (%s)" % reason)
        self.set('needRedraw', True) # make sure the screen is refreshed

    def disableRedraw(self, reason="not given"):
        """disable window redrawing"""
        self.modrana.gui.setRedraw(False)
        self.log.info("redraw OFF (%s)" % reason)

    def windowStateChangedCallback(self, window, event):
        if event.new_window_state == gtk.gdk.WINDOW_STATE_ICONIFIED:
            self.disableRedraw(reason="window minimised")
        elif event.new_window_state == gtk.gdk.WINDOW_STATE_WITHDRAWN:
            self.disableRedraw(reason="window is hidden")
        else:
            self.enableRedraw(reason="window not hidden or minimised")

    def visibilityChangedCallback(self, window, event):
        if event.state == gtk.gdk.VISIBILITY_FULLY_OBSCURED:
            self.disableRedraw(reason="window is obscured")
        else:
            self.enableRedraw(reason="window is un-obscured or partially obscured")


    # * screen blanking control *

    def screenBlankingControlSupported(self):
        """report if controlling the screen blanking is supported"""
        return self.dmod.screenBlankingControlSupported()

    def usesDashboard(self):
        """this reports if the device/OS uses a dashboard
        instead of minimizing the the window out of view
        the user might want that the window updates on the dashboard or not"""
        return self.dmod.usesDashboard()


    def pauseScreenBlanking(self):
        """pause screen blanking for 30 seconds"""
        if self.dmod.screenBlankingControlSupported(): # make sure the device module really supports this
            self.dmod.pauseScreenBlanking()

    def unlockScreen(self):
        self.dmod.unlockScreen()

    def checkScreenBlankingMode(self):
        if self.screenBlankingControlSupported(): # can we do this ?
            mode = self.get('screenBlankingMode', 'always')
            if mode == 'always':
                self.checkConditionsStop()
                self.screenBlankingControlStart()
                self.log.info("keep display ON -> always")
            elif mode == 'never':
                self.checkConditionsStop()
                self.screenBlankingControlStop()
                self.log.info("keep display ON -> never :)")
            elif mode == 'moving':
                self.screenBlankingControlStop()
                self.checkConditionsStart(self.checkMovement)
                self.log.info("keep display ON -> while moving")
            elif mode == 'movingInFullscreen':
                self.screenBlankingControlStop()
                self.checkConditionsStart(self.checkFullscreenMovement)
                self.log.info("keep display ON -> while moving in Fullscreen")
            elif mode == 'fullscreen':
                self.screenBlankingControlStop()
                self.checkConditionsStart(self.checkFullscreen)
                self.log.info("keep display ON -> while in Fullscreen")
            elif mode == 'gpsFix':
                self.screenBlankingControlStop()
                self.checkConditionsStart(self.checkGPSFix)
                self.log.info("keep display ON -> while there is a GPS fix")
            elif mode == 'centred':
                self.screenBlankingControlStop()
                self.checkConditionsStart(self.checkCentred)
                self.log.info("keep display ON -> while there is a GPS fix")

    def screenBlankingControlStart(self):
        self.pauseScreenBlanking()
        self.pauseScreenBlankingEnabled = True

    def screenBlankingControlStop(self):
        self.pauseScreenBlankingEnabled = False

    def checkConditionsStart(self, method):
        self.checkMethod = method
        self.checkConditions = True

    def checkConditionsStop(self):
        self.checkMethod = None
        self.checkConditions = False

    # * window visibility checking and redraw control *

    def checkFullscreenMovement(self):
        """check if we are in fullscreen and moving"""
        if self.modrana.gui.fullscreen:
            # OK, we are in fullscreen, check movement
            self.checkMovement()
        else:
            # we are not in fullscreen, disable blanking pause if in progress
            if self.pauseScreenBlankingEnabled:
                self.screenBlankingControlStop()

    def checkFullscreen(self):
        """check if we are in fullscreen"""
        if self.modrana.gui.fullscreen:
            # OK, we are in fullscreen, check if blanking is being paused
            if self.pauseScreenBlankingEnabled == False:
                # unlock screen
                self.unlockScreen()
                # keep screen on
                self.screenBlankingControlStart()
        else:
            # we are not in fullscreen, disable blanking pause if in progress
            if self.pauseScreenBlankingEnabled == True:
                self.screenBlankingControlStop()


    def checkMovement(self):
        """check if we are moving"""
        units = self.m.get('units', None)
        if units:
            moveState = units.moving() # check we are currently moving
            if moveState == True: # we are moving
                if self.pauseScreenBlankingEnabled == False:
                    # unlock screen
                    self.unlockScreen()
                    # keep screen on
                    self.screenBlankingControlStart()
            elif moveState == False: # we aren't moving
                if self.pauseScreenBlankingEnabled == True:
                    # don't keep screen on
                    self.screenBlankingControlStop()
            """moveState can be also None, which means that speed is unknown
               in this case, we keep tha status quo"""

    def checkGPSFix(self):
        """check if we have GPS fix"""
        fix = self.get('fix', None)
        if fix is not None:
            if fix == 0: # no fix
                if self.pauseScreenBlankingEnabled == True:
                    self.screenBlankingControlStop()
            elif fix > 0: # there is some form of GPS fix (at least some sats have been seen)
                if self.pauseScreenBlankingEnabled == False:
                    # unlock screen
                    self.unlockScreen()
                    # keep screen on
                    self.screenBlankingControlStart()

    def checkCentred(self):
        """check if we are centred on current position"""
        if self.get('centred', None):
            # OK, we are centred, check if blanking is being paused
            if self.pauseScreenBlankingEnabled == False:
                # unlock screen
                self.unlockScreen()
                # keep screen on
                self.screenBlankingControlStart()
        else:
            # we are not centred, disable blanking pause if in progress
            if self.pauseScreenBlankingEnabled == True:
                self.screenBlankingControlStop()

    def _updateDisplayControlCB(self):
        if self.pauseScreenBlankingEnabled: # pause screen blanking for 60s
            # screen blanking for 60 seconds is requested every 30 seconds
            # (on Fremantle it should be 60s, other platforms might differ)
            self.pauseScreenBlanking()
        if self.checkConditions: # run a check for screen un/blanking conditions
            currentTime = time.time()
            if (currentTime - self.lastCheckConditions) > self.checkConditionsInterval:
                if self.checkMethod:
                    self.checkMethod() # call the check method
                self.lastCheckConditions = currentTime
