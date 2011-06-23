#!/usr/bin/python
#----------------------------------------------------------------------------
# A timing and sheduling module for modRana.
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
from base_module import ranaModule
import gobject
import threading

def getModule(m,d,i):
  return(Cron(m,d,i))

class Cron(ranaModule):
  """A timing and sheduling module for modRana."""

  """Why is there a specuial module for timing ?
     The reason is twofold:
     Toolkit independence and power saving/monitoring.

     If all timing calls go throgh this module,
     the undelying engine (currently glibs gobject)
     can be more easily changed thant rewriting code everywhere.

     Also, modRana targets mobile devices with limited power budget.
     If all timing goes throught this module, rogue modules many frequent
     timers can be easily identified.
     It might be also possible to stop or pause some/all of the timers
     after a period of inactivity, or some such.
  """
  
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.nextId = 0
    # cronTab and activeIds should be in sync
    self.cronTab = {"idle":{}, "timeout":{}}
#    self.info = {}
    self.dataLock = threading.RLock()

  def _getID(self):
    """get an unique id for timing related request that can be
    returned to the callers and used as a handle
    TODO: can int overflow in Python ?"""
    id = self.nextId
    self.nextId+=1
    return id

  def addIdle(self, callback, args):
    """add a callback that is called once the main loop becomes idle"""
    gobject.idle_add(callback, *args)

  def addTimeout(self, callback, timeout, caller, description, args=[]):
    """the callback will be called timeout + time needed to execute the callback
    and other events"""
    id = self._getID()
    # TODO: other backends
    realId = gobject.timeout_add(timeout, self._doTimeout, id, callback, args)
    timeoutTupple = (callback, args, timeout, caller, description, realId)
    with self.dataLock:
      self.cronTab['timeout'][id] = timeoutTupple

  def removeTimeout(self, id):
    """remove timeout with a given id"""
    with self.dataLock:
      if id in self.cronTab['timeout'].keys():
        (callback, args, timeout, caller, description, realId) = self.cronTab['timeout'][id]
        del self.cronTab['timeout'][id]
        gobject.source_remove(realId)
      else:
        print("cron: can't remove timeout, wrong id: ", id)

  def modifyTimeout(self,id, newTimeout):
    """modify the duration of a timeout in progress"""
    with self.dataLock:
      if id in self.cronTab['timeout'].keys():
        # load the timeout description
        (callback, args, timeout, caller, description, realId) = self.cronTab['timeout'][id]
        gobject.source_remove(realId) # remove the old timeout
        realId = gobject.timeout_add(self._doTimeout, newTimeout, id, callback, args) # new timeout
        # update the timeout description
        self.cronTab['timeout'][id] = (callback, args, newTimeout, caller, description, realId)
      else:
        print("cron: can't modify timeout, wrong id: ", id)

  def _doTimeout(self, id, callback, args):
    """wraper about the timeout function, which makes it possible to check
    if a timeout is still in progress from the "outside"
    - like this, the underlying timer should also be easily replacable
    """

    if callback(*args) == False:
      # the callback returned False,
      # that means it wants to quit the timeout

      # stop tracking
      self.removeTimeout(id)
      # propagate the quit signal
      return False
    else:
      return True # just run the loop



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


if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
