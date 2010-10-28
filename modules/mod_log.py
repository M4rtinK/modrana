import os
#!/usr/bin/python
#----------------------------------------------------------------------------
# A modRana logging module
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
import sys
import time

def getModule(m,d):
  return(log(m,d))

class log(ranaModule):
  """A modRana logging module"""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.savedStdout = None
    self.fsock = None
    self.currentLogPath = ""

  def firstTime(self):
    self.checkLoggingStatus()

  def handleMessage(self, message, type, args):
    if message == "checkLoggingStatus": # check if logging was enabled
      self.checkLoggingStatus()

  def update(self):
    if self.fsock:
      try:
        self.fsock.flush()
      except:
        print "**log: flushing the log file failed"

  def getLogFilePath(self):
    logFolderPath = self.dmod.getLogFolderPath()
    # check if folder exists, if not, try to create it
    if not os.path.exists(logFolderPath):
      try:
        os.makedirs(logFolderPath)
      except:
        print "debug log: creating log folder failed"
    units = self.m.get('units', None)
    if units:
      timeHashString = units.getTimeHashString()
      fileName = 'modrana_stdout_%s.log.txt' % timeHashString
      return("" + logFolderPath + "/" + fileName)

  def checkLoggingStatus(self):
    loggingStatus = self.get('loggingStatus', False)
    if loggingStatus:
      self.enableLogging()
    else:
      self.disableLogging()

  def enableLogging(self):
    try:
      self.savedStdout = sys.stdout
      if not self.fsock:
        print "**log: opening stdout log file"
        self.fsock = open(self.getLogFilePath(), 'w')
      print "**log: redirectiong stdout to log file:\%s" % self.currentLogPath
      sys.stdout = self.fsock
      print "**log: stdout redirected to (this :) log file"
    except Exception, e:
      print "debug log: redirecting stdout to file failed:\n%s" % e

  def disableLogging(self):
    """disable logging"""
    #do whe have a usable saved stdout ?
    if self.savedStdout:
      print "**log: redirectiong stdout back"
      sys.stdout = self.savedStdout

  def shutdown(self):
    """disable logging"""
    self.disableLogging()
    """try to close the log file"""
    # is there actually something to close ?
    if self.fsock:
      try:
        self.fsock.close()
      except:
        print "**log: closing log file failed"


    

if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
