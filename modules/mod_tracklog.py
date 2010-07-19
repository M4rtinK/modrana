#!/usr/bin/python
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
#import re
import random
from upoints import gpx
import time
import geo

def getModule(m,d):
  return(tracklog(m,d))

class tracklog(ranaModule):
  """Record tracklogs"""
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
#    self.nodes = []
#    self.updateTime = 0
#    self.lastx = 0
#    self.lasty = 0
    self.startButtonIndex = 0
    self.loggingEnabled = False
    self.loggingPaused = False
    self.loggingStartTimestamp = None
    self.logInterval = 1 #loggin interval in secconds
    self.saveInterval = 10 #saving interval in secconds
    self.lastTimestamp = None
    self.lastSavedTimestamp = None
    self.lastCoords = None
    self.currentLogGPX = None #a GPX tree for current log
    self.currentTempLog = None #a temporary log segment before saving to file
    self.currentLogName = None #name of the current log
    self.currentLogPath = None #path to the current log
    self.maxSpeed = None
    self.avg1 = 0
    self.avg2 = 0
    self.avgSpeed = None
    self.distance = None
    self.units = self.m.get('units') #maybe this is faster ?
    self.toolsMenuDone = False

#    self.startupTimestamp = time.strftime("%Y%m%dT%H%M%S")


  def handleMessage(self, message):
    if message == "incrementStartIndex":
      self.startButtonIndex = (self.startButtonIndex+1)%2 # when we go to 2, we return to 0
    elif message == "startLogging":
      print "starting to log"
      # start a new log
      if not self.loggingEnabled:
        self.loggingEnabled = True
        print "initilizing the log file"
        self.initLog()
      # or resume an existing one
      elif self.loggingEnabled == True & self.loggingPaused == True:
        print "resuming the logging"
        self.loggingPaused = False

    elif message == "pauseLogging":
      print "pausing the logging"
      self.saveLogIncrement()
      self.loggingPaused = True

    elif message == "stopLogging":
      print "stopping the logging"
      self.stopLogging()
      
    elif message == "setNewLoggingInterval":
      print "setting new log interval"
      self.logInterval=int(self.get('tracklogLogInterval', 1))

    elif message == "setNewSavingInterval":
      print "setting new save interval"
      self.saveInterval=int(self.get('tracklogSaveInterval', 10))

    elif(message == 'nameInput'):
      entry = self.m.get('textEntry', None)
      if entry == None:
        return
      entryText = ""
      logNameEntry = self.get('logNameEntry', None)
      if logNameEntry:
        entryText = logNameEntry
      entry.entryBox(self ,'logNameEntry','Write tracklog name',entryText)
#      self.expectTextEntry = 'start'


  def handleTextEntryResult(self, key, result):
    if key == 'logNameEntry':
      self.set('logNameEntry', result)

#  def saveMinimal(self, filename):
#    try:
#      f = open(filename, "w")
#      for n in self.nodes:
#        f.write("%f,%f\n"%n)
#      f.close();
#    except IOError:
#      print "Error saving tracklog" # TODO: error reporting

  def update(self):
    if self.loggingEnabled & (not self.loggingPaused):
      currentTimestamp = time.time()

      # update the current log speed statistics
      currentSpeed = self.get('speed', None)
      if currentSpeed:
        # max speed
        if currentSpeed>self.maxSpeed:
          self.maxSpeed = currentSpeed
        # avg speed
        self.avg1 += currentSpeed
        self.avg2 += (currentTimestamp - self.lastTimestamp)
        self.avgSpeed = self.avg1/self.avg2

      if (currentTimestamp - self.lastTimestamp)>self.logInterval:
        print "updating the log"
        (lat,lon) = self.get('pos', None)
        currentPosition = (lat,lon)
        self.currentTempLog.append(currentPosition)
        self.lastTimestamp = currentTimestamp
        # update traveled distance
        currentCoords = self.get('pos', None)
        if (self.lastCoords!=None and currentCoords!=None):
          (lat1,lon1) = self.lastCoords
          (lat2,lon2) = currentCoords
          self.distance+=geo.distance(lat1,lon1,lat2,lon2)
          self.lastCoords = currentCoords

      if (currentTimestamp - self.lastSavedTimestamp)>self.saveInterval:
        print "saving log increment"
        self.saveLogIncrement()
        self.lastSavedTimestamp = currentTimestamp

  def initLog(self,type='gpx',name=None):
    """start a new log, zero the apropriate variables, etc."""
    self.loggingStartTimestamp = int(time.time())
    self.maxSpeed = 0
    self.avg1 = 0
    self.avg2 = 0
    self.avgSpeed = 0
    self.currentTempLog = []
    self.distance = 0
    tracklogFolder = self.get('tracklogFolder', None)

    if name==None:
      name = self.generateLogName()

    self.currentLogName = name

    if type=='gpx':
      self.currentLogGPX = gpx.Trackpoints()
      self.currentLogPath = tracklogFolder + name + ".gpx"
      self.saveGPXLog(self.currentLogGPX, self.currentLogPath)

    self.lastTimestamp = self.lastSavedTimestamp = int(time.time())
    self.lastCoords = self.get('pos', None)
    print "log file initialized"

  def saveGPXLog(self, GPXTracklog, path):
      f = open(self.currentLogPath,'w')
      xmlTree = self.currentLogGPX.export_gpx_file()
      xmlTree.write(f)
      f.close()


  def saveLogIncrement(self):
    """save current log increment
    TODO: support for more log types"""
    newTrackpoints = map(lambda x: gpx.Trackpoint(x[0],x[1]), self.currentTempLog)

    if len(self.currentLogGPX)==0:
      self.currentLogGPX.append(newTrackpoints)
    else:
      self.currentLogGPX[0].extend(newTrackpoints)
    self.saveGPXLog(self.currentLogGPX, self.currentLogPath)
    #the current temporary log segment has been saved to disk, we can empty it
    self.currentTempLog = []

  def generateLogName(self):
    """generate a unique name for a log"""
    timeString = time.strftime("%Y%m%d#%H-%M-%S", time.gmtime())
    prefix = "log"
    logNameEntry = self.get('logNameEntry', None)
    if logNameEntry:
      prefix = logNameEntry
    return prefix + "_" + timeString

  def stopLogging(self):
      self.saveLogIncrement()
      path = self.currentLogPath
      self.clean()
      self.loggingEnabled = False
      self.startButtonIndex=0
      # now we make the tracklog manager aware, that there is a new log
      loadTl = self.m.get('loadTracklogs', None)
      if loadTl:
        # we also set the correct cathegory ('log')
        loadTl.setTracklogPathCathegory(path, 'log')
        # refresh the list of available tracklogs
        # the list also includes info abotut the category
        # therefore we set the cathegory first
        loadTl.listAvailableTracklogs()


  def clean(self):
    """zero unneaded datastructures after logging is stoped"""
    self.currentLogGPX = None
    self.currentTempLog = None
    self.loggingStartTimestamp = None
#    self.maxSpeed = None
#    self.avgSpeed = None

#  def load(self, filename):
#    # TODO: share this with replayGpx
#    self.nodes = []
#    file = open(filename, 'r')
#    if(file):
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
#        if first: #the first coordintes are wrong co we skip them
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
      menus.clearMenu('tracklogTools', "set:menu:tracklog")

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

      # * elevation toggle
      textIconAction = [
                        ('OFF #elevation', '', 'set:tracklogLogElevation:False'),
                        ('ON #elevation', '', 'set:tracklogLogElevation:True')
                        ]
      menus.addToggleItem('tracklogTools', textIconAction, 0, None, 'tracklogToolsElevation')

      # * time toggle
      textIconAction = [
                  ('OFF #time', '', 'set:tracklogLogeTime:False'),
                  ('ON #time', '', 'set:tracklogLogTime:True')
                  ]
      menus.addToggleItem('tracklogTools', textIconAction, 0, None, 'tracklogToolsTime')
      menus.addItem('tracklogTools', 'folder#go to', 'generic', 'set:currentTracCat:log|set:menu:tracklogManager')





  def drawMenu(self, cr, menuName):
    if menuName == 'tracklog':
      # is the submenu initialized ?
      if self.toolsMenuDone == False:
        print "setting up tracklogTools menu"
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

      parent = 'main'

      """this is a alist of button parameters, all buttons can be togglable
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
                  [ [["name#enter", "generic", "tracklog:nameInput"]], 0 ],
                  [ [["tools", "tools", "set:menu:tracklogTools"]], 0 ],
                  ]


      text = ""
      if self.loggingEnabled:
        text+= "logging is ON"
      elif self.loggingPaused:
        text+= "logging paused"
      else:
        text+= "logging is OFF"

      if not self.loggingEnabled:
        text+= "|||%s" % self.generateLogName()
      else:
        text+= "|||%s" % self.currentLogName

      text+= "||logging interval %d s, saving every %d s" % (self.logInterval, self.saveInterval)
      if self.loggingStartTimestamp:
        elapsedSeconds = (int(time.time()) - self.loggingStartTimestamp)
        text+= "|elapsed time: %s" % time.strftime('%H:%M:%S', time.gmtime(elapsedSeconds))

      currentSpeed = self.get('speed',0)
      if currentSpeed:
        text+="||current speed: %s" % self.units.km2CurrentUnitPerHourString(currentSpeed)
      else:
        text+="||current speed unknown"
      if self.maxSpeed:
        avgString = self.units.km2CurrentUnitPerHourString(self.avgSpeed)
        maxString = self.units.km2CurrentUnitPerHourString(self.maxSpeed)
        text+= "||max: %s, average: %s" % (maxString, avgString)
      if self.distance:
        distanceString = self.units.km2CurrentUnitString(self.distance)
        text+= "||distance traveled %s" % distanceString

      box = (text , "set:menu:showPOIDetail")
      menus.drawSixPlusOneMenu(cr, menuName, parent, fiveButtons, box)

    else:
      return # we arent the active menu so we dont do anything
    
  def shutdown(self):
    # try to save and stop the log
    if self.loggingEnabled:
      self.stopLogging()







