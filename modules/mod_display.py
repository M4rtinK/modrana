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


def getModule(*args, **kwargs):
    return Display(*args, **kwargs)


class Display(RanaModule):
    """A platform independent display device control module"""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)

        """according to documentation on:
        (http://wiki.maemo.org/PyMaemo/Python-osso_examples#Device_State),
        every display_blanking_pause() call pauses screenblank for 60 seconds,
        to make sure, we request it every 30 seconds"""
        self.pauseScreenBlankingEnabled = False
        #self.msScreenBlankPauseIntervalMs = 30000
        self.msScreenBlankPauseIntervalMs = 1000

        self.checkMethod = None
        self.checkConditions = False
        self.checkConditionsInterval = 5 # how often to check blanking conditions
        self.lastCheckConditions = time.time()

    # * screen blanking control *

    def screenBlankingControlSupported(self):
        """report if controlling the screen blanking is supported"""
        return self.dmod.screen_blanking_control_supported

    def usesDashboard(self):
        """this reports if the device/OS uses a dashboard
        instead of minimizing the the window out of view
        the user might want that the window updates on the dashboard or not"""
        return self.dmod.uses_dashboard

    def pauseScreenBlanking(self):
        """pause screen blanking for 30 seconds"""
        if self.dmod.screen_blanking_control_supported: # make sure the device module really supports this
            self.dmod.pause_screen_blanking()

    def unlockScreen(self):
        self.dmod.unlock_screen()

    def checkScreenBlankingMode(self):
        if self.screenBlankingControlSupported: # can we do this ?
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
