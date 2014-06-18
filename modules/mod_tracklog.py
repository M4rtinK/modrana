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
from modules.base_module import RanaModule
import shutil
import glob
import time
import os
from collections import deque
from core import geo
from core import way
from core import gs

if gs.GUIString == "GTK":
    import gtk

DONT_ADD_TO_TRACE_THRESHOLD = 1
# if a point is less distant from the last
# point added to the trace than DONT_ADD_TO_TRACE_THRESHOLD
# it is not added to the trace point list
#
# Usage: to get rid of points that have very similar coordinates,
# that are generated when for example waiting
# at teh traffic lights
#
# NOTE: all points are still stored, just not drawn


def getModule(m, d, i):
    return Tracklog(m, d, i)


class Tracklog(RanaModule):
    """Record tracklogs"""

    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)
        self.loggingEnabled = False
        self.loggingPaused = False
        self.loggingStartTimestamp = None
        self.logInterval = 1 #loggin interval in seconds
        self.saveInterval = 10 #saving interval in seconds
        self.lastUpdateTimestamp = None
        self.lastCoords = None
        self.logName = None #name of the current log
        self.logFilename = None #name of the current log
        self.logPath = None #path to the current log
        self.currentTempLog = []
        # primary and secondary AOWay objects for
        # persistent log storage during logging
        self.log1 = None
        self.log2 = None
        # timer ids
        self.updateLogTimerId = None
        self.saveLogTimerId = None
        # statistics
        self.maxSpeed = None
        self.avg1 = 0
        self.avg2 = 0
        self.avgSpeed = None
        self.distance = None
        self.toolsMenuDone = False
        self.category = 'logs'
        # trace
        self.traceColor = 'blue'
        self.lastTracePoint = None
        self.traceIndex = 0
        self.pxpyIndex = deque()

    #    self.startupTimestamp = time.strftime("%Y%m%dT%H%M%S")

    def firstTime(self):
        # rescue any log files that were not exported to GPX previously
        # eq, due to modRana or device crashing
        self._rescueLogs()

    def handleMessage(self, message, messageType, args):
        if message == "startLogging":
            print("tracklog: starting to log")
            # start a new log
            if not self.loggingEnabled:
                self.loggingEnabled = True
                print("tracklog: initializing the log file")
                self.initLog()
            # or resume an existing one
            elif self.loggingEnabled == True & self.loggingPaused == True:
                print("tracklog: resuming the logging")
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
            entry.entryBox(self, 'logNameEntry', 'Write tracklog name', entryText)
            self.set('needRedraw', True)

        elif message == 'clearTrace':
            self.pxpyIndex = []

        elif message == 'setupColorMenu':
            m = self.m.get('showTracklogs', None)
            if m:
                m.setupChooseDistColorMenu('tracklog', '|tracklog:colorFromRegister|set:menu:None')

        elif message == 'colorFromRegister':
            # set the color from the color register
            colorName = self.get('distinctColorRegister', 'blue')
            self.traceColor = colorName

    def handleTextEntryResult(self, key, result):
        if key == 'logNameEntry':
            self.set('logNameEntry', result)

    def initLog(self, logType='gpx', name=None):
        """start a new log, zero the appropriate variables, etc."""
        self.loggingStartTimestamp = int(time.time())
        self.maxSpeed = 0
        self.avg1 = 0
        self.avg2 = 0
        self.avgSpeed = 0
        self.currentTempLog = []
        self.distance = 0
        self.pxpyIndex.clear()
        logFolder = self.getLogFolderPath()

        if name is None:
            name = self.generateLogName()

        self.logName = name

        if logType == 'gpx':
            # importing the GPX module can be time consuming so import it
            # when it is really needed
            from upoints import gpx

            self.currentLogGPX = gpx.Trackpoints()
            # set tracklog metadata
            self.currentLogGPX.name = name
            self.currentLogGPX.time = time.gmtime()

            #      self.currentLogGPX.author = "modRana - a flexible GPS navigation system"
            #      self.currentLogGPX.link = "http://nlp.fi.muni.cz/trac/gps_navigace"

            filename = "%s.gpx" % name
            self.logFilename = filename
            self.logPath = os.path.join(logFolder, filename)

            # initialize temporary CSV log files
            path1 = os.path.join(logFolder, "%s.temporary_csv_1" % name)
            path2 = os.path.join(logFolder, "%s.temporary_csv_2" % name)

            log1 = way.AppendOnlyWay()
            log1.startWritingCSV(path1)
            self.log1 = log1

            log2 = way.AppendOnlyWay()
            log2.startWritingCSV(path2)
            self.log2 = log2

            # start update and save timers
            self._startTimers()

        self.lastUpdateTimestamp = time.time()
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
            if self.loggingEnabled and not self.loggingPaused:
                # update the current log speed statistics
                currentSpeed = self.get('speed', None)
                if currentSpeed:
                    # max speed
                    if currentSpeed > self.maxSpeed:
                        self.maxSpeed = currentSpeed
                        # avg speed
                    self.avg1 += currentSpeed
                    self.avg2 += (time.time() - self.lastUpdateTimestamp)
                    self.avgSpeed = self.avg1 / self.avg2
                    self.lastUpdateTimestamp = time.time()

                # update traveled distance
                if self.lastCoords:
                    lLat, lLon = self.lastCoords
                    self.distance += geo.distance(lLat, lLon, lat, lon)
                    self.lastCoords = lat, lon

                # update the on-map trace
                if self.lastTracePoint:
                    lat1, lon1 = self.lastTracePoint
                    # check if the point is distant enough from the last added point
                    # (which was either the first point or also passed the test)
                    if geo.distanceApprox(lat, lon, lat1, lon1) * 1000 >= DONT_ADD_TO_TRACE_THRESHOLD:
                        self._addLL2Trace(lat, lon)
                else: # this is the first known log point, just add it
                    self._addLL2Trace(lat, lon)

    def _addLL2Trace(self, lat, lon):
        proj = self.m.get('projection')
        if proj:
            (px, py) = proj.ll2pxpyRel(lat, lon)
            index = self.traceIndex
            # the pxpyIndex deque is created in reverse order
            # so that it doesn't need to be reversed when its
            # drawn on the map from current position to first point
            self.pxpyIndex.appendleft((px, py, index))
            self.traceIndex += 1
            self.lastTracePoint = (lat, lon)

    def _saveLogCB(self):
        """save the log to temporary files in storage
        (only the increment from last save needs to be stored)"""
        if not self.loggingPaused:
            self._saveLogIncrement()
            print('tracklog: temporary log files saved')

    def _saveLogIncrement(self):
        """save current log increment to storage"""
        try:
            self.log1.flush()
        except Exception:
            import sys

            e = sys.exc_info()[1]
            print('tracklog: saving primary temporary log failed')
            print(e)
        try:
            self.log2.flush()
        except Exception:
            import sys

            e = sys.exc_info()[1]
            print('tracklog: saving secondary temporary log failed')
            print(e)

    def generateLogName(self):
        """generate a unique name for a log"""
        timeString = time.strftime("%Y%m%d#%H-%M-%S", time.gmtime())
        prefix = "log"
        logNameEntry = self.get('logNameEntry', None)
        if logNameEntry:
            prefix = logNameEntry
        return prefix + "_" + timeString

    def getLogFolderPath(self):
        """return path to the log folder"""
        tracklogFolder = self.modrana.paths.getTracklogsFolderPath()
        return os.path.join(tracklogFolder, self.category)

    def _startTimers(self):
        """start the update and save timers"""
        cron = self.m.get('cron', None)
        if cron:
            # in milliseconds, stored as seconds
            updateTimeout = int(self.get('tracklogLogInterval', 1)) * 1000
            saveTimeout = int(self.get('tracklogSaveInterval', 10)) * 1000
            # update timer
            self.updateLogTimerId = cron.addTimeout(self._updateLogCB, updateTimeout, self,
                                                    "update tracklog with current position")
            # save timer
            self.saveLogTimerId = cron.addTimeout(self._saveLogCB, saveTimeout, self, "save tracklog increment")
            # update timer intervals if they are changed
            # in the persistent dictionary
            self.modrana.watch('tracklogLogInterval', self._updateIntervalChangedCB)
            self.modrana.watch('tracklogSaveInterval', self._saveIntervalChangedCB)

    def _updateIntervalChangedCB(self, key, oldInterval, newInterval):
        if self.updateLogTimerId:
            cron = self.m.get('cron', True)
            interval = int(newInterval) * 1000
            if cron:
                cron.modifyTimeout(self.updateLogTimerId, interval)
                print('tracklog: tracklog update interval changed to %s s' % newInterval)
            else:
                print("tracklog: error, the cron module is not loaded")

    def _saveIntervalChangedCB(self, key, oldInterval, newInterval):
        if self.updateLogTimerId:
            cron = self.m.get('cron', True)
            interval = int(newInterval) * 1000
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
        self.notify("saving tracklog", 3000)
        # first from the primary log
        if not self.log1.saveToGPX(self.logPath):
            self.log2.saveToGPX(self.logPath) # try the secondary log
            # TODO: check if the GPX file is loadable and retry ?

        # cleanup
        # -> this deletes the temporary log files
        # and discards the temporary AOWay objects
        self._cleanup()
        self.loggingEnabled = False
        # now we make the tracklog manager aware, that there is a new log
        loadTl = self.m.get('loadTracklogs', None)
        if loadTl:
            loadTl.listAvailableTracklogs() #TODO: incremental addition


    def _cleanup(self, deleteTempLogs=True):
        """zero unneeded datastructures after logging is stopped"""

        # delete the temporary log files
        if deleteTempLogs:
            self.log1.deleteFile()
            self.log2.deleteFile()
        self.log1 = None
        self.log2 = None

        # statistics
        self.loggingStartTimestamp = None
        self.maxSpeed = None
        self.avgSpeed = None
        # on-map trace
        self.lastTracePoint = None
        self.traceIndex = 0
        self.pxpyIndex.clear()

    #  def getVisiblePoints(self):
    #    # get only the points, that are currently visible
    #    proj = self.m.get('projection', None)
    #    if proj:
    #      print(self.LatLonIndex)
    #      (lat1,lon1,lat2,lon2) = proj.screenBBoxLL()
    #      print((lat1,lon1,lat2,lon2))
    #      print("filtering")
    #      # first get only point for available latitude range
    #      visiblePoints = filter(lambda x: lat1 >= x[0] >= lat2, self.LatLonIndex)
    #      print(visiblePoints)
    #      visiblePoints = filter(lambda x: lon1 <= x[1] <= lon2, visiblePoints)
    #      print(visiblePoints)
    #      # now sort the list of visible points according to the index
    #      visiblePoints = sorted(visiblePoints, key=lambda x: x[2])
    #      print(visiblePoints)
    #      return visiblePoints

    def point(self, cr, x, y):
        s = 2 #default 2
        cr.rectangle(x - s, y - s, 2 * s, 2 * s)

    def line(self, cr, x, y):
        """ draws a line from xb*yb to xe*ye """
        cr.set_line_width(5)
        #cr.set_source_rgb(0.0, 0.0, 0.8)
        cr.line_to(x, y)
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
                ('1 s#log every', '', 'set:tracklogLogInterval:1' + baseAction),
                ('2 s#log every', '', 'set:tracklogLogInterval:2' + baseAction),
                ('5 s#log every', '', 'set:tracklogLogInterval:5' + baseAction),
                ('10 s#log every', '', 'set:tracklogLogInterval10:' + baseAction),
                ('20 s#log every', '', 'set:tracklogLogInterval:20' + baseAction),
                ('30 s#log every', '', 'set:tracklogLogInterval:30' + baseAction),
                ('1 min#log every', '', 'set:tracklogLogInterval:60' + baseAction),
                ('2 min#log every', '', 'set:tracklogLogInterval:120' + baseAction)
            ]
            menus.addToggleItem('tracklogTools', textIconAction, 0, None, 'tracklogToolsLogInterval')

            # * saving interval button
            baseAction = '|tracklog:setNewSavingInterval'
            textIconAction = [
                ('10 s#save every', '', 'set:tracklogSaveInterval:10' + baseAction),
                ('20 s#save every', '', 'set:tracklogSaveInterval:20' + baseAction),
                ('30 s#save every', '', 'set:tracklogSaveInterval:30' + baseAction),
                ('1 min#save every', '', 'set:tracklogSaveInterval:60' + baseAction),
                ('2 min s#save every', '', 'set:tracklogSaveInterval:120' + baseAction),
                ('5 min s#save every', '', 'set:tracklogSaveInterval:300' + baseAction),
                ('10 min s#save every', '', 'set:tracklogSaveInterval:600' + baseAction)
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
            menus.addItem('tracklogTools', 'folder#go to', 'generic',
                          'set:currentTracCat:logs|set:menu:tracklogManager#tracklogManager')
            menus.addItem('tracklogTools', 'trace#clear', 'generic', 'tracklog:clearTrace|set:menu:None')
            menus.addItem('tracklogTools', 'color#change', 'generic',
                          'tracklog:setupColorMenu|set:menu:chooseDistColor')

    def drawMenu(self, cr, menuName, args=None):
        if menuName == 'tracklog':
            # is the submenu initialized ?
            if self.toolsMenuDone == False:
                print("tracklog: setting up tracklogTools menu")
                self.initToolsMenu()
                self.toolsMenuDone = True

            parentAction = 'set:menu:main'
            # this is a a list of button parameters, all buttons can be toggleable
            # it is in this form:
            # [list of string-lists for toggling, index of string-list to show]
            units = self.m.get('units', None)

            # main status text

            startButtonIndex = 0
            text = ""
            if self.loggingEnabled:
                if self.loggingPaused:
                    text += '<span foreground="cyan">logging is <i>PAUSED</i></span>'
                    startButtonIndex = 2 # resume
                else:
                    text += '<span foreground="green">logging is ON</span>'
                    startButtonIndex = 1 # pause
            else:
                text += '<span foreground="red">logging is OFF</span>'
                startButtonIndex = 0 # start

            # buttons

            fiveButtons = [
                [[
                     ["start", "start", "tracklog:startLogging|set:needRedraw:True"],
                     ["pause", "pause", "tracklog:pauseLogging|set:needRedraw:True"],
                     ["resume", "start", "tracklog:startLogging|set:needRedraw:True"]
                 ], startButtonIndex],
                [[["stop", "stop", "tracklog:stopLogging"]], 0],
                [[["split", "split", "tracklog:stopLogging|tracklog:startLogging"]], 0],
                [[["name#edit", "generic", "tracklog:nameInput"]], 0],
                [[["tools", "tools", "set:menu:tracklogTools"]], 0],
            ]

            text += "\n\n"

            if not self.loggingEnabled:
                text += "%s" % self.generateLogName()
            else:
                text += "%s" % self.logName

            text += "\n\nlogging interval %d s, saving every %d s" % (self.logInterval, self.saveInterval)
            if self.loggingStartTimestamp:
                elapsedSeconds = (int(time.time()) - self.loggingStartTimestamp)
                text += "\nelapsed time: %s" % time.strftime('%H:%M:%S', time.gmtime(elapsedSeconds))

            currentSpeed = self.get('speed', 0)
            if currentSpeed:
                if units:
                    currentSpeedString = units.km2CurrentUnitPerHourString(currentSpeed)
                else:
                    currentSpeedString = "%f kmh" % currentSpeed
                text += "\n\ncurrent speed: <span foreground='yellow'>%s</span>" % currentSpeedString
            else:
                text += '\n\ncurrent speed <span foreground="red">unknown</span>'

            if self.maxSpeed:
                if units:
                    avgString = units.km2CurrentUnitPerHourString(self.avgSpeed)
                    maxString = units.km2CurrentUnitPerHourString(self.maxSpeed)
                else:
                    avgString = "%f kmh" % self.avgSpeed
                    maxString = "%f kmh" % self.maxSpeed
                text += "\n\nmax: %s, average: %s" % (maxString, avgString)

            if self.distance:
                if units:
                    distanceString = units.km2CurrentUnitString(self.distance, 2)
                else:
                    distanceString = "%f km" % self.distance
                text += "\ndistance traveled <span foreground='white'>%s</span>\n" % distanceString

            box = (text, "set:menu:tracklog#tracklog")
            menus = self.m.get("menu", None)
            if menus:
                menus.drawSixPlusOneMenu(cr, menuName, parentAction, fiveButtons, box)
            else:
                print('tracklog: error, menus module is missing')

        else:
            return # we aren't the active menu so we dont do anything

    def drawMapOverlay(self, cr):
        proj = self.m.get('projection', None)
        if proj and self.pxpyIndex:
            cr.set_source_color(gtk.gdk.color_parse(self.traceColor))
            cr.set_line_width(10)
            # log trace drawing algorithm
            # adapted from TangoGPS source (tracks.c)
            # works surprisingly good :)
            # TODO: use the modulo method for drawing stored tracklogs
            posXY = proj.getCurrentPosXY()
            if posXY and self.loggingEnabled and not self.loggingPaused:
                cr.move_to(*posXY) # start drawing from current position
            else:
                (px, py, index) = self.pxpyIndex[0] # start drawing from first trace point
                (x, y) = proj.pxpyRel2xy(px, py)
                cr.move_to(x, y)

            z = proj.zoom

            if 16 > z > 10:
                modulo = 2 ** (16 - z)
            elif z <= 10:
                modulo = 32
            else:
                modulo = 1

            maxDraw = 300
            drawCount = 0
            counter = 0

            #draw the track
            for point in self.pxpyIndex:  # pypyIndex is already in reverse order
                counter += 1
                if counter % modulo == 0:
                    drawCount += 1
                    if drawCount > maxDraw:
                        break
                    (px, py, index) = point
                    (x, y) = proj.pxpyRel2xy(px, py)
                    cr.line_to(x, y)
                    # TODO: don't iterate, just get items based on index

                    # draw a track to current position (if known):

                #      print(z, modulo)
                #      print(counter, drawCount)

            cr.stroke()
            cr.fill()

    def _rescueLogs(self):
        """rescue any log files that were not exported to GPX previously"""

        # get log folder path
        logFolder = self.getLogFolderPath()

        # check out the log folder for temporary files

        # first scan for primary logs
        primaryLogs = glob.glob("%s/*.temporary_csv_1" % logFolder)
        secondaryLogs = glob.glob("%s/*.temporary_csv_2" % logFolder)

        if primaryLogs or secondaryLogs:
            self.notify("exporting temporary tracklogs to GPX", 5000)
            self.set('needRedraw', True)

        if primaryLogs:
            print('tracklog: exporting %d unsaved primary log files to GPX' % len(primaryLogs))
            for logPath in primaryLogs:
                # export any found files
                print('tracklog: exporting %s to GPX' % logPath)
                try:
                    w1 = way.fromCSV(logPath, delimiter=",")
                    exportPath = "%s.gpx" % os.path.splitext(logPath)[0]
                    # does the GPX file already exist ?
                    # TODO: check if the GPX file is corrupted and swap with newly exported one ?
                    # (eq. caused by a crash during saving the GPX file)
                    if os.path.exists(exportPath): # save to backup path
                        exportPath = "%s_1.gpx" % os.path.splitext(logPath)[0]
                    w1.saveToGPX(exportPath)
                    print('tracklog: GPX export successful')
                    # success, delete temporary files

                    # primary
                    os.remove(logPath)
                    print('tracklog: temporary file %s deleted' % logPath)
                    # secondary
                    secondaryPath = "%s.temporary_csv_2" % os.path.splitext(logPath)[0]
                    if os.path.exists(secondaryPath):
                        os.remove(secondaryPath)
                        print('tracklog: temporary file %s deleted' % secondaryPath)

                except Exception:

                    import sys

                    e = sys.exc_info()[1]
                    print('tracklog: exporting unsaved primary log file failed')
                    print(e)
                    failedPath = "%s_1.csv" % os.path.splitext(logPath)[0]
                    print('tracklog: renaming to %s instead' % failedPath)
                    try:
                        shutil.move(logPath, failedPath)
                        print("tracklog: renaming successful")
                    except Exception:
                        import sys

                        e = sys.exc_info()[1]
                        print('tracklog: renaming %s to %s failed' % (logPath, failedPath))
                        print(e)


        # rescan for secondary logs
        # (there should be only secondary logs that
        # either don't have primary logs or where primary logs
        # failed to parse (primary logs delete secondary logs
        # after successful processing)

        secondaryLogs = glob.glob("%s/*.temporary_csv_2" % logFolder)
        if secondaryLogs:
            print('tracklog: exporting %d unsaved secondary log files to GPX' % len(primaryLogs))
            for logPath in secondaryLogs:
                # export any found files
                print('tracklog: exporting %s to GPX' % logPath)
                try:
                    w2 = way.fromCSV(logPath, delimiter=",")
                    exportPath = "%s.gpx" % os.path.splitext(logPath)[0]
                    # does the GPX file already exist ?
                    # TODO: check if the GPX file is corrupted and swap with newly exported one ?
                    # (eq. caused by a crash during saving the GPX file)
                    if os.path.exists(exportPath): # save to backup path
                        exportPath = "%s_2.gpx" % os.path.splitext(logPath)[0]
                    w2.saveToGPX(exportPath)
                    print('tracklog: GPX export successful')
                    # success, delete temporary file

                    # secondary
                    # (primary is either not there or was already removed in primary pass)
                    os.remove(logPath)
                    print('tracklog: temporary file %s deleted' % logPath)

                except Exception:
                    import sys

                    e = sys.exc_info()[1]
                    print('tracklog: exporting unsaved secondary log file failed')
                    print(e)
                    failedPath = "%s_2.csv" % os.path.splitext(logPath)[0]
                    print('tracklog: renaming to %s instead' % failedPath)
                    try:
                        shutil.move(logPath, failedPath)
                        print("tracklog: renaming successful")
                    except Exception:
                        import sys

                        e = sys.exc_info()[1]
                        print('tracklog: renaming %s to %s failed' % (logPath, failedPath))
                        print(e)

    def shutdown(self):
        # try to stop and save the log
        if self.loggingEnabled:
            self.stopLogging()







