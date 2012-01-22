#!/usr/bin/python
#----------------------------------------------------------------------------
# A modRana GTK GUI class
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

import pygtk
import time
import traceback
import sys

pygtk.require('2.0')
import gobject
import gtk
from gtk import gdk

from base_gui_module import GUIModule

def getModule(m,d,i):
  return(GTKGUI(m,d,i))

class GTKGUI(GUIModule):
  def __init__(self, m, d, i):
    GUIModule.__init__(self, m, d, i)

    # some constants
    self.msLongPress = 400

    # window state
    self.fullscreen = False

    """
    NOTE: we are calling the device module through the main class
    as it otherwise is first available in firstTime

    """

    # create the GTK window

    """when on N900, use a hildon StackableWindow, which
    enables app menu and other features on Maemo 5"""
    if self.modrana.dmod.getDeviceIDString() == 'n900':
      try:
        import hildon
        win = hildon.StackableWindow()
      except Exception, e:
        print("creating hildon stackable window failed")
        print(e)
        win = gtk.Window()
    else:
      pass
    pass
    win = gtk.Window()
    self.win = win
    win.connect("destroy", self._destroyCB)

    # resize it to preferred width x height
    (w,h) = self.modrana.dmod.getWinWH()
    self.resize(w,h)
    self.modrana.addTime("window created")
    # set title
    self.setWindowTitle("modRana")
    # connect delete event
    win.connect('delete-event', gtk.main_quit)

    ## Instantiate the main widget ##
    self.mw = MainWidget(self.modrana)
    self.mw.topWindow = win
    # make the main window accessible from modules
    self.topWindow=win
    self.modrana.addTime("map widget created")

    # Event handling
    event_box = gtk.EventBox()

    event_box.connect("button_press_event", self.mw.pressed)
    event_box.connect("button_release_event", self.mw.released)
    event_box.connect("motion_notify_event", self.mw.moved)
    win.add(event_box)

    # add redraw request watch
    self.watch('needRedraw', self.mw._checkForRedrawCB) # react on redraw requests
    # TODO: add a function for directly requesting redraw

    event_box.add(self.mw)
    # Finalise the window
    win.show_all()
    self.modrana.addTime("window finalized")

  def firstTime(self):
    # provide the main widget with possibility to react to
    # the first time call
    self.mw.firstTime()

  def getIDString(self):
    return "GTK"

  def resize(self, w, h):
    """resize the GUI to given width and height"""
    self.win.resize(w,h)

  def getWindow(self):
    """return the main window"""
    return self.win

  def getViewport(self):
    """return a (x,y,w,h) tuple"""
    pass

  def setWindowTitle(self, title):
    """set the window title to a given string"""
    self.win.set_title(title)

  def getToolkit(self):
    """report which toolkit the current GUI uses"""
    return "GTK"

  def getAccel(self):
    """report if current GUI supports acceleration"""
    return False

  def toggleFullscreen(self):
    """
     just set inverted fullscreen
     variable value
    """
    self.setFullscreen(not self.fullscreen)

  def setFullscreen(self, value):
    if value:
      self.mw.topWindow.fullscreen()
      self.fullscreen = True
    else:
      self.mw.topWindow.unfullscreen()
      self.fullscreen = False


  def enableDefaultDrag(self):
    self.mw.enableDefaultDrag()

  def enableStaticMapDrag(self):
    self.mw.enableStaticMapDrag()

  def lockDrag(self):
    """start ignoring drag events"""
    self.mw.dragLocked = True

  def setRedraw(self, value):
    self.mw.redraw = value

  def unlockDrag(self):
    """stop ignoring drag events"""
    self.mw.dragLocked = False

  def setCDDragThreshold(self, threshold):
    """set the threshold which needs to be reached to disable centering while dragging
    basically, larger threshold = longer drag is needed to disable centering
    default value = 2048
    """
    self.mw.centeringDisableThreshold = threshold

  def startMainLoop(self):
    """start the main loop or its equivalent"""
    gtk.main()

  def stopMainLoop(self):
    """stop the main loop or its equivalent"""
    gtk.main_quit()

  def shutdown(self):
    """once modRana is notified of shutdown
    it starts shutting down modules
    once it shuts down this one, it makes sure
    the GTK main loop is also shut down"""
    self.stopMainLoop()

  ## GTK specific methods ##

  def getLastFullRedrawRequest(self):
    """
    return a timestamp of last redraw request
    """
    return self.mw.lastFullRedrawRequest

  def setShowRedrawTime(self, value):
    """
    enable/disable printing how long screen
    redraw took to stdout
    """
    self.mw.showRedrawTime = value

  def getShowRedrawTime(self):
    return self.mw.showRedrawTime

  def getGTKTopWindow(self):
    return self.mw.topWindow

  def _destroyCB(self, window):
    """notify modRana that is is shutting down"""
    self.modrana.shutdown()

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

class MainWidget(gtk.Widget):
  __gsignals__ = {\
    'realize': 'override',
    'expose-event' : 'override',
    'size-allocate': 'override',
    'size-request': 'override',
    }
  def __init__(self, modrana):
    gtk.Widget.__init__(self)
    self.modrana = modrana
    self.draw_gc = None
    self.dmod = modrana.dmod # device specific module
    self.currentDrawMethod = self.fullDrawMethod

    self.centeringDisableThreshold = 2048

    # press length timing
    self.lastPressEpoch = 0
    self.pressInProgress = False
    self.pressLengthTimer = None

    # dragging
    self.dragX = 0
    self.dragY = 0

    """ setting this both to 100 and 1 in mapView and gpsd fixes the arrow
     orientation bug """
    self.timer1 = gobject.timeout_add(100, self.update, self) #default 100
    self.timer3 = None # will be used for timing long press events

    self.mapRotationAngle = 0 # in radians
    self.notMovingSpeed = 1 # in m/s

    self.topWindow = None

    self.redraw = True

    self.showRedrawTime = False

    # map center shifting variables
    self.centerShift = (0,0)

    # alternative map drag variables
    self.altMapDragEnabled = False
    self.altMapDragInProgress = False
    self.shift = (0,0,0,0)

    self.defaultMethodBindings() # use default map dragging method binding

    self.lastFullRedraw = time.time()
    self.lastFullRedrawRequest = time.time()

    # map layers
    self.mapLayers = {}
    self.notificationModule = None

    # per mode options
    # NOTE: this variable is automatically saved by the
    # options module
    self.keyModifiers = {}

    # projection module cache
    self.proj = None

  def firstTime(self):
    """called at the same time as the modules firstTime"""
    self.proj = self.modrana.getModule('projection', None)

  def shutdown(self):
    """terminate GTK main loop, which should
    trigger the modRana standard shutdown sequence,
    then terminate the GTK main loop"""
    gtk.main_quit()

  def update(self):
    """ trigger periodic module update """
    # TODO: depreciate this
    # in favor of event based and explicit update timers
    self.modrana.update()

  def get(self, key, defaultValue):
    """
    local alias for the modRana persistent dictionary get function
    """
    self.modrana.get(key, defaultValue)

  def set(self, key, value):
    """
    local alias for the modRana persistent dictionary set function
    """
    self.modrana.set(key, value)

  def _checkForRedrawCB(self, key, oldValue, newValue):
    """react to redraw requests"""
    if newValue == True:
      self.forceRedraw()

  def forceRedraw(self):
    """Make the window trigger a draw event.
TODO: consider replacing this if porting pyroute to another platform"""
    self.set('needRedraw', False)
    """ alter directly, no need to notificate
    about returning the key to default state"""

    # record timestamp
    self.lastFullRedrawRequest = time.time()

    if self.redraw:
      try:
        self.window.invalidate_rect((0,0,self.rect.width,self.rect.height),False)
      except Exception, e:
        print("error in screen invalidating function"
              "exception: %s" % e)

  def pressed(self, w, event):
    """Press-handler"""
    self.lastPressEpoch=event.time
    self.pressInProgress = True

    self.dragStartX = event.x
    self.dragStartY = event.y
    #print "Pressed button %d at %1.0f, %1.0f" % (event.button, event.x, event.y)

    self.dragX = event.x
    self.dragY = event.y

    if not self.pressLengthTimer:
      self.pressLengthTimer = gobject.timeout_add(50, self.checkStillPressed, event.time, time.time(), event.x,event.y)

  def moved(self, w, event):
    """Drag-handler"""

    self.handleDrag(\
      event.x,
      event.y,
      event.x - self.dragX,
      event.y - self.dragY,
      self.dragStartX,
      self.dragStartY,
      event.time - self.lastPressEpoch)

    self.dragX = event.x
    self.dragY = event.y

  def released(self, w, event):
    """
    mouse button has been released or
    the tapping object has been lifted up from the touchscreen
    """
    self.pressInProgress = False
    self.pressLengthTimer = None
    msDuration = event.time - self.lastPressEpoch

    #always unlock drag on release
    self.modrana.gui.unlockDrag()

    if self.altDragEnd:
      self.altDragEnd(event)

    dx = event.x - self.dragStartX
    dy = event.y - self.dragStartY
    distSq = dx * dx + dy * dy
    # Adjust this to the length^2 of a gerfingerpoken on your touchscreen (1024 is for Freerunner, since it's very high resolution)
    if distSq < 1024:
      self.click(event.x, event.y,msDuration)

  def checkStillPressed(self, pressStartEpoch, pressStartTime, startX, startY):
    """check if a press is still in progress and report:
    pressStart epoch - to differentiate presses
    duration
    start coordinates
    currentCoordinates
    if no press is in progress or another press already started, shut down the timer
    """

    """just to be sure, time out after 60 seconds
    - provided the released signal is always called, this timeout might not be necessary,
    but better be safe, than eat the whole battery if the timer is not terminated"""
    dt = (time.time() - pressStartTime)*1000
    if dt > 60000:
      print "long press timeout reached"
      return False

    if pressStartEpoch == self.lastPressEpoch and self.pressInProgress:
      self.handleLongPress(pressStartEpoch, dt, startX, startY, self.dragX, self.dragY)
      return True
    else: # the press ended or a new press is in progress -> stop the timer
      return False

  def click(self, x, y, msDuration):
    """this fires after a drag is finished or mouse button released"""
    m = self.modrana.getModule("clickHandler",None)
    if m:
      m.handleClick(x,y,msDuration)
      self.update()

  def handleDrag(self,x,y,dx,dy,startX,startY,msDuration):
    """
    handle dragging on the screen
    """
    # check if centering is on
    if self.modrana.get("centred",True):
      fullDx = x - startX
      fullDy = y - startY
      distSq = fullDx * fullDx + fullDy * fullDy
      # check if the drag is strong enough to disable centering
      # this prevents centering being disabled by pressing buttons
      if self.centeringDisableThreshold:
        if distSq > self.centeringDisableThreshold:
          self.set("centred", False) # turn off centering after dragging the map (like in TangoGPS)
          self.set("needRedraw", True)
    else:
      if self.altMapDragEnabled:
        # start simple map drag if its not already in progress
        menuName = self.modrana.get('menu', None)
        if menuName == None and not self.altMapDragInProgress:
          self.altDragStart(x-startX,y-startY,dx,dy)
        elif self.altMapDragInProgress:
          self.altDragHandler(x-startX,y-startY,dx,dy)
      else:
        m = self.modrana.getModule("clickHandler",None)
        if m:
          m.handleDrag(startX,startY,dx,dy,x,y,msDuration)

  def handleLongPress(self, pressStartEpoch, msCurrentDuration, startX, startY, x, y):
    """handle long press"""
    m = self.modrana.getModule("clickHandler",None)
    if m:
      m.handleLongPress(pressStartEpoch, msCurrentDuration, startX, startY, x, y)

  def draw(self, cr, event):
    """ re/Draw the modRana GUI """
    start = time.clock()
    # run the currently used draw method
    self.currentDrawMethod(cr,event)
    # enable redraw speed debugging
    if self.showRedrawTime:
      print "Redraw took %1.2f ms" % (1000 * (time.clock() - start))
    self.lastFullRedraw = time.time()

  def getLastFullRedraw(self):
    """
    return when the GUI was last redrawn
    """
    return self.lastFullRedraw

  def fullDrawMethod(self, cr, event):
    """
    this is the default drawing method
    draws all layers and should be used together with full screen redraw
    """

    # get all modules
    modules = self.modrana.getModules().values()
    #
    for m in modules:
      m.beforeDraw()

    menuName = self.modrana.get('menu', None)
    if menuName: # draw the menu
      menus = self.modrana.getModule('menu', None)
      if menus:
        menus.mainDrawMenu(cr, menuName)
      else:
        print("GTK GUI: error, menu module missing")
    else: # draw the map
      cr.set_source_rgb(0.2,0.2,0.2) # map background
      cr.rectangle(0,0,self.rect.width,self.rect.height)
      cr.fill()
      if (self.modrana.get("centred", False) and self.modrana.get("rotateMap", False)):
        proj = self.proj
        (lat, lon) = (proj.lat,proj.lon)
        (x1,y1) = proj.ll2xy(lat, lon)

        (x,y) = self.centerShift
        cr.translate(x,y)
        cr.save()
        # get the speed and angle
        speed = self.modrana.get('speed', 0)
        angle = self.modrana.get('bearing', 0)

        """
        only if current direction angle and speed are known,
        submit a new angle
        like this, the map does not revert back to default orientation
        on short GPS errors
        """
        if angle and speed:
          if speed > self.notMovingSpeed: # do we look like we are moving ?
            self.mapRotationAngle = angle
        cr.translate(x1,y1) # translate to the rotation center
        cr.rotate(radians(360 - self.mapRotationAngle)) # do the rotation
        cr.translate(-x1,-y1) # translate back

        # Draw the base map, the map overlays, and the screen overlays
        try:
          for m in modules:
            m.drawMap(cr)
          for m in modules:
            m.drawMapOverlay(cr)
        except Exception, e:
          print "modRana GTK main loop: an exception occurred:\n"
          traceback.print_exc(file=sys.stdout) # find what went wrong
        cr.restore()
        cr.translate(-x,-y)
        for m in modules:
          m.drawScreenOverlay(cr)
      else: # centering is disabled, just draw the map
        try:
          for m in modules:
            m.drawMap(cr)
          for m in modules:
            m.drawMapOverlay(cr)
        except Exception, e:
          print "modRana GTK main loop: an exception occurred:\n"
          traceback.print_exc(file=sys.stdout) # find what went wrong
        for m in modules:
          m.drawScreenOverlay(cr)

    # do the master overlay over everything
    self.drawMasterOverlay(cr)

  # TODO: get this to work or clean it up
  #  def draw2(self, cr1):
  #    start = time.clock()
  #
  #
  ##      cr.paint()
  ##      print cr.get_target()
  ##      print cr.get_target().get_width()
  ##      print cr.get_target().get_height()
  #
  #    mapAndMapOverlayBuffer = self.getMapAndMapOverlayBuffer()
  #    if mapAndMapOverlayBuffer:
  #      cr1.set_source_surface(mapAndMapOverlayBuffer, float(self.centerX), float(self.centerY))
  #      cr1.paint()
  #    start1 = time.clock()
  #    for m in self.m.values():
  #      m.drawScreenOverlay(cr1)
  #
  #    # enable redraw speed debugging
  #    if 'showRedrawTime' in self and self['showRedrawTime'] == True:
  #      print "Redraw1 took %1.2f ms" % (1000 * (time.clock() - start))
  #      print "Redraw2 took %1.2f ms" % (1000 * (time.clock() - start1))
  #
  #  def getMapAndMapOverlayBuffer(self):
  #    if self.mapBuffer == None:
  #      self.mapBuffer = self.drawMapAndMapOverlay()
  #    return self.mapBuffer
  #
  #  def drawMapAndMapOverlay(self):
  #    mapAndMapOverlayBuffer = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.rect.width, self.rect.height)
  #    ct = cairo.Context(mapAndMapOverlayBuffer)
  #    cr = gtk.gdk.CairoContext(ct)
  #
  #    for m in self.m.values():
  #      m.beforeDraw()
  #
  #    menuName = self.modrana.get('menu', None)
  #    if(menuName != None):
  #      for m in self.m.values():
  #        m.drawMenu(cr1, menuName)
  #    else:
  #      # map background
  #      cr.set_source_rgb(0.2,0.2,0.2)
  #      cr.rectangle(0,0,self.rect.width,self.rect.height)
  #      cr.fill()
  #
  #      cr.save()
  #      if (self.modrana.get("centred", False)):
  #        if self.modrana.get("rotateMap", False):
  #
  #          # get the speed and angle
  #          speed = self.modrana.get('speed', 0)
  #          angle = self.modrana.get('bearing', 0)
  #
  #          proj = self.m['projection']
  #          (lat, lon) = (proj.lat,proj.lon)
  #          (x1,y1) = proj.ll2xy(lat, lon)
  #
  #          """
  #          only if current direction angle and speed are known,
  #          submit a new angle
  #          like this, the map does not revert back to default orientation
  #          on short GPS errors
  #          """
  #          if angle and speed:
  #            if speed > self.notMovingSpeed: # do we look like we are moving ?
  #              angle = 360 - angle
  #              self.mapRotationAngle = radians(angle)
  #          cr.translate(x1,y1) # translate to the rotation center
  #          cr.rotate(self.mapRotationAngle) # do the rotation
  #          cr.translate(-x1,-y1) # translate back
  #
  #      # Draw the base map, the map overlays, and the screen overlays
  #      for m in self.m.values():
  #        m.drawMap(cr)
  #      cr.restore()
  #      for m in self.m.values():
  #        m.drawMapOverlay(cr)
  #
  #      return mapAndMapOverlayBuffer

  ## clean map + overlay generation reference
  #    staticMap = cairo.ImageSurface(cairo.FORMAT_ARGB32,w,h)
  #    cr1 = cairo.Context(staticMap)
  #    for m in self.m.values():
  #      m.beforeDraw()
  #    try:
  #      for m in self.m.values():
  #        m.drawMap(cr1)
  #      for m in self.m.values():
  #        m.drawMapOverlay(cr1)
  #    except Exception, e:
  #      print "modRana simple map: an exception occured:\n"
  #      traceback.print_exc(file=sys.stdout) # find what went wrong
  #      self.stopSimpleMapDrag()
  #      return
  #    self.simpleStaticMap = staticMap

  ## damage area computation reference
  #    damage = gtk.gdk.region_rectangle((x,y,w,h))
  #    keep = gtk.gdk.region_rectangle((dx,dy,w,h))
  #    damage.subtract(keep)


  ## FASTER MAP DRAGGING ##

  def enableDefaultDrag(self):
    """try to revert to the default dragging method"""
    if self.altDragRevert:
      self.altDragRevert()
    else: # just to be sure
      self.defaultMethodBindings()
      self.altMapDragEnabled = False

  def setCurrentRedrawMethod(self, method=None):
    if method == None:
      self.currentDrawMethod = self.fullDrawMethod
    else:
      self.currentDrawMethod = method


  def defaultMethodBindings(self):
    """revert drag method bindings to default state"""
    self.altDragStart = None # alternative map drag enabler
    self.altDragHandler = None # alternative map drag handler
    self.altDragEnd = None
    self.altDragRevert = None # reverts the current alt map drag to default
    self.currentDrawMethod = self.fullDrawMethod

  def initGCandBackingPixmap(self,w,h):
    if self.window:
      self.gc = self.window.new_gc(background=(gtk.gdk.color_parse('white')))
      self.gc.set_clip_rectangle(gtk.gdk.Rectangle(0, 0, w, h))
      self.backingPixmap = gtk.gdk.Pixmap(self.window, int(w), int(h), depth=-1)

  # static map image dragging #
  def enableStaticMapDrag(self):
    """enable static map dragging method"""
    # first do a cleanup
    self.enableDefaultDrag()

    self.modrana.set('needRedraw', True)

    # then bind all relevant methods to variables
    self.altDragStart = self.staticMapDragStart
    self.altDragEnd = self.staticMapDragEnd
    self.altDragHandler = self.staticMapDrag
    self.altDragRevert = self.staticMapRevert
    # enable alternative map drag
    self.altMapDragEnabled = True

  def staticMapDragStart(self,shiftX,shiftY,dx,dy):
    """start the simple map dragging procedure"""
    self.altMapDragInProgress = True
    self.setCurrentRedrawMethod(self.staticMapPixmapDrag)
    # get the map and overlay
    try:
      (sx,sy,w,h) = self.modrana.get('viewport', None)
    except TypeError:
      print "gtk gui: viewport not available"
      return

    # store current screen content in backing pixmap
    self.backingPixmap.draw_drawable(self.gc, self.window, 0, 0, 0,0,-1,-1)
    # initiate first drag
    self.staticMapDrag(shiftX, shiftY,dx,dy)
    self.modrana.set('needRedraw',True)

  def staticMapDragEnd(self, event):
    """revert the changes needed for the drag"""
    proj = self.proj
    (shiftX,shiftY,dx,dy) = self.shift
    proj.nudge(shiftX, shiftY)
    self.shift = (0,0,0,0)

    # disable alternative map drag
    self.altMapDragInProgress = False

    # return the defaultRedrawMethod
    self.setCurrentRedrawMethod()

    # redraw the whole screen
    self.modrana.set('needRedraw',True)

  def staticMapDrag(self,shiftX,shiftY,dx,dy):
    """drag the map"""
    self.shift = (shiftX,shiftY,dx,dy)
    (x,y,w,h) = (self.rect.x, self.rect.y, self.rect.width, self.rect.height)
    self.modrana.set('needRedraw',True)

  def staticMapPixmapDrag(self, cr, event):
    (x,y,w,h) = (self.rect.x, self.rect.y, self.rect.width, self.rect.height)
    (shiftX,shiftY,dx,dy) = self.shift
    self.window.draw_drawable(self.gc, self.backingPixmap, 0,0,int(shiftX),int(shiftY),-1,-1)

  def staticMapRevert(self):
    """revert changes needed for static map dragging"""
    self.defaultMethodBindings()
    self.altMapDragEnabled = False

  def do_realize(self):
    self.set_flags(self.flags() | gtk.REALIZED)
    self.window = gdk.Window(\
      self.get_parent_window(),
      width = self.allocation.width,
      height = self.allocation.height,
      window_type = gdk.WINDOW_CHILD,
      wclass = gdk.INPUT_OUTPUT,
      event_mask = self.get_events() | gdk.EXPOSURE_MASK)
    self.window.set_user_data(self)
    self.style.attach(self.window)
    self.style.set_background(self.window, gtk.STATE_NORMAL)
    self.window.move_resize(*self.allocation)

    # initialize resources needed for fast map dragging support
    self.initGCandBackingPixmap(self.allocation.width, self.allocation.height)

  def do_size_request(self, allocation):
    pass

  def do_size_allocate(self, allocation):
    """
    handle new window size allocation
    """
    self.allocation = allocation
    self.rect = self.allocation
    self._updateViewport()

    if self.flags() & gtk.REALIZED:
      self.window.move_resize(*allocation)
    newW = allocation[2]
    newH = allocation[3]

    print "GTK GUI: size allocation", allocation
    # resize the backing pixmap
    self.initGCandBackingPixmap(self.allocation.width, self.allocation.height)

    # notify all modules
    # TODO: move this somewhere else ?
    for m in self.modrana.getModules().values(): # enable resize handling by modules
      m.handleResize(newW, newH)
    self.forceRedraw() # redraw window contents after resize

  def _updateViewport(self):
    """update the current viewport in the global persistent dictionary"""
    self.modrana.set('viewport', (self.rect.x, self.rect.y, self.rect.width, self.rect.height))

  def _expose_cairo(self, event, cr):
    """redraw screen with Cairo"""
    # set clipping in cairo
    cr.rectangle(
      self.rect.x,
      self.rect.y,
      self.rect.width,
      self.rect.height)
    cr.clip()

    self.draw(cr,event)

  def do_expose_event(self, event):
    """handle screen redraw"""
    self.chain(event)
    cr = self.window.cairo_create()
    return self._expose_cairo(event, cr)

  # * MASTER OVERLAY *
  # master overlay needs to be over all layers
  # and is used mainly by notifications

  def drawMasterOverlay(self, cr):
    if self.notificationModule:
      self.notificationModule.drawMasterOverlay(cr)
