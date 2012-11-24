# -*- coding: utf-8 -*-
# Supplies position info from Qt Mobility
#---------------------------------------------------------------------------
# Copyright 2012, Martin Kolman
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

#from QtMobility.Location import QGeoPositionInfoSource
print("importing Qt Mobility")
from QtMobility.Location import QGeoPositionInfoSource
print("Qt Mobility imported")

from base_position_source import PositionSource, Fix

class QtMobility(PositionSource):
  def __init__(self, location):
    PositionSource.__init__(self, location)

    # connect to QT Mobility position source
    self.source = QGeoPositionInfoSource.createDefaultSource(None)
    if self.source is not None:
      self.source.positionUpdated.connect(self._positionUpdateCB)
      print("location Qt Mobility: position source created")
    else:
      print("location Qt Mobility: source creation failed")

  def start(self):
    if self.source is not None:
      # TODO: custom interval setting
      self.source.setUpdateInterval(1000)
      self.source.startUpdates()
      print("location qt mobility: started")

  def stop(self):
    print("location qt mobility: stopping")
    if self.source:
      self.source.stopUpdates()
      print("location qt mobility: stopped")

  def canSetUpdateInterval(self):
    return True

  def setUpdateInterval(self, interval):
    if self.source:
      self.source.setUpdateInterval(interval)

  def getFix(self):
    return self.fix

  def _positionUpdateCB(self, update):
    direction = update.attribute(update.Direction)
    speed = update.attribute(update.GroundSpeed)
    if direction == -1.0:
      direction = 0
    if speed == -1.0:
      speed = 0

    fix = Fix( (update.coordinate().latitude(),
                update.coordinate().longitude()),
               update.coordinate().altitude(),
               direction,
               speed
             )
    # print debug message if enabled
    if self.debug:
      print("Qt-Mobility POS DEBUG")
      print ("%s, %s" % (update.coordinate().latitude(), update.coordinate().longitude()))
      print(update)

    # trigger update in the location module
    self.location.updatePosition(fix)
    self.fix = fix