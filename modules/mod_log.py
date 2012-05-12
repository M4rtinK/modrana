from ScrolledText import example
import os
#!/usr/bin/python
# -*- coding: utf-8 -*-
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
import os

def getModule(m,d,i):
  return(log(m,d,i))

class log(ranaModule):
  """A modRana logging module"""
  
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.savedStdout = None
    self.fSock = None
    self.currentLogPath = ""

  def firstTime(self):
    self.checkLoggingStatus()

  def handleMessage(self, message, type, args):
    if message == "checkLoggingStatus": # check if logging was enabled
      self.checkLoggingStatus()

  def update(self):
    if self.fSock:
      try:
        self.fSock.flush()
      except Exception, e:
        print("**log: flushing the log file failed")
        print(e)

  def getLogFilePath(self):
    logFolderPath = self.modrana.paths.getLogFolderPath()
    """modRana should make sure that the folder exists"""
    units = self.m.get('units', None)
    if units:
      timeHashString = units.getTimeHashString()
      fileName = 'modrana_stdout_%s.log.txt' % timeHashString
      return os.path.join(logFolderPath, fileName)
    else:
      print("log: units module missing")
      return None

  def checkLoggingStatus(self):
    loggingStatus = self.get('loggingStatus', False)
    if loggingStatus:
      self.enableLogging()
    else:
      self.disableLogging()

  def enableLogging(self):
    try:
      self.savedStdout = sys.stdout
      if not self.fSock:
        print "**log: opening stdout log file"
        self.fSock = open(self.getLogFilePath(), 'w')
      print "**log: redirecting stdout to log file:\%s" % self.currentLogPath
      sys.stdout = self.fSock
      print "**log: stdout redirected to (this :) log file"
    except Exception, e:
      print "debug log: redirecting stdout to file failed:\n%s" % e

  def disableLogging(self):
    """disable logging"""
    #do whe have a usable saved stdout ?
    if self.savedStdout:
      print "**log: redirecting stdout back"
      sys.stdout = self.savedStdout

  def shutdown(self):
    """disable logging"""
    self.disableLogging()
    """try to close the log file"""
    # is there actually something to close ?
    if self.fSock:
      try:
        self.fSock.close()
      except Exception ,e:
        print("**log: closing log file failed")
        print(e)


if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
