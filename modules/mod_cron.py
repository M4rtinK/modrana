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

from core import gs

if gs.GUIString.lower() == "qt5":
    import pyotherside

def getModule(*args, **kwargs):
    """
    return module version corresponding to the currently used toolkit
    (eq. one that uses the timers provided by the toolkit
    - gobject.timeout_add, QTimer, etc.
    """
    if gs.GUIString.lower() == 'qt5':
        return CronQt5(*args, **kwargs)
    else:
        return Cron(*args, **kwargs)


class Cron(RanaModule):
    """A timing and scheduling module for modRana"""

    # -> this is an abstract class
    # that specifies and interface for concrete implementations
    #
    # Why is there a special module for timing ?
    #    The reason is twofold:
    #    Toolkit independence and power saving/monitoring.
    #
    #    If all timing calls go through this module,
    #    the underlying engine (currently glibs gobject)
    #    can be more easily changed than rewriting code everywhere.
    #
    #    Also, modRana targets mobile devices with limited power budget.
    #    If all timing goes through this module, rogue modules many frequent
    #    timers can be easily identified.
    #    It might be also possible to stop or pause some/all of the timers
    #    after a period of inactivity, or some such.

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)

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


class CronQt5(Cron):
    """A Qt 5 timing and scheduling module for modRana"""

    def __init__(self, *args, **kwargs):
        Cron.__init__(self, *args, **kwargs)
        self.nextId = 0
        # cronTab and activeIds should be in sync
        self.cronTab = {"idle": {}, "timeout": {}}
        self.dataLock = threading.RLock()

    def _timerTriggered(self, timerId):
        with self.dataLock:
            timerTuple = self.cronTab['timeout'].get(timerId)
            if timerTuple:
                call = timerTuple[6]
                call()
            else:
                self.log.error("unknown timer triggered: %s", timerId)

    def _getID(self):
        """get an unique id for timing related request that can be
        returned to the callers and used as a handle
        TODO: can int overflow in Python ?
        TODO: id recycling ?"""
        with self.dataLock:
            timeoutId = self.nextId
            self.nextId += 1
            return timeoutId

    def addTimeout(self, callback, timeout, caller, description, args=None):
        """the callback will be called timeout + time needed to execute the callback
        and other events
        """
        if not args: args = []
        timeoutId = self._getID()
        self.log.debug("qt5: adding a %s ms timeout from %s as %s", timeout, caller, timeoutId)
        # create a new function that calls the callback processing function
        # with thh provided arguments
        handleThisTimeout = lambda: self._doTimeout(timeoutId, callback, args)
        # store timer data
        # - we don't actually have a Python-side timer object, so we just store
        #   the callback function and tell QML to add the timer
        timeoutTuple = (callback, args, timeout, caller, description, timeoutId, handleThisTimeout)
        with self.dataLock:
            self.cronTab['timeout'][timeoutId] = timeoutTuple
            pyotherside.send("addTimer", timeoutId, timeout)

        # return the id
        return timeoutId

    def removeTimeout(self, timeoutId):
        """remove timeout with a given id"""
        with self.dataLock:
            if timeoutId in self.cronTab['timeout'].keys():
                caller = self.cronTab['timeout'][timeoutId][3]
                del self.cronTab['timeout'][timeoutId]
                pyotherside.send("removeTimer", timeoutId)
                self.log.debug("qt5: timeout %s from %s has been removed", timeoutId, caller)
            else:
                self.log.error("can't remove timeout, wrong id: %s", timeoutId)

    def modifyTimeout(self, timeoutId, newTimeout):
        """modify the duration of a timeout in progress"""
        with self.dataLock:
            if timeoutId in self.cronTab['timeout'].keys():
                # we don't store the timeout value Python-side,
                # so we just notify QML about the change
                pyotherside.send("modifyTimerTimeout", timeoutId, newTimeout)
            else:
                self.log.error("can't modify timeout, wrong id: %s", timeoutId)

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
