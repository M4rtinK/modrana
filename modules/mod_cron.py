# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# A timing and scheduling module for modRana.
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
from __future__ import with_statement # for python 2.5
from modules.base_module import RanaModule
import threading

# only import GKT libs if GTK GUI is used
from core import gs

if gs.GUIString == "GTK":
    import gobject
else:
    from PySide import QtCore


def getModule(m, d, i):
    """
    return module version corresponding to the currently used toolkit
    (eq. one that uses the timers provided by the toolkit
    - gobject.timeout_add, QTimer, etc.
    """
    if gs.GUIString == 'QML':
        return CronQt(m, d, i)
    else: # GTK for now
        return CronGTK(m, d, i)


class Cron(RanaModule):
    """A timing and scheduling module for modRana

    -> this is an abstract class
    that specifies and interface for concrete implementations

    Why is there a special module for timing ?
       The reason is twofold:
       Toolkit independence and power saving/monitoring.

       If all timing calls go through this module,
       the underlying engine (currently glibs gobject)
       can be more easily changed than rewriting code everywhere.

       Also, modRana targets mobile devices with limited power budget.
       If all timing goes through this module, rogue modules many frequent
       timers can be easily identified.
       It might be also possible to stop or pause some/all of the timers
       after a period of inactivity, or some such.
    """

    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)

    def addIdle(self, callback, args):
        """add a callback that is called once the main loop becomes idle"""
        pass

    def addTimeout(self, callback, timeout, caller, description, args=None):
        """the callback will be called timeout + time needed to execute the callback
        and other events"""
        if not args: args = []
        pass

    def _doTimeout(self, timeoutId, callback, args):
        """wrapper about the timeout function, which makes it possible to check
        if a timeout is still in progress from the "outside"
        - like this, the underlying timer should also be easily replaceable
        """

        if callback(*args) == False:
            # the callback returned False,
            # that means it wants to quit the timeout

            # stop tracking
            self.removeTimeout(timeoutId)
            # propagate the quit signal
            return False
        else:
            return True # just run the loop

    def removeTimeout(self, timeoutId):
        """remove timeout with a given id"""
        pass

    def modifyTimeout(self, timeoutId, newTimeout):
        """modify the duration of a timeout in progress"""
        pass


class CronGTK(Cron):
    """A GTK timing and scheduling module for modRana"""

    def __init__(self, m, d, i):
        Cron.__init__(self, m, d, i)
        gui = self.modrana.gui

        self.nextId = 0
        # cronTab and activeIds should be in sync
        self.cronTab = {"idle": {}, "timeout": {}}
        self.dataLock = threading.RLock()

    def _getID(self):
        """get an unique id for timing related request that can be
        returned to the callers and used as a handle
        TODO: can int overflow in Python ?"""
        timeoutId = self.nextId
        self.nextId += 1
        return timeoutId

    def addIdle(self, callback, args):
        """add a callback that is called once the main loop becomes idle"""
        gobject.idle_add(callback, *args)

    def addTimeout(self, callback, timeout, caller, description, args=None):
        """the callback will be called timeout + time needed to execute the callback
        and other events"""
        if not args: args = []
        timeoutId = self._getID()
        realId = gobject.timeout_add(timeout, self._doTimeout, timeoutId, callback, args)
        timeoutTuple = (callback, args, timeout, caller, description, realId)
        with self.dataLock:
            self.cronTab['timeout'][timeoutId] = timeoutTuple
        return timeoutId

    def removeTimeout(self, timeoutId):
        """remove timeout with a given id"""
        with self.dataLock:
            if timeoutId in self.cronTab['timeout'].keys():
                (callback, args, timeout, caller, description, realId) = self.cronTab['timeout'][timeoutId]
                del self.cronTab['timeout'][timeoutId]
                gobject.source_remove(realId)
            else:
                print("cron: can't remove timeout, wrong id: ", timeoutId)

    def modifyTimeout(self, timeoutId, newTimeout):
        """modify the duration of a timeout in progress"""
        with self.dataLock:
            if timeoutId in self.cronTab['timeout'].keys():
                # load the timeout description
                (callback, args, timeout, caller, description, realId) = self.cronTab['timeout'][timeoutId]
                gobject.source_remove(realId) # remove the old timeout
                realId = gobject.timeout_add(newTimeout, self._doTimeout, timeoutId, callback, args) # new timeout
                # update the timeout description
                self.cronTab['timeout'][timeoutId] = (callback, args, newTimeout, caller, description, realId)
            else:
                print("cron: can't modify timeout, wrong id: ", timeoutId)


class CronQt(Cron):
    """A Qt timing and scheduling module for modRana"""

    def __init__(self, m, d, i):
        Cron.__init__(self, m, d, i)
        self.nextId = 0
        # cronTab and activeIds should be in sync
        self.cronTab = {"idle": {}, "timeout": {}}
        self.dataLock = threading.RLock()

    def _getID(self):
        """get an unique id for timing related request that can be
        returned to the callers and used as a handle
        TODO: can int overflow in Python ?
        TODO: id recycling ?"""
        with self.dataLock:
            timeoutId = self.nextId
            self.nextId += 1
            return timeoutId

    def addIdle(self, callback, args):
        """add a callback that is called once the main loop becomes idle"""
        pass

    def addTimeout(self, callback, timeout, caller, description, args=None):
        """the callback will be called timeout + time needed to execute the callback
        and other events
        """
        if not args: args = []
        # create and configure the timer
        timer = QtCore.QTimer()
        #    timer.setInterval(timeout)
        timeoutId = self._getID()
        # create a new function that calls the callback processing function
        # with thh provided arguments"""
        handleThisTimeout = lambda: self._doTimeout(timeoutId, callback, args)
        # connect this function to the timeout
        timer.timeout.connect(handleThisTimeout)
        # store timer data
        timeoutTuple = (callback, args, timeout, caller, description, timeoutId, timer)
        with self.dataLock:
            self.cronTab['timeout'][timeoutId] = timeoutTuple
            # start the timer
        timer.start(timeout)
        # return the id
        return timeoutId

    def removeTimeout(self, timeoutId):
        """remove timeout with a given id"""
        with self.dataLock:
            if timeoutId in self.cronTab['timeout'].keys():
                (callback, args, timeout, caller, description, timeoutId, timer) = self.cronTab['timeout'][timeoutId]
                timer.stop()
                del self.cronTab['timeout'][timeoutId]
            else:
                print("cron: can't remove timeout, wrong id: ", timeoutId)

    def modifyTimeout(self, timeoutId, newTimeout):
        """modify the duration of a timeout in progress"""
        with self.dataLock:
            if timeoutId in self.cronTab['timeout'].keys():
                # load the timeout data
                (callback, args, timeout, caller, description, timeoutId, timer) = self.cronTab['timeout'][timeoutId]
                # reset the timeout duration
                timer.setInterval(newTimeout)
                # update the timeout data
                self.cronTab['timeout'][timeoutId] = (callback, args, newTimeout, caller, description, timeoutId, timer)
            else:
                print("cron: can't modify timeout, wrong id: ", timeoutId)

#  def _addInfo(self, id, info):
#    """add a message for a timeout handler to read"""
#    with self.dataLock:
#      if id in self.info:
#        self.info[id].append(info) # add message to queue
#      else:
#        self.info[id] = [info] # create message queue
#
#  def _popInfo(self, id):
#    with self.dataLock:
#      if id in self.info:
#        try:
#          return self.info[id].pop() # try to return the message
#        except IndexError:
#          del self.info[id] # message queue empty, delete it
#          return None
#      else:
#        return None
