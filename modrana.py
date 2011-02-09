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
import pygtk
pygtk.require('2.0')
import gobject
import gtk
import sys
import traceback
import threading
import global_device_id # used for communicating the device id to other modules
import cairo
import os
#from math import sqrt
from time import clock
from time import time
from time import sleep
from gtk import gdk
from math import radians


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
    """ setting this both to 100 and 1 in mapView and gpsd fixes the arow orientation bug """
    self.timer1 = gobject.timeout_add(100, update1, self) #default 100
    self.timer2 = gobject.timeout_add(10, update2, self) #default 10
    self.d = {} # List of data
    self.m = {} # List of modules

    self.mapRotationAngle = 0 # in radians
    self.notMovingSpeed = 1 # in m/s

    self.topWindow = None

    self.redraw = True
    
#    self.mapBuffer = None
#    self.startX = 0
#    self.startY = 0
#    self.dragX = 0
#    self.dragY = 0
#    self.centerX = 0
#    self.centerY = 0

    global_device_id.device = device

  def loadModules(self, module_path):
    """Load all modules from the specified directory"""
    sys.path.append(module_path)
    print "importing modules:"
    start = clock()
    for f in os.listdir(module_path):
      if(f[0:4] == 'mod_' and f[-3:] == '.py'):
        startM = clock()
        name = f[4:-3]
        filename = "%s\\%s" % ( module_path, f[0:-3]) # with directory name, but without .py extension
        a = __import__(f[0:-3])
        self.m[name] = a.getModule(self.m,self.d)
        self.m[name].moduleName = name
        print " * %s: %s (%1.2f ms)" % (name, self.m[name].__doc__, (1000 * (clock() - startM)))

    # load device specific module
    deviceModulesPath = module_path + "/device_modules/"
    sys.path.append(deviceModulesPath)
    deviceId = global_device_id.device
    deviceModuleName = "device_" + deviceId + ".py"
    if os.path.exists(deviceModulesPath + deviceModuleName):
      print "Loading device specific module for %s" % deviceId
      startM = clock()
      name = "device"
#      filename = "%s\\%s" % ( module_path, f[0:-3]) # with directory name, but without .py extension
      a = __import__(deviceModuleName[0:-3])
      self.m[name] = a.getModule(self.m,self.d)
      self.m[name].moduleName = name
      self.dmod = self.m[name]
      print " * %s: %s (%1.2f ms)" % (name, self.m[name].__doc__, (1000 * (clock() - startM)))

#    for k in self.m.keys():
#      print k

    print "Loaded all modules in %1.2f ms, initialising" % (1000 * (clock() - start))

    # make sure all modules have the device module and other variables before first time
    for m in self.m.values():
      m.modrana = self # make this class accessible from modules
      m.dmod = self.dmod

    start = clock()
    for m in self.m.values():
      m.firstTime()
    print "Initialization complete in %1.2f ms" % (1000 * (clock() - start))
      
  def beforeDie(self):
    print "Shutting-down modules"
    for m in self.m.values():
      m.shutdown()
    sleep(2) # leave some times for threads to shut down
    print "Shuttdown complete"
  
  def update(self):
    for m in self.m.values():
      m.update()

  def checkForRedraw(self):
    # check if redrawing is enabled
    if(self.d.get("needRedraw", False)):
      self.forceRedraw()

  def mousedown(self,x,y):
    pass
    
  def click(self, x, y):
    m = self.m.get("clickHandler",None)
    if(m != None):
      m.handleClick(x,y)
      self.update()
      
  def handleDrag(self,x,y,dx,dy,startX,startY):
    m = self.m.get("clickHandler",None)
    if(m != None):
      m.handleDrag(startX,startY,dx,dy,x,y)
        
  def forceRedraw(self):
    """Make the window trigger a draw event.  
    TODO: consider replacing this if porting pyroute to another platform"""
    self.d['needRedraw'] = False
    try:
      self.window.invalidate_rect((0,0,self.rect.width,self.rect.height),False)
    except AttributeError:
      pass

  def draw(self, cr):
    start = clock()
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
        x=0
        y=0
        shiftAmount = self.d.get('posShiftAmount', 0.75)
        (sx,sy,sw,sh) = self.d.get('viewport')
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
          # we dont need to do anything if direction is set to don't shift (None)
        cr.translate(x,y)
        cr.save()
        # get the speed and angle
        speed = self.d.get('speed', 0)
        angle = self.d.get('bearing', 0)

        (lat, lon) = (proj.lat,proj.lon)
        (x1,y1) = proj.ll2xy(lat, lon)

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

    # enable redraw speed debugging
    if 'showRedrawTime' in self.d and self.d['showRedrawTime'] == True:
      print "Redraw took %1.2f ms" % (1000 * (clock() - start))

#  def draw2(self, cr1):
#    start = clock()
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
#    start1 = clock()
#    for m in self.m.values():
#      m.drawScreenOverlay(cr1)
#
#    # enable redraw speed debugging
#    if 'showRedrawTime' in self.d and self.d['showRedrawTime'] == True:
#      print "Redraw1 took %1.2f ms" % (1000 * (clock() - start))
#      print "Redraw2 took %1.2f ms" % (1000 * (clock() - start1))
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
    
    self.draw(cr)
  def do_expose_event(self, event):
    if self.redraw:
      self.chain(event)
      cr = self.window.cairo_create()
      return self._expose_cairo(event, cr)

class GuiBase:
  """Wrapper class for a GUI interface"""
  def __init__(self, device):
    # Create the window
    win = gtk.Window()
    win.set_title('modRana')
    win.connect('delete-event', gtk.main_quit)

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
    event_box.connect("button_press_event", lambda w,e: self.pressed(e))
    event_box.connect("button_release_event", lambda w,e: self.released(e))
    event_box.connect("motion_notify_event", lambda w,e: self.moved(e))
    win.add(event_box)
    
    # Create the map
    self.mapWidget = MapWidget()
    self.mapWidget.topWindow=win # make the main widown accessible from modules
    event_box.add(self.mapWidget)

    # Finalise the window
    win.show_all()

    # start loading modules
    self.mapWidget.loadModules('modules') # name of the folder with modules

    # start gtk main loop
    gtk.main()
    self.mapWidget.beforeDie()

  def pressed(self, event):
    self.dragstartx = event.x
    self.dragstarty = event.y
    #print dir(event)
    #print "Pressed button %d at %1.0f, %1.0f" % (event.button, event.x, event.y)
    
    self.dragx = event.x
    self.dragy = event.y
    self.mapWidget.mousedown(event.x,event.y)
    
  def moved(self, event):
    """Drag-handler"""

    self.mapWidget.handleDrag( \
      event.x,
      event.y,
      event.x - self.dragx, 
      event.y - self.dragy,
      self.dragstartx,
      self.dragstarty)

    self.dragx = event.x
    self.dragy = event.y
  def released(self, event):
    dx = event.x - self.dragstartx
    dy = event.y - self.dragstarty
    distSq = dx * dx + dy * dy
    # Adjust this to the length^2 of a gerfingerpoken on your touchscreen (1024 is for Freerunner, since it's very high resolution)
    if distSq < 1024:
      self.mapWidget.click(event.x, event.y)


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

 