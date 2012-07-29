#!/usr/bin/python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Log position as GPX, draw the track traveled
#----------------------------------------------------------------------------
# Copyright 2008, Oliver White
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
import os
import geo
from core import gs
from modules import way

if gs.GUIString == "GTK":
  import gtk


def getModule(m,d,i):
  return(tracklog(m,d,i))

class tracklog(ranaModule):
  """Record tracklogs"""
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.startButtonIndex = 0
    self.loggingEnabled = False
    self.loggingPaused = False
    self.loggingStartTimestamp = None
    self.logInterval = 1 #loggin interval in seconds
    self.saveInterval = 10 #saving interval in seconds
    self.lastTimestamp = None
    self.lastSavedTimestamp = None
    self.lastCoords = None
    self.logName = None #name of the current log
    self.logFilename = None #name of the current log
    self.logPath = None #path to the current log
    # primary and secondary AOWay objects for
    # persistent log storage during logging
    self.log1 = None
    self.log2 = None
    # timer ids
    self.updateLogTimerId = None
    self.saveLogTimerId = None

    self.maxSpeed = None
    self.avg1 = 0
    self.avg2 = 0
    self.avgSpeed = None
    self.distance = None
    self.toolsMenuDone = False
    self.category='logs'
    self.traceColor = 'blue'
    self.traceIndex = 0
    self.pxpyIndex = []

#    self.startupTimestamp = time.strftime("%Y%m%dT%H%M%S")

  def handleMessage(self, message, type, args):
    if message == "incrementStartIndex":
      self.startButtonIndex = (self.startButtonIndex+1)%2 # when we go to 2, we return to 0
    elif message == "startLogging":
      print("tracklog: starting to log")
      # start a new log
      if not self.loggingEnabled:
        self.loggingEnabled = True
        print("tracklog: initializing the log file")
        self.initLog()
      # or resume an existing one
      elif self.loggingEnabled == True & self.loggingPaused == True:
        print "tracklog: resuming the logging"
        self.loggingPaused = False
      self.set('needRedraw', True)

    elif message == "pauseLogging":
      self.pauseLogging()
      self.set('needRedraw', True)

    elif message == "stopLogging":
      print("tracklog: stopping logging")
      self.stopLogging()
      self.set('needRedraw', True)

    elif message == 'nameInput':
      entry = self.m.get('textEntry', None)
      if entry is None:
        print("tracklog: error, text entry module is not loaded")
        return
      entryText = ""
      logNameEntry = self.get('logNameEntry', None)
      if logNameEntry:
        entryText = logNameEntry
      entry.entryBox(self ,'logNameEntry','Write tracklog name',entryText)
      self.set('needRedraw', True)

    elif message == 'clearTrace':
      self.pxpyIndex=[]

    elif message == 'setupColorMenu':
      m = self.m.get('showGPX', None)
      if m:
        m.setupChooseDistColorMenu('tracklog', '|tracklog:colorFromRegister|set:menu:None')

    elif message == 'colorFromRegister':
      # set the color from the color register
      colorName = self.get('distinctColorRegister', 'blue')
      self.traceColor = colorName

  def handleTextEntryResult(self, key, result):
    if key == 'logNameEntry':
      self.set('logNameEntry', result)

#  def update(self):
#    if self.loggingEnabled & (not self.loggingPaused):
#      currentTimestamp = time.time()
#
#      # update the current log speed statistics
#      currentSpeed = self.get('speed', None)
#      if currentSpeed:
#        # max speed
#        if currentSpeed>self.maxSpeed:
#          self.maxSpeed = currentSpeed
#        # avg speed
#        self.avg1 += currentSpeed
#        self.avg2 += (currentTimestamp - self.lastTimestamp)
#        self.avgSpeed = self.avg1/self.avg2
#
#      if (currentTimestamp - self.lastTimestamp)>self.logInterval:
#        print("tracklog: updating the log")
#        (lat,lon) = self.get('pos', None)
#        elevation = self.get('elevation', None) # TODO: add elevation logging support
#        currentLatLonElevTime = (lat,lon, elevation, time.strftime("%Y-%m-%dT%H:%M:%S"))
#        self.currentTempLog.append(currentLatLonElevTime)
#        self.lastTimestamp = currentTimestamp
#        # update traveled distance
#        self.storeCurrentPosition()
#        currentCoords = self.get('pos', None)
#        if self.lastCoords is not None and currentCoords is not None:
#          (lat1,lon1) = self.lastCoords
#          (lat2,lon2) = currentCoords
#          self.distance+=geo.distance(lat1,lon1,lat2,lon2)
#          self.lastCoords = currentCoords
#
#      if (currentTimestamp - self.lastSavedTimestamp)>self.saveInterval:
#        print("tracklog: saving log increment")
#        self._saveLogIncrement()
#        self.lastSavedTimestamp = currentTimestamp
#        self.set('needRedraw', True)

  def initLog(self,type='gpx',name=None):
    """start a new log, zero the appropriate variables, etc."""
    self.loggingStartTimestamp = int(time.time())
    self.maxSpeed = 0
    self.avg1 = 0
    self.avg2 = 0
    self.avgSpeed = 0
    self.currentTempLog = []
    self.distance = 0
    self.pxpyIndex = []
    tracklogFolder = self.modrana.paths.getTracklogsFolderPath()

    if name is None:
      name = self.generateLogName()

    self.logName = name

    if type=='gpx':
      """ importing the GPX module can be time consuming so import it
      when it is really needed"""
      from upoints import gpx
      self.currentLogGPX = gpx.Trackpoints()
      # set tracklog metadata
      self.currentLogGPX.name = name
      self.currentLogGPX.time = time.gmtime()

#      self.currentLogGPX.author = "modRana - a flexible GPS navigation system"
#      self.currentLogGPX.link = "http://nlp.fi.muni.cz/trac/gps_navigace"

      filename = "%s.gpx" % name
      self.logFilename = filename
      self.logPath = os.path.join(tracklogFolder, self.category, filename)

      # initialize temporary CSV log files
      path1 = os.path.join(tracklogFolder, self.category, "%s.temporary_csv_1" % name)
      path2 = os.path.join(tracklogFolder, self.category, "%s.temporary_csv_2" % name)

      log1 = way.AppendOnlyWay()
      log1.startWritingCSV(path1)
      self.log1 = log1

      log2 = way.AppendOnlyWay()
      log2.startWritingCSV(path2)
      self.log2 = log2

      # start update and save timers
      self._startTimers()

    self.lastTimestamp = self.lastSavedTimestamp = int(time.time())
    self.lastCoords = self.get('pos', None)
    print("tracklog: log file initialized")

  def pauseLogging(self):
    """pause logging"""
    if self.loggingEnabled:
      self._saveLogIncrement() # save increment
      self.loggingPaused = True # pause logging
      print('tracklog: logging paused')
    else:
      print("tracklog: can't pause logging - no logging in progress")

  def unPauseLogging(self):
    """pause logging"""
    if self.loggingEnabled:
      self._saveLogIncrement() # save increment
      self.loggingPaused = False # un-pause logging
      print('tracklog: logging un-paused')
    else:
      print("tracklog: can't un-pause logging - no logging in progress")

  def _updateLogCB(self):
    """add current position at the end of the log"""
    pos = self.get('pos', None)
    if pos and not self.loggingPaused:
      timestamp = geo.timestampUTC()
      lat, lon = pos
      elevation = self.get('elevation', None)
      self.log1.addPointLLET(lat, lon, elevation, timestamp)
      self.log2.addPointLLET(lat, lon, elevation, timestamp)

      # update statistics for the current log
      if self.loggingEnabled and (not self.loggingPaused):
        # update the current log speed statistics
        currentSpeed = self.get('speed', None)
        if currentSpeed:
          # max speed
          if currentSpeed > self.maxSpeed:
            self.maxSpeed = currentSpeed
          # avg speed
          self.avg1 += currentSpeed
          self.avg2 += (time.time() - self.lastTimestamp)
          self.avgSpeed = self.avg1/self.avg2

        # update traveled distance
        lLat, lLon = self.lastCoords
        self.distance+=geo.distance(lLat, lLon, lat, lon)
        self.lastCoords = lat, lon

  def _saveLogCB(self):
    """save the log to temporary files in storage
    (only the increment from last save needs to be stored)"""
    if not self.loggingPaused:
      self._saveLogIncrement()

  def _saveLogIncrement(self):
    """save current log increment to storage"""
    self.log1.flush()
    self.log2.flush()

  def generateLogName(self):
    """generate a unique name for a log"""
    timeString = time.strftime("%Y%m%d#%H-%M-%S", time.gmtime())
    prefix = "log"
    logNameEntry = self.get('logNameEntry', None)
    if logNameEntry:
      prefix = logNameEntry
    return prefix + "_" + timeString

  def _startTimers(self):
    """start the update and save timers"""
    cron = self.m.get('cron', None)
    if cron:
      # in milliseconds, stored as seconds
      updateTimeout = int(self.get('tracklogLogInterval', 1))*1000
      saveTimeout = int(self.get('tracklogSaveInterval', 10))*1000
      # update timer
      self.updateLogTimerId = cron.addTimeout(self._updateLogCB(), updateTimeout, self, "update tracklog with current position")
      # save timer
      self.updateLogTimerId = cron.addTimeout(self._saveLogCB(), saveTimeout, self, "save tracklog increment")
      # update timer intervals if they are changed
      # in the persistent dictionary
      self.modrana.watch('tracklogLogInterval', self._updateIntervalChangedCB)
      self.modrana.watch('tracklogSaveInterval', self._saveIntervalChangedCB)

  def _updateIntervalChangedCB(self, key, oldInterval, newInterval):
    if self.updateLogTimerId:
      cron = self.m.get('cron', True)
      interval = int(newInterval)*1000
      if cron:
        cron.modifyTimeout(self.updateLogTimerId, interval)
        print('tracklog: tracklog update interval changed to %s s' % newInterval)
      else:
        print("tracklog: error, the cron module is not loaded")

  def _saveIntervalChangedCB(self, key, oldInterval, newInterval):
    if self.updateLogTimerId:
      cron = self.m.get('cron', True)
      interval = int(newInterval)*1000
      if cron:
        cron.modifyTimeout(self.saveLogTimerId, interval)
        print('tracklog: tracklog save interval changed to %s s' % newInterval)
      else:
        print("tracklog: error, the cron module is not loaded")

  def _stopTimers(self):
    """stop the update and save timers"""
    cron = self.m.get('cron', None)
    if cron:
      cron.removeTimeout(self.updateLogTimerId)
      cron.removeTimeout(self.saveLogTimerId)
      self.saveLogTimerId = None
      self.updateLogTimerId = None

  def stopLogging(self):
    """stop logging, export the log to GPX and delete the temporary
    log files"""
    # stop timers
    self._stopTimers()

    # save current log increment to storage (in CSV)
    self._saveLogIncrement()

    # try to export the log to GPX
    # first from the primary log
    if not self.log1.saveToGPX(self.logPath):
      self.log2.saveToGPX(self.logPath) # try the secondary log

    # cleanup
    # -> this deletes the temporary log files
    # and discards the temporary AOWay objects
    self._cleanup()
    self.loggingEnabled = False
    self.startButtonIndex=0
    # now we make the tracklog manager aware, that there is a new log
    loadTl = self.m.get('loadTracklogs', None)
    if loadTl:
#        # we also set the correct category ('log')
#        loadTl.setTracklogPathCategory(path, 'log')
      loadTl.listAvailableTracklogs() #TODO: incremental addition


  def _cleanup(self, deleteTempLogs=True):
    """zero unneeded datastructures after logging is stopped"""

    if deleteTempLogs:
      self.log1.deleteFile()
      self.log2.deleteFile()

    self.log1 = None
    self.log2 = None

    self.loggingStartTimestamp = None
#    self.maxSpeed = None
#    self.avgSpeed = None


  def storeCurrentPosition(self):
    pos = self.get('pos', None)
    proj = self.m.get('projection', None)

    if pos and proj:
      (lat,lon) = pos
      (px,py) = proj.ll2pxpyRel(lat, lon)
      index = self.traceIndex
      """
      for not, latLonIndex is unsorted, if we sort it according
      to lat + lon + index to speed up filter, we would need another list in
      insert order
      """
      self.pxpyIndex.append((px,py,index))
      self.traceIndex+=1

#    proj = self.m.get('projection', None)
#    if proj:
##      (lat,lon) = self.get('pos', None)
#      (lat,lon) = (48.0,16.0)
##      print proj.ll2pxpy(lat, lon)
#      print (lat,lon)
#      (px,py) =  proj.ll2pxpy(lat, lon)
#      print (px, py)
#      (x,y) = proj.pxpy2xy(px, py)
#      print (x,y)
#      print proj.xy2ll(x, y)


#  def getVisiblePoints(self):
#    # get only the points, that are currently visible
#    proj = self.m.get('projection', None)
#    if proj:
#      print self.LatLonIndex
#      (lat1,lon1,lat2,lon2) = proj.screenBBoxLL()
#      print (lat1,lon1,lat2,lon2)
#      print "filtering"
#      # first get only point for available latitude range
#      visiblePoints = filter(lambda x: lat1 >= x[0] >= lat2, self.LatLonIndex)
#      print visiblePoints
#      visiblePoints = filter(lambda x: lon1 <= x[1] <= lon2, visiblePoints)
#      print visiblePoints
#      # now sort the list of visible points according to the index
#      visiblePoints = sorted(visiblePoints, key=lambda x: x[2])
#      print visiblePoints
#      return visiblePoints


#  def load(self, filename):
#    # TODO: share this with replayGpx
#    self.nodes = []
#    file = open(filename, 'r')
#    if(file):
#      """ importing the GPX module can be time consuming so import it
#      when it is really needed"""
#      from upoints import gpx
#      track = gpx.Trackpoints() # create new Trackpoints object
#      track.import_locations(file) # load a gpx file into it
#      for point in track[0]: #iterate over the points, track[0] is list of all points in file
#        lat = point.latitude
#        lon = point.longitude
#        self.nodes.append([lat,lon])
#      file.close()
#      self.numNodes = len(self.nodes)
#      self.set("centreOnce", True)
#      self.pos = int(self.get("replayStart",0) * self.numNodes)
      
#only for GPX 1.0, the above works for GPX 1.1
#      regexp = re.compile("<trkpt lat=['\"](.*?)['\"] lon=['\"](.*?)['\"]")
#      for text in file:
#        matches = regexp.match(text)
#        if(matches):
#          lat = float(matches.group(1))
#          lon = float(matches.group(2))
#          self.nodes.append([lat,lon])
#      file.close()

#  def scheduledUpdate(self):
#    pos = self.get('pos', None)
#    if(pos != None):
#      self.nodes.append(pos)
#      #(lat,lon) = pos
#      #print "Logging %f, %f" % (lat,lon)
#    self.saveMinimal("data/tracklogs/%s.txt" % self.startupTimestamp);
#
#  def drawMapOverlay(self, cr):
#    # Where is the map?
#    proj = self.m.get('projection', None)
#    if(proj == None):
#      return
#    if(not proj.isValid()):
#      return
#
#    # Draw all trackpoints as lines (TODO: optimisation)
#    cr.set_source_rgb(0,0,0.5)
#    first = True
#    for n in self.nodes:
#      (lat,lon) = n
#      (x,y) = proj.ll2xy(lat,lon)
#      if(proj.onscreen(x,y)):
#        if first: #the first coordinates are wrong co we skip them
#          self.line(cr, x, y)
#          first = False
#        else:
#          self.line(cr, x, y)
#
#      cr.fill()
    
  def point(self, cr, x, y):
    s = 2 #default 2
    cr.rectangle(x-s,y-s,2*s,2*s)

  def line(self, cr, x, y):
    """ draws a line from xb*yb to xe*ye """
    cr.set_line_width(5)
    #cr.set_source_rgb(0.0, 0.0, 0.8)
    cr.line_to(x,y)
    cr.stroke()
    self.lastx = x
    self.lasty = y

#    s = 2 #default 2
#    cr.rectangle(x-s,y-s,2*s,2*s)
#    last_x = x
#    last_y = y
    #print("bod")

#  def update(self):
#    # Run scheduledUpdate every second
#    t = time()
#    dt = t - self.updateTime
#    if(dt > self.get("logPeriod", 2)):
#      self.updateTime = t
#      self.scheduledUpdate()

  def initToolsMenu(self):
    """initialize the tools submenu"""
    menus = self.m.get('menu', None)
    if menus:
      # add the buttons

      # * escape button
      menus.clearMenu('tracklogTools', "set:menu:tracklog#tracklog")

      # * logging interval button

      baseAction = '|tracklog:setNewLoggingInterval'
      textIconAction = [
                        ('1 s#log every', '', 'set:tracklogLogInterval:1'+baseAction),
                        ('2 s#log every', '', 'set:tracklogLogInterval:2'+baseAction),
                        ('5 s#log every', '', 'set:tracklogLogInterval:5'+baseAction),
                        ('10 s#log every', '', 'set:tracklogLogInterval10:'+baseAction),
                        ('20 s#log every', '', 'set:tracklogLogInterval:20'+baseAction),
                        ('30 s#log every', '', 'set:tracklogLogInterval:30'+baseAction),
                        ('1 min#log every', '', 'set:tracklogLogInterval:60'+baseAction),
                        ('2 min#log every', '', 'set:tracklogLogInterval:120'+baseAction)
                        ]
      menus.addToggleItem('tracklogTools', textIconAction, 0, None, 'tracklogToolsLogInterval')
      
      # * saving interval button
      baseAction = '|tracklog:setNewSavingInterval'
      textIconAction = [
                        ('10 s#save every', '', 'set:tracklogSaveInterval:10'+baseAction),
                        ('20 s#save every', '', 'set:tracklogSaveInterval:20'+baseAction),
                        ('30 s#save every', '', 'set:tracklogSaveInterval:30'+baseAction),
                        ('1 min#save every', '', 'set:tracklogSaveInterval:60'+baseAction),
                        ('2 min s#save every', '', 'set:tracklogSaveInterval:120'+baseAction),
                        ('5 min s#save every', '', 'set:tracklogSaveInterval:300'+baseAction),
                        ('10 min s#save every', '', 'set:tracklogSaveInterval:600'+baseAction)
                        ]
      menus.addToggleItem('tracklogTools', textIconAction, 0, None, 'tracklogToolsSaveInterval')

#      # * elevation toggle
#      textIconAction = [
#                        ('OFF #elevation', '', 'set:tracklogLogElevation:False'),
#                        ('ON #elevation', '', 'set:tracklogLogElevation:True')
#                        ]
#      menus.addToggleItem('tracklogTools', textIconAction, 0, None, 'tracklogToolsElevation')
#
#      # * time toggle
#      textIconAction = [
#                  ('OFF #time', '', 'set:tracklogLogeTime:False'),
#                  ('ON #time', '', 'set:tracklogLogTime:True')
#                  ]
#      menus.addToggleItem('tracklogTools', textIconAction, 0, None, 'tracklogToolsTime')
      menus.addItem('tracklogTools', 'folder#go to', 'generic', 'set:currentTracCat:logs|set:menu:tracklogManager#tracklogManager')
      menus.addItem('tracklogTools', 'trace#clear', 'generic', 'tracklog:clearTrace|set:menu:None')
      menus.addItem('tracklogTools', 'color#change', 'generic', 'tracklog:setupColorMenu|set:menu:chooseDistColor')

  def drawMenu(self, cr, menuName, args=None):
    if menuName == 'tracklog':
      # is the submenu initialized ?
      if self.toolsMenuDone == False:
        print("tracklog: setting up tracklogTools menu")
        self.initToolsMenu()
        self.toolsMenuDone = True
      # setup the viewport
      menus = self.m.get("menu",None)
      (e1,e2,e3,e4,alloc) = menus.threePlusOneMenuCoords()
      (x1,y1) = e1
      (x2,y2) = e2
      (x3,y3) = e3
      (x4,y4) = e4
      (w1,h1,dx,dy) = alloc

      parentAction = 'set:menu:main'

      """this is a a list of button parameters, all buttons can be toggleable
      it is in this form:
      [list of string-lists for toggling, index of string-list to show]
      """

      fiveButtons=[
                  [ [
                    ["start", "start", "tracklog:incrementStartIndex|tracklog:startLogging|set:needRedraw:True"],
                    ["pause", "pause", "tracklog:incrementStartIndex|tracklog:pauseLogging|set:needRedraw:True"]
                  ], self.startButtonIndex ],
                  [ [["stop", "stop", "tracklog:stopLogging"]], 0 ],
                  [ [["split", "split", "tracklog:stopLogging|tracklog:startLogging"]], 0 ],
                  [ [["name#edit", "generic", "tracklog:nameInput"]], 0 ],
                  [ [["tools", "tools", "set:menu:tracklogTools"]], 0 ],
                  ]

      units = self.m.get('units', None)

      text = ""
      if self.loggingEnabled:
        text+= '<span foreground="green">logging is ON</span>'
      elif self.loggingPaused:
        text+= "logging paused"
      else:
        text+= '<span foreground="red">logging is OFF</span>'

      text+="\n\n"

      if not self.loggingEnabled:
        text+= "%s" % self.generateLogName()
      else:
        text+= "%s" % self.logName

      text+= "\n\nlogging interval %d s, saving every %d s" % (self.logInterval, self.saveInterval)
      if self.loggingStartTimestamp:
        elapsedSeconds = (int(time.time()) - self.loggingStartTimestamp)
        text+= "\nelapsed time: %s" % time.strftime('%H:%M:%S', time.gmtime(elapsedSeconds))

      currentSpeed = self.get('speed',0)      
      if currentSpeed:
        if units:
          currentSpeedString = units.km2CurrentUnitPerHourString(currentSpeed)
        else:
          currentSpeedString = "%f kmh" % currentSpeed
        text+="\n\ncurrent speed: <span foreground='yellow'>%s</span>" % currentSpeedString
      else:
        text+='\n\ncurrent speed <span foreground="red">unknown</span>'

      if self.maxSpeed:
        if units:
          avgString = units.km2CurrentUnitPerHourString(self.avgSpeed)
          maxString = units.km2CurrentUnitPerHourString(self.maxSpeed)
        else:
          avgString = "%f kmh" % self.avgSpeed
          maxString = "%f kmh" % self.maxSpeed
        text+= "\n\nmax: %s, average: %s" % (maxString, avgString)

      if self.distance:
        if units:
          distanceString = units.km2CurrentUnitString(self.distance, 2)
        else:
          distanceString = "%f km" % self.distance
        text+= "\ndistance traveled <span foreground='white'>%s</span>\n" % distanceString

      box = (text , "set:menu:tracklog#tracklog")
      menus.drawSixPlusOneMenu(cr, menuName, parentAction, fiveButtons, box)

    else:
      return # we aren't the active menu so we dont do anything

  def drawMapOverlay(self, cr):
    proj = self.m.get('projection', None)

    if proj and self.pxpyIndex:
#      cr.set_source_rgba(0, 0, 1, 1)
      cr.set_source_color(gtk.gdk.color_parse(self.traceColor))
      cr.set_line_width(10)

      """
      log trace drawing algorithm
      adapted from TangoGPS source (tracks.c)
      works surprisingly good :)
      TODO: use the modulo method for drawing stored tracklogs
      """

      posXY = proj.getCurrentPospxpy()
      if posXY and self.loggingEnabled and not self.loggingPaused:
        (x,y) = posXY
        cr.move_to(x,y)
      else:
        (px,py,index) = self.pxpyIndex[-1]
        (x,y) = proj.pxpyRel2xy(px, py)
        cr.move_to(x,y)

      z = proj.zoom

      if 16 > z > 10:
        modulo = 2**(16-z)
      elif z <= 10:
        modulo = 32
      else:
        modulo = 1

      maxDraw = 300
      drawCount = 0
      counter=0
#
#
      for point in reversed(self.pxpyIndex): #draw the track
        counter+=1
        if counter%modulo==0:
          drawCount+=1
          if drawCount>maxDraw:
            break
          (px,py,index) = point
          (x,y) = proj.pxpyRel2xy(px, py)
          cr.line_to(x,y)
          
      # draw a track to current position (if known):

#      print z, modulo
#      print counter, drawCount

      cr.stroke()
      cr.fill()

    
  def shutdown(self):
    # try to save and stop the log
    if self.loggingEnabled:
      self.stopLogging()







