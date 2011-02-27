#!/usr/bin/python
#----------------------------------------------------------------------------
# Rana main GUI.  Displays maps, for use on a mobile device
#
# Controls:
#   * click on the overlay text to change fields displayed
#----------------------------------------------------------------------------
# Copyright 2007-2008, Oliver White
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
#----------------------------------------------------------------------------
#import dbus.glib
import time
startTimestamp = time.time()
import pygtk
pygtk.require('2.0')
import gobject
import gtk
import sys
import traceback
import global_device_id # used for communicating the device id to other modules
import os
from gtk import gdk
from math import radians
importsDoneTimestamp = time.time()


def update1(mapWidget):
  mapWidget.update()
  return(True)

def update2(mapWidget):
  mapWidget.checkForRedraw()
  return(True)

class MapWidget(gtk.Widget):
  __gsignals__ = { \
    'realize': 'override',
    'expose-event' : 'override',
    'size-allocate': 'override',
    'size-request': 'override',
    }
  def __init__(self):
    gtk.Widget.__init__(self)
    self.draw_gc = None
    self.dmod = None # device specific module
    self.currentDrawMethod = self.fullDrawMethod

    self.centeringDisableTreshold = 1024

    self.msLongPress = 400

    """ setting this both to 100 and 1 in mapView and gpsd fixes the arow orientation bug """
    self.timer1 = gobject.timeout_add(100, update1, self) #default 100
    self.timer2 = gobject.timeout_add(10, update2, self) #default 10
    self.timer3 = None # will be used for timing long press events
    self.d = {} # List of data
    self.m = {} # List of modules

    self.mapRotationAngle = 0 # in radians
    self.notMovingSpeed = 1 # in m/s

    self.topWindow = None

    self.redraw = True

    self.showRedrawTime = False

    # alternative map drag variables
    self.altMapDragEnabled = False
    self.altMapDragInProgress = False
    self.shift = (0,0,0,0)

    self.defaulMethodBindings() # use default map dragging method bindings

    
    global_device_id.device = device

  def loadModules(self, module_path):
    """Load all modules from the specified directory"""
    sys.path.append(module_path)
    print "importing modules:"
    start = time.clock()
    initInfo={
              'modrana': self,
              'device': global_device_id.device, # TODO: do this directly
              'name': ""
             }
    for f in os.listdir(module_path):
      if(f[0:4] == 'mod_' and f[-3:] == '.py'):
        startM = time.clock()
        name = f[4:-3]
        a = __import__(f[0:-3])
        initInfo['name'] = name
        self.m[name] = a.getModule(self.m,self.d, initInfo)
        print " * %s: %s (%1.2f ms)" % (name, self.m[name].__doc__, (1000 * (time.clock() - startM)))

    # load device specific module
    deviceModulesPath = module_path + "/device_modules/"
    sys.path.append(deviceModulesPath)
    deviceId = global_device_id.device
    deviceModuleName = "device_" + deviceId + ".py"
    if os.path.exists(deviceModulesPath + deviceModuleName):
      print "Loading device specific module for %s" % deviceId
      startM = time.clock()
      a = __import__(deviceModuleName[0:-3])
      name = 'device'
      initInfo['name'] = name
      self.m[name] = a.getModule(self.m,self.d, initInfo)
      self.dmod = self.m[name]
      print " * %s: %s (%1.2f ms)" % (name, self.m[name].__doc__, (1000 * (time.clock() - startM)))

    print "Loaded all modules in %1.2f ms, initialising" % (1000 * (time.clock() - start))

    # make sure all modules have the device module and other variables before first time
    for m in self.m.values():
      m.modrana = self # make this class accessible from modules
      m.dmod = self.dmod

    start = time.clock()
    for m in self.m.values():
      m.firstTime()
    # check if redrawing time should be printed to terminal
    if 'showRedrawTime' in self.d and self.d['showRedrawTime'] == True:
      self.showRedrawTime = True
    print "Initialization complete in %1.2f ms" % (1000 * (time.clock() - start))
      
  def beforeDie(self):
    print "Shutting-down modules"
    for m in self.m.values():
      m.shutdown()
    time.sleep(2) # leave some times for threads to shut down
    print "Shuttdown complete"
  
  def update(self):
    for m in self.m.values():
      m.update()

  def checkForRedraw(self):
    # check if redrawing is enabled
    if(self.d.get("needRedraw", False)):
      self.forceRedraw()

  def mousedown(self,x,y):
    """this signalizes start of a drag or a just a click"""
    pass
    
  def click(self, x, y, msDuration):
    """this fires after a drag is finished or mouse button released"""
    m = self.m.get("clickHandler",None)
    if m:
      m.handleClick(x,y,msDuration)
      self.update()
      
  def released(self,event):
    """mouse button has been released or
    the tapping object has been lifted up from the touchscreen"""

    #always unlock drag on release
    self.unlockDrag()

    if self.altDragEnd:
      self.altDragEnd(event)
      
  def handleDrag(self,x,y,dx,dy,startX,startY,msDuration):
    # check if centering is on
    if self.d.get("centred",True):
      fullDx = x - startX
      fullDy = y - startY
      distSq = fullDx * fullDx + fullDy * fullDy
      """ check if the drag is strong enought to disable centering
      -> like this, centering is not dsabled by pressing buttons"""
      if distSq > self.centeringDisableTreshold:
        self.d["centred"] = False # turn off centering after dragging the map (like in TangoGPS)
        self.d["needRedraw"] = True
    else:
      if self.altMapDragEnabled:
        # start simple map drag if its not already in progress
        menuName = self.d.get('menu', None)
        if menuName == None and not self.altMapDragInProgress:
          self.altDragStart(x-startX,y-startY,dx,dy)
        elif self.altMapDragInProgress:
          self.altDragHandler(x-startX,y-startY,dx,dy)
      else:
        m = self.m.get("clickHandler",None)
        if m:
          m.handleDrag(startX,startY,dx,dy,x,y,msDuration)

  def handleLongPress(self, pressStartEpoch, msCurrentDuration, startX, startY, x, y):
    """handle long press"""
    m = self.m.get("clickHandler",None)
    if m:
      m.handleLongPress(pressStartEpoch, msCurrentDuration, startX, startY, x, y)
        
  def lockDrag(self):
    """start ignoring drag events"""
    self.dragLocked = True
    
  def unlockDrag(self):
    """stop ignoring drag events"""
    self.dragLocked = False

  def forceRedraw(self):
    """Make the window trigger a draw event.  
    TODO: consider replacing this if porting pyroute to another platform"""
    self.d['needRedraw'] = False
    if self.redraw:
      try:
        self.window.invalidate_rect((0,0,self.rect.width,self.rect.height),False)
      except Exception, e:
        print "error in screen invalidating function"
        print "exception: %s" % e

  def draw(self, cr, event):
    """ re/Draw the modrana GUI """
    start = time.clock()
    # run the currently used draw method
    self.currentDrawMethod(cr,event)
    # enable redraw speed debugging
    if self.showRedrawTime:
      print "Redraw took %1.2f ms" % (1000 * (time.clock() - start))

  def fullDrawMethod(self, cr, event):
    """ this is the default drawing method
    draws all layers and should be used together with full screen redraw """

    for m in self.m.values():
      m.beforeDraw()

    menuName = self.d.get('menu', None)
    if menuName: # draw the menu
      for m in self.m.values():
        m.drawMenu(cr, menuName)
    else: # draw the map
      cr.set_source_rgb(0.2,0.2,0.2) # map background
      cr.rectangle(0,0,self.rect.width,self.rect.height)
      cr.fill()
      if (self.d.get("centred", False) and self.d.get("rotateMap", False)):
        proj = self.m['projection']
        (lat, lon) = (proj.lat,proj.lon)
        (x1,y1) = proj.ll2xy(lat, lon)
        (sx,sy,sw,sh) = self.d.get('viewport')
        x=0
        y=0
        shiftAmount = self.d.get('posShiftAmount', 0.75)
        """this value might show up as string, so we convert it to float, just to be sure"""
        floatShiftAmount = float(shiftAmount)
        shiftDirection = self.d.get('posShiftDirection', "down")
        if shiftDirection:
          if shiftDirection == "down":
            y =  sh * 0.5 * floatShiftAmount
          elif shiftDirection == "up":
            y =  - sh * 0.5 * floatShiftAmount
          elif shiftDirection == "left":
            x =  - sw * 0.5 * floatShiftAmount
          elif shiftDirection == "right":
            x =  + sw * 0.5 * floatShiftAmount
          # we dont need to do anything if direction is set to don't shift (False)
        cr.translate(x,y)
        cr.save()
        # get the speed and angle
        speed = self.d.get('speed', 0)
        angle = self.d.get('bearing', 0)

        """
        only if current direction angle and speed are known,
        submit a new angle
        like this, the map does not revert back to default orientation
        on short GPS errors
        """
        if angle and speed:
          if speed > self.notMovingSpeed: # do we look like we are moving ?
            angle = 360 - angle
            self.mapRotationAngle = radians(angle)
        cr.translate(x1,y1) # translate to the rotation center
        cr.rotate(self.mapRotationAngle) # do the rotation
        cr.translate(-x1,-y1) # translate back

        # Draw the base map, the map overlays, and the screen overlays
        try:
          for m in self.m.values():
            m.drawMap(cr)
          for m in self.m.values():
            m.drawMapOverlay(cr)
        except Exception, e:
          print "modRana main loop: an exception occured:\n"
          traceback.print_exc(file=sys.stdout) # find what went wrong
        cr.restore()
        cr.translate(-x,-y)
        for m in self.m.values():
          m.drawScreenOverlay(cr)
      else: # centering is disabled, just draw the map
        try:
          for m in self.m.values():
            m.drawMap(cr)
          for m in self.m.values():
            m.drawMapOverlay(cr)
        except Exception, e:
          print "modRana main loop: an exception occured:\n"
          traceback.print_exc(file=sys.stdout) # find what went wrong
        for m in self.m.values():
          m.drawScreenOverlay(cr)

#    if 'showRedrawTime' in self.d and self.d['showRedrawTime'] == True:

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
#    if 'showRedrawTime' in self.d and self.d['showRedrawTime'] == True:
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
#    menuName = self.d.get('menu', None)
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
#      if (self.d.get("centred", False)):
#        if self.d.get("rotateMap", False):
#
#          # get the speed and angle
#          speed = self.d.get('speed', 0)
#          angle = self.d.get('bearing', 0)
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

  def setDefaultDrag(self):
    """try to revert to the default dragging method"""
    if self.altDragRevert:
      self.altDragRevert()
    else: # just to be sure
      self.defaulMethodBindings()
      self.altMapDragEnabled = False

  def setCurrentRedrawMethod(self, method=None):
    if method == None:
      self.currentDrawMethod = self.fullDrawMethod
    else:
      self.currentDrawMethod = method


  def defaulMethodBindings(self):
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
      self.backingPixmap = gtk.gdk.Pixmap(self.window, w, h, depth=-1)

# static map image dragging #
  def staticMapDragEnable(self):
    """enable static map dragging method"""
    # first do a cleanup
    self.setDefaultDrag()

    self.d['needRedraw'] = True

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
    (sx,sy,w,h) = self.d.get('viewport')

    # store current screen content in backing pixmap
    self.backingPixmap.draw_drawable(self.gc, self.window, 0, 0, 0,0,-1,-1)
    # initiate first drag
    self.staticMapDrag(shiftX, shiftY,dx,dy)

  def staticMapDragEnd(self, event):
    """revert the changes neede for the drag"""
    proj = self.m['projection']
    (shiftX,shiftY,dx,dy) = self.shift
    proj.nudge(shiftX, shiftY)
    self.shift = (0,0,0,0)

    # disable alternative map drag
    self.altMapDragInProgress = False

    # return the defaultRedrawMethod
    self.setCurrentRedrawMethod()

    # redraw the whole screen
    self.d['needRedraw'] = True

  def staticMapDrag(self,shiftX,shiftY,dx,dy):
    """drag the map"""
    self.shift = (shiftX,shiftY,dx,dy)
    (x,y,w,h) = (self.rect.x, self.rect.y, self.rect.width, self.rect.height)
    self.d['needRedraw'] = True

  def staticMapPixmapDrag(self, cr, event):
    (x,y,w,h) = (self.rect.x, self.rect.y, self.rect.width, self.rect.height)
    (shiftX,shiftY,dx,dy) = self.shift
    self.window.draw_drawable(self.gc, self.backingPixmap, 0,0,shiftX,shiftY,-1,-1)

  def staticMapRevert(self):
    self.defaulMethodBindings()
    self.altMapDragEnabled = False
    
  def do_realize(self):
    self.set_flags(self.flags() | gtk.REALIZED)
    self.window = gdk.Window( \
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

    # alow the modules to manipulate the window TODO: do this more elegantly (using signals ?)
    for name in self.m:
      self.m[name].mainWindow = self.window
      self.m[name].topWindow = self.topWindow

  def do_size_request(self, allocation):
    pass
  def do_size_allocate(self, allocation):
    self.allocation = allocation
    if self.flags() & gtk.REALIZED:
      self.window.move_resize(*allocation)
    newW = allocation[2]
    newH = allocation[3]

    print "size allocate", allocation
    # resize the backing pixmap
    self.initGCandBackingPixmap(self.allocation.width, self.allocation.height)

    # notify all modules
    for m in self.m.values(): # enable resize handling by modules
        m.handleResize(newW, newH)
#    self.forceRedraw() # redraw window contents after resize
  def _expose_cairo(self, event, cr):
    self.rect = self.allocation
    self.d['viewport'] = (self.rect.x, self.rect.y, self.rect.width, self.rect.height)
    #self.modules['projection'].setView( \
    #  self.rect.x, 
    #  self.rect.y, 
    #  self.rect.width, 
    #  self.rect.height)
    
    if(1): # optional set clipping in cairo
      cr.rectangle(
        self.rect.x,
        self.rect.y,
        self.rect.width,
        self.rect.height)
      cr.clip()
    
    self.draw(cr,event)
  def do_expose_event(self, event):
    self.chain(event)
    cr = self.window.cairo_create()
    return self._expose_cairo(event, cr)

class GuiBase:
  """Wrapper class for a GUI interface"""
  def __init__(self, device):
    # start timing the launch
    self.timing = []
    self.addCustomTime("modRana start",startTimestamp)
    self.addCustomTime("imports done", importsDoneTimestamp)
    self.addTime("GUI creation")

    # Create the window
    win = gtk.Window()
    win.set_title('modRana')
    win.connect('delete-event', gtk.main_quit)
    self.addTime("window created")

    # press length timing
    self.lastPressEpoch = 0
    self.pressInProgress = False
    self.pressLengthTimer = None

    if(device == 'eee'): # test for use with asus eee
      win.resize(800,600)
      win.move(gtk.gdk.screen_width() - 900, 50)
    if(device == 'netbook'): # test for use with asus eee
      win.resize(800,600)
      win.move(gtk.gdk.screen_width() - 900, 50)
    elif(device == 'n900'): # test for use with nokie N900
      win.resize(800,480)
    elif(device == 'q7'): # test for use with Smart Q7
      win.resize(800,480)
      win.move(gtk.gdk.screen_width() - 900, 50)
    elif(device == 'n95'): # test for use with nokia 95
      win.resize(480,640)
      win.move(gtk.gdk.screen_width() - 500, 50)
    elif(device == 'square'): # for testing equal side displays
      win.resize(480,480)
      win.move(gtk.gdk.screen_width() - 500, 50)
    elif(device == 'ipaq'): #  for some 240*320 displays (like most old Ipaqs/PocketPCs)
      win.resize(240,320)
      win.move(gtk.gdk.screen_width() - 500, 50)
    else: # test for use with neo freerunner
      win.resize(480,640)
      win.move(gtk.gdk.screen_width() - 500, 50)
    
    # Events
    event_box = gtk.EventBox()

    event_box.connect("button_press_event", self.pressed)
    event_box.connect("button_release_event", self.released)
    event_box.connect("motion_notify_event", self.moved)
    win.add(event_box)
    
    # Create the map
    self.mapWidget = MapWidget()
    self.mapWidget.topWindow=win # make the main widown accessible from modules
    event_box.add(self.mapWidget)
    self.addTime("map widget created")

    # Finalise the window
    win.show_all()
    self.addTime("window finalized")

    # start loading modules
    self.mapWidget.loadModules('modules') # name of the folder with modules

    # add last timing checkpoint
    self.addTime("all modules loaded")

    # report startup time
    self.reportStartupTime()

    # start gtk main loop
    gtk.main()
    self.mapWidget.beforeDie()

## STARTUP TIMING ##

  def addTime(self, message):
    timestamp = time.time()
    self.timing.append((message,timestamp))
    return (timestamp)

  def addCustomTime(self, message, timestamp):
    self.timing.append((message,timestamp))
    return (timestamp)

  def reportStartupTime(self):
    if self.timing:
      print "** modRana startup timing **"

      tl = self.timing
      startupTime = tl[0][1] * 1000
      lastTime = startupTime
      totalTime = (tl[-1][1] * 1000) - startupTime
      for i in tl:
        (message, t) = i
        t = 1000 * t # convert to ms
        timeSpent = t - lastTime
        timeSinceStart = t - startupTime
        print "* %s (%1.0f ms), %1.0f/%1.0f ms" % (message, timeSpent, timeSinceStart, totalTime)
        lastTime = t
      print "** whole startup: %1.0f ms **" % totalTime
    else:
      print "* timing list empty *"



  def pressed(self, w, event):
    self.lastPressEpoch=event.time
    self.pressInProgress = True

    self.dragstartx = event.x
    self.dragstarty = event.y
    #print dir(event)
    #print "Pressed button %d at %1.0f, %1.0f" % (event.button, event.x, event.y)
    
    self.dragx = event.x
    self.dragy = event.y
    self.mapWidget.mousedown(event.x,event.y)

    if not self.pressLengthTimer:
      self.pressLengthTimer = gobject.timeout_add(50, self.checkStillPressed, event.time, time.time(), event.x,event.y)
    
  def moved(self, w, event):
    """Drag-handler"""

    self.mapWidget.handleDrag( \
      event.x,
      event.y,
      event.x - self.dragx, 
      event.y - self.dragy,
      self.dragstartx,
      self.dragstarty,
      event.time - self.lastPressEpoch)

    self.dragx = event.x
    self.dragy = event.y

  def released(self, w, event):
    self.pressInProgress = False
    self.pressLengthTimer = None
    msDuration = event.time - self.lastPressEpoch

    self.mapWidget.released(event)
    dx = event.x - self.dragstartx
    dy = event.y - self.dragstarty
    distSq = dx * dx + dy * dy
    # Adjust this to the length^2 of a gerfingerpoken on your touchscreen (1024 is for Freerunner, since it's very high resolution)
    if distSq < 1024:
      self.mapWidget.click(event.x, event.y,msDuration)

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
      self.mapWidget.handleLongPress(pressStartEpoch, dt, startX, startY, self.dragx, self.dragy)     
      return True
    else: # the press ended or a new press is in progress -> stop the timer
      return False

if __name__ == "__main__":
  """
  suported devices (for now):
  'neo' (480*640)
  'n95' (480*640)
  'eee' (800*600)
  'netbook' (800*600)
  'q7'  (800*480)
  'n900' (800*480) -> for now can also be used for the Q7 or Q5 (same resolution)
  'square' (480*480) -> this is for testing screens with equal sides
  'ipaq' (240*320) -> old Ipaqs (and and other Pocket PCs) had this resolution
  """

  print " == modRana Starting == "

  try:
    import sys
    device = sys.argv[1].lower()
    print " device string (first parameter): %s " % sys.argv[1]
  except:
    device = 'neo'
    print " no device string in first parameter, using: %s" % device

  program = GuiBase(device)

 