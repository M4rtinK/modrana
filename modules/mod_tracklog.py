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
from core.way import Way, AppendOnlyWay
from core.signal import Signal


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


def getModule(*args, **kwargs):
    return Tracklog(*args, **kwargs)


class Tracklog(RanaModule):
    """Record tracklogs"""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self.loggingEnabled = False
        self.loggingPaused = False
        self.loggingStartTimestamp = 0
        self.lastUpdateTimestamp = None
        self.lastCoords = None
        self.logName = None #name of the current log
        self.logFilename = None #name of the current log
        self.logPath = None #path to the current log
        self.currentLogGPX = None
        self.currentTempLog = []
        # primary and secondary AOWay objects for
        # persistent log storage during logging
        self.log1 = None
        self.log2 = None
        # timer ids
        self.updateLogTimerId = None
        self.saveLogTimerId = None
        # signals
        self.tracklogUpdated = Signal()
        # statistics
        self.maxSpeed = 0
        self.avg1 = 0
        self.avg2 = 0
        self.avgSpeed = 0
        self.distance = 0
        self.toolsMenuDone = False
        self.category = 'logs'
        # trace
        self.traceColor = 'blue'
        self.lastTracePoint = None
        self.traceIndex = 0
        self.pxpyIndex = deque()
        self.lastX = 0
        self.lastY = 0

    #    self.startupTimestamp = time.strftime("%Y%m%dT%H%M%S")

    def firstTime(self):
        # rescue any log files that were not exported to GPX previously
        # eq, due to modRana or device crashing
        self._rescueLogs()

    def handleMessage(self, message, messageType, args):
        if message == "startLogging":
            self.log.info("starting track logging")
            # start a new log
            if not self.loggingEnabled:
                self.startLogging(self.get('logNameEntry', ""))
            # or resume an existing one
            elif self.loggingEnabled == True & self.loggingPaused == True:
                self.log.info("resuming track logging")
                self.loggingPaused = False

        elif message == "pauseLogging":
            self.pauseLogging()

        elif message == "stopLogging":
            self.log.info("stopping track logging")
            self.stopLogging()

        elif message == 'nameInput':
            entry = self.m.get('textEntry', None)
            if entry is None:
                self.log.error("error, text entry module is not loaded")
                return
            entryText = ""
            logNameEntry = self.get('logNameEntry', None)
            if logNameEntry:
                entryText = logNameEntry
            entry.entryBox(self, 'logNameEntry', 'Write tracklog name', entryText)

        elif message == 'clearTrace':
            self.clearTrace()

        elif message == 'setupColorMenu':
            m = self.m.get('showTracklogs', None)
            if m:
                m.setupChooseDistColorMenu('tracklog', '|tracklog:colorFromRegister|set:menu:None')

        elif message == 'colorFromRegister':
            # set the color from the color register
            colorName = self.get('distinctColorRegister', 'blue')
            self.traceColor = colorName

    def startLogging(self, name="", logType='gpx'):
        """Start a new log file

        :param str logType: tracklog output type
        :param str name: tracklog name
        :returns: tracklog filename or None
        :rtype: str or None
        """
        if self.loggingEnabled:
            self.log.error("track logging already in progress")
            return None
        self.log.info("initializing the tracklog file")
        # zero the appropriate variables, etc.
        self.loggingEnabled = True
        self.loggingStartTimestamp = int(time.time())
        self.maxSpeed = 0
        self.avg1 = 0
        self.avg2 = 0
        self.avgSpeed = 0
        self.currentTempLog = []
        self.distance = 0
        self.pxpyIndex.clear()
        logFolder = self.getLogFolderPath()

        name = self.generateLogName(name)

        self.logName = name

        filename = None

        if logType == 'gpx':
            # importing the GPX module can be time consuming so import it
            # when it is really needed
            self.log.info("GPX selected as format for the final output")

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

            log1 = AppendOnlyWay()
            log1.start_writing_csv(path1)
            self.log1 = log1

            log2 = AppendOnlyWay()
            log2.start_writing_csv(path2)
            self.log2 = log2

            # start update and save timers
            self._startTimers()
        else:
            self.log.error("unknown track log format: %s" % logType)

        self.lastUpdateTimestamp = time.time()
        self.lastCoords = self.get('pos', None)
        self.log.info("tracklog file initialized")

        return filename

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
        if not self.log1.save_to_GPX(self.logPath):
            self.log2.save_to_GPX(self.logPath) # try the secondary log
            # TODO: check if the GPX file is loadable and retry ?

        # cleanup
        # -> this deletes the temporary log files
        # and discards the temporary AOWay objects
        self._cleanup()
        self.loggingEnabled = False
        # now we make the tracklog manager aware, that there is a new log
        loadTl = self.m.get('loadTracklogs', None)
        if loadTl:
            loadTl.list_available_tracklogs() #TODO: incremental addition


    def pauseLogging(self):
        """pause logging"""
        if self.loggingEnabled:
            self._saveLogIncrement() # save increment
            self.loggingPaused = True # pause logging
            self.log.info('track logging paused')
        else:
            self.log.error("can't pause track logging - no logging in progress")

    def unPauseLogging(self):
        """pause logging"""
        if self.loggingEnabled:
            self._saveLogIncrement() # save increment
            self.loggingPaused = False # un-pause logging
            self.log.info('track logging un-paused')
        else:
            self.log.error("can't un-pause track logging - no logging in progress")

    def clearTrace(self):
        """Clear the on-map log trace
        NOTE: currently does something only with GTK GUI
        """
        self.pxpyIndex = []

    def _updateLogCB(self):
        """add current position at the end of the log"""
        pos = self.get('pos', None)
        if pos and not self.loggingPaused:
            timestamp = geo.timestamp_utc()
            lat, lon = pos
            elevation = self.get('elevation', None)
            self.log1.add_point_llet(lat, lon, elevation, timestamp)
            self.log2.add_point_llet(lat, lon, elevation, timestamp)

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
                    addToTrace = True
                    try:
                        addToTrace = geo.distance_approx(lat, lon, lat1, lon1) * 1000 >= DONT_ADD_TO_TRACE_THRESHOLD
                    except Exception:
                        self.log.exception("measuring distance failed (yeah, really! :P), adding point anyway")

                    if addToTrace:
                        self._addLL2Trace(lat, lon)
                else: # this is the first known log point, just add it
                    self._addLL2Trace(lat, lon)
        # done, trigger the tracklog updated signal
        self.tracklogUpdated()

    def getStatusDict(self):
        """Return status of the current track logging as a dictionary
        This is used by the Qt 5 GUI to show the various logging related
        statistics.

        :returns: dictionary describing current track logging state
        """
        pointCount = 0
        units = self.m.get('units', None)
        if self.log1:
            pointCount = self.log1.point_count

        speed = self.get('speed', 0)
        if speed is not None:
            speed = units.km2CurrentUnitPerHourString(speed)
        else:
            speed = "unknown"

        return {
            "speed" : {
                "current" : speed,
                "max" : units.km2CurrentUnitPerHourString(self.maxSpeed),
                "avg" : units.km2CurrentUnitPerHourString(self.avgSpeed)
            },
            "distance" : units.km2CurrentUnitString(self.distance, 2),
            "elapsedTime" : time.strftime('%H:%M:%S', time.gmtime(int(time.time()) - self.loggingStartTimestamp)),
            "pointCount" : pointCount
        }

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
            minutesElapsed = (time.time() - self.loggingStartTimestamp)/60.0
            self.log.info('temp log files saved for %s, %1.1f min elapsed', self.logName, minutesElapsed)

    def _saveLogIncrement(self):
        """save current log increment to storage"""
        try:
            self.log1.flush()
        except Exception:
            self.log.exception('saving primary temporary tracklog failed')

        try:
            self.log2.flush()
        except Exception:
            self.log.exception('saving secondary temporary tracklog failed')

    def generateLogName(self, name):
        """generate a unique name for a log"""
        timeString = time.strftime("%Y%m%d#%H-%M-%S", time.gmtime())
        prefix = "log"
        if name:
            prefix = name
        return prefix + "_" + timeString

    def getLogFolderPath(self):
        """return path to the log folder"""
        tracklogFolder = self.modrana.paths.tracklog_folder_path
        return os.path.join(tracklogFolder, self.category)

    def _startTimers(self):
        """start the update and save timers"""
        # in milliseconds, stored as seconds
        updateTimeout = int(self.get('tracklogLogInterval', 1)) * 1000
        saveTimeout = int(self.get('tracklogSaveInterval', 10)) * 1000
        cron = self.m.get('cron', None)
        if cron:
            # update timer
            self.updateLogTimerId = cron.addTimeout(self._updateLogCB, updateTimeout, self,
                                                    "update tracklog with current position")
            # save timer
            self.saveLogTimerId = cron.addTimeout(self._saveLogCB, saveTimeout, self, "save tracklog increment")

            # report the timer cadence
            self.log.info("starting track logging timers: update every %d s, save every %d s",
                          updateTimeout/1000, saveTimeout/1000)
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
                self.log.info('tracklog update interval changed to %s s', newInterval)
            else:
                self.log.error("the modRana cron module is not available")

    def _saveIntervalChangedCB(self, key, oldInterval, newInterval):
        if self.updateLogTimerId:
            cron = self.m.get('cron', True)
            interval = int(newInterval) * 1000
            if cron:
                cron.modifyTimeout(self.saveLogTimerId, interval)
                self.log.info('tracklog save interval changed to %s s' % newInterval)
            else:
                self.log.error("the modRana cron module is not available")

    def _stopTimers(self):
        """stop the update and save timers"""
        cron = self.m.get('cron', None)
        if cron:
            cron.removeTimeout(self.updateLogTimerId)
            cron.removeTimeout(self.saveLogTimerId)
            self.saveLogTimerId = None
            self.updateLogTimerId = None
            self.log.info("track logging timers stopped")
        else:
            self.log.error("the modRana cron module is not available")

    def _cleanup(self, deleteTempLogs=True):
        """zero unneeded datastructures after logging is stopped"""

        # delete the temporary log files
        if deleteTempLogs:
            self.log1.delete_file()
            self.log2.delete_file()
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
        self.lastX = x
        self.lastY = y

    #    s = 2 #default 2
    #    cr.rectangle(x-s,y-s,2*s,2*s)
    #    last_x = x
    #    last_y = y
    #print("bod")

    def _rescueLogs(self):
        """rescue any log files that were not exported to GPX previously"""

        # get log folder path
        logFolder = self.getLogFolderPath()

        # check out the log folder for temporary files

        # first scan for primary logs
        primaryLogs = glob.glob("%s/*.temporary_csv_1" % logFolder)
        secondaryLogs = glob.glob("%s/*.temporary_csv_2" % logFolder)

        if primaryLogs or secondaryLogs:
            self.log.info("unsaved temporary tracklogs detected")
            self.notify("exporting temporary tracklogs to GPX", 5000)

            if primaryLogs:
                self.log.info('exporting %d unsaved primary tracklog files to GPX', len(primaryLogs))
                for logPath in primaryLogs:
                    # export any found files
                    self.log.info('exporting %s to GPX', logPath)
                    try:
                        w1 = Way.from_csv(logPath, delimiter=",")
                        exportPath = "%s.gpx" % os.path.splitext(logPath)[0]
                        # does the GPX file already exist ?
                        # TODO: check if the GPX file is corrupted and swap with newly exported one ?
                        # (eq. caused by a crash during saving the GPX file)
                        if os.path.exists(exportPath): # save to backup path
                            exportPath = "%s_1.gpx" % os.path.splitext(logPath)[0]
                        w1.save_to_GPX(exportPath)
                        self.log.info('GPX export of unsaved primary tracklog successful')
                        # success, delete temporary files

                        # primary
                        os.remove(logPath)
                        self.log.debug('primary temporary file %s deleted', logPath)
                        # secondary
                        secondaryPath = "%s.temporary_csv_2" % os.path.splitext(logPath)[0]
                        if os.path.exists(secondaryPath):
                            os.remove(secondaryPath)
                            self.log.debug('secondary temporary file %s deleted', secondaryPath)

                    except Exception:
                        self.log.exception('exporting unsaved primary log file failed')
                        failedPath = "%s_1.csv" % os.path.splitext(logPath)[0]
                        self.log.info('renaming to %s instead', failedPath)
                        try:
                            shutil.move(logPath, failedPath)
                            self.log.info("renaming successful")
                        except Exception:
                            self.log.exception('renaming %s to %s failed', logPath, failedPath)

            # rescan for secondary logs
            # (there should be only secondary logs that
            # either don't have primary logs or where primary logs
            # failed to parse (primary logs delete secondary logs
            # after successful processing)

            secondaryLogs = glob.glob("%s/*.temporary_csv_2" % logFolder)
            if secondaryLogs:
                self.log.info('exporting %d unsaved secondary log files to GPX' % len(primaryLogs))
                for logPath in secondaryLogs:
                    # export any found files
                    self.log.info('exporting %s to GPX' % logPath)
                    try:
                        w2 = Way.from_csv(logPath, delimiter=",")
                        exportPath = "%s.gpx" % os.path.splitext(logPath)[0]
                        # does the GPX file already exist ?
                        # TODO: check if the GPX file is corrupted and swap with newly exported one ?
                        # (eq. caused by a crash during saving the GPX file)
                        if os.path.exists(exportPath): # save to backup path
                            exportPath = "%s_2.gpx" % os.path.splitext(logPath)[0]
                        w2.save_to_GPX(exportPath)
                        self.log.info('GPX export of unsaved secondary tracklog successful')
                        # success, delete temporary file

                        # secondary
                        # (primary is either not there or was already removed in primary pass)
                        os.remove(logPath)
                        self.log.info('secondary temporary file %s deleted' % logPath)

                    except Exception:
                        self.log.exception('exporting unsaved secondary log file failed')
                        failedPath = "%s_2.csv" % os.path.splitext(logPath)[0]
                        self.log.info('renaming to %s instead', failedPath)
                        try:
                            shutil.move(logPath, failedPath)
                            self.log.info("renaming successful")
                        except Exception:
                            self.log.exception('renaming %s to %s failed', logPath, failedPath)
            self.log.debug("unsaved tracklog handling finished")

    def shutdown(self):
        # try to stop and save the log
        if self.loggingEnabled:
            self.stopLogging()
