#!/usr/bin/python
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
from base_module import ranaModule
import time
import gtk

def getModule(m,d):
  return(display(m,d))

class display(ranaModule):
  """A platform independent display device control module"""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.fullscreen = False
    """according to documentation on:
    (http://wiki.maemo.org/PyMaemo/Python-osso_examples#Device_State),
    every display_blanking_pause() call pauses screenblank for 60 secconds,
    to make sure, we request every 30 secconds"""
    self.pauseScreenBlankingEnabled = False
    self.screenBlankPauseInterval = 30
    self.lastScreenblankPauseRequest = time.time()

    self.checkMethod = None
    self.checkConditions = False
    self.checkConditionsInterval = 5 # how often to check blanking conditions
    self.lastCheckConditions = time.time()
  def firstTime(self):
    self.checkScreenBlankingMode() # check the screen blanking mode on startup

    # connect to window state signals
    self.modrana.topWindow.connect('window-state-event', self.windowStateChangedCallback)
    self.modrana.topWindow.connect('visibility-notify-event', self.visibilityChangedCallback)

  def handleMessage(self, message, type, args):
    if message=="fullscreen" and type == "ms":
      if args == "toggle":
        self.fullscreenToggle()
    elif message=="blankingModeChanged":
      self.checkScreenBlankingMode() # check if screen blanking changed
    elif message=="checkShowRedrawTime":
      state = self.get('showRedrawTime', False)
      self.modrana.showRedrawTime = state

  def enableRedraw(self,reason="not given"):
    """enable window redrawing"""
    self.modrana.redraw=True
    print "display: redraw ON (%s)" % reason
    self.set('needRedraw',True) # make sure the screen is refreshed

  def disableRedraw(self,reason="not given"):
    """disable window redrawing"""
    self.modrana.redraw=False
    print "display: redraw OFF (%s)" % reason

  def windowStateChangedCallback(self, window, event):
    if event.new_window_state == gtk.gdk.WINDOW_STATE_ICONIFIED:
      self.disableRedraw(reason="window minimised")
    elif event.new_window_state == gtk.gdk.WINDOW_STATE_WITHDRAWN:
      self.disableRedraw(reason="window is hidden")
    else:
      self.enableRedraw(reason="window not hidden or minimised")

  def visibilityChangedCallback(self,window, event):
    if event.state == gtk.gdk.VISIBILITY_FULLY_OBSCURED:
      self.disableRedraw(reason="window is obscured")
    else:
      self.enableRedraw(reason="window is unobscured or partially obscured")

  def fullscreenToggle(self):
    """toggle fullscreen state"""
    if self.fullscreen == True:
          self.modrana.topWindow.unfullscreen()
          self.fullscreen = False
          self.menusSetFullscreen(self.fullscreen)
          print "going out of fullscreen"
    else:
      self.modrana.topWindow.fullscreen()
      self.fullscreen = True
      self.menusSetFullscreen(self.fullscreen)
      print "going to fullscreen"

  def menusSetFullscreen(self, value):
    """update the cached value in the menus module"""
    m = self.m.get('menu', None)
    if m:
      m.fullscreen = value

  def getFullscreenEnabled(self):
    """
    True - we are in fullscreen, False othewise
    """
    return self.fullscreen


  # * screen blanking control *

  def screenBlankingControlSupported(self):
    """report if controling the screen blanking is supported"""
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
      self.lastScreenblankPauseRequest = time.time() # update the timestamp

  def unlockScreen(self):
    self.dmod.unlockScreen()

  def checkScreenBlankingMode(self):
    if self.screenBlankingControlSupported(): # can we do this ?
      mode = self.get('screenBlankingMode', 'always')
      if mode == 'always':
        self.checkConditionsStop()
        self.screenBlankingControlStart()
        print "display: keep display ON -> always"
      elif mode == 'never':
        self.checkConditionsStop()
        self.screenBlankingControlStop()
        print "display: keep display ON -> never :)"
      elif mode == 'moving':
        self.screenBlankingControlStop()
        self.checkConditionsStart(self.checkMovement)
        print "display: keep display ON -> while moving"
      elif mode == 'movingInFullscreen':
        self.screenBlankingControlStop()
        self.checkConditionsStart(self.checkFullscreenMovement)
        print "display: keep display ON -> while moving in Fullscreen"
      elif mode == 'fullscreen':
        self.screenBlankingControlStop()
        self.checkConditionsStart(self.checkFullscreen)
        print "display: keep display ON -> while in Fullscreen"
      elif mode == 'gpsFix':
        self.screenBlankingControlStop()
        self.checkConditionsStart(self.checkGPSFix)
        print "display: keep display ON -> while there is a GPS fix"
      elif mode == 'centred':
        self.screenBlankingControlStop()
        self.checkConditionsStart(self.checkCentred)
        print "display: keep display ON -> while there is a GPS fix"

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
    if self.fullscreen:
      # OK, we are in fullscreen, check movement
      self.checkMovement()
    else:
      # we are not in fullscreen, disable blanking pause if in progress
      if self.pauseScreenBlankingEnabled:
        self.screenBlankingControlStop()

  def checkFullscreen(self):
    """check if we are in fullscreen"""
    if self.fullscreen:
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
      """moveState can be also None, which meens that speed is unknown
         in this case, we keep tha status quo"""

  def checkGPSFix(self):
    """check if we have GPS fix"""
    fix = self.get('fix', None)
    if fix != None:
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
        
  def update(self):
    if self.pauseScreenBlankingEnabled: # pause screen blanking for 60s
      currentTime = time.time()
      if (currentTime - self.lastScreenblankPauseRequest)>self.screenBlankPauseInterval:
        # reaguest to pause screen blanking for 60 secconds every 30 secconds
        self.pauseScreenBlanking()
    if self.checkConditions: # run a check for screen un/blanking conditions
      currentTime = time.time()
      if (currentTime - self.lastCheckConditions)>self.checkConditionsInterval:
        if self.checkMethod:
          self.checkMethod() # call the check method
        self.lastCheckConditions = currentTime


if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
