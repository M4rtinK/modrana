#!/usr/bin/python
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Calculate speed, time, etc. from position
#---------------------------------------------------------------------------
# Copyright 2007-2008, Oliver White
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
from modules.base_module import ranaModule
from core import geo
from time import *

def getModule(m,d,i):
  return(stats(m,d,i))

class stats(ranaModule):
  """Handles messages"""
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.minimalSpeed = 2 #  in kmh, we don't update the avg speed if the current speed is like this
    self.lastT = None
    self.maxSpeed = 0
    self.avg1 = 0
    self.avg2 = 0
  
  def update(self):
    # Run scheduledUpdate every second
    t = time()
    if(self.lastT == None):
      self.scheduledUpdate(t, 1, True) # dt should not be 0 because we use it for division
      self.lastT = t
    else:
      dt = t - self.lastT
      if(dt > 1):
        self.scheduledUpdate(t, dt)
        self.lastT = t
  
  def scheduledUpdate(self, t, dt, firstTime=False):
    """Called every dt seconds"""
    pos = self.get('pos', None)
    if(pos == None):
      return # TODO: zero stats

    speed = self.get('speed', None)
    if speed == None or speed<=self.minimalSpeed:
      """we have no data, or the speed is below the threshold (we are not moving)"""
      return

    average = 0

    if(speed > self.maxSpeed):
      self.maxSpeed = speed
    self.avg1 += speed
    self.avg2 += dt
    average = self.avg1/self.avg2

    self.set('maxSpeed', self.maxSpeed)
    self.set('avgSpeed', average)


if(__name__ == '__main__'):
  d = {'pos':[51, -1]}
  a = stats({},d)
  a.update()
  d['pos'] = [52, 0]
  a.update()
  print d.get('speed')
  