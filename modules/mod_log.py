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
from modules.base_module import RanaModule
import sys
import os

def getModule(m,d,i):
  return Log(m,d,i)

class Log(RanaModule):
  """A modRana STDOUT logging module"""
  
  def __init__(self, m, d, i):
    RanaModule.__init__(self, m, d, i)
    self.savedStdout = None
    self.fSock = None
    self.currentLogPath = ""

  def firstTime(self):
    self.checkLoggingStatus()

  def handleMessage(self, message, messageType, args):
    if message == "checkLoggingStatus": # check if logging was enabled
      self.checkLoggingStatus()

  def getLogFilePath(self):
    logFolderPath = self.modrana.paths.getLogFolderPath()
    # the paths module tires to make sure that the folder exists
    # before returning the path
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
      import sys
      self.savedStdout = sys.stdout
      if not self.fSock:
        print("**log: opening stdout log file")
        # open a line-buffered socket (the "1" parameter in open() does that)
        # -> like this, every write to stdout modRana does should be flashed to file
        # -> so if it crashes for some reason, the output leading up to the crash should be already
        # in storage
        self.fSock = open(self.getLogFilePath(), 'w', 1)
      print("**log: redirecting stdout to log file:\%s" % self.currentLogPath)
      sys.stdout = self.fSock
      print("**log: stdout redirected to (this :) log file")
    except Exception:
      import sys
      e = sys.exc_info()[1]
      print("debug log: redirecting stdout to file failed:\n%s" % e)

  def disableLogging(self):
    """disable logging"""
    #do whe have a usable saved stdout ?
    if self.savedStdout:
      print("**log: redirecting stdout back")
      sys.stdout = self.savedStdout

  def shutdown(self):
    """disable logging"""
    self.disableLogging()
    # try to close the log file
    # is there actually something to close ?
    if self.fSock:
      try:
        self.fSock.close()
      except Exception:
        import sys
        e = sys.exc_info()[1]
        print("**log: closing log file failed")
        print(e)
