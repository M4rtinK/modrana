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

# Why is QGeoSatelliteInfoSource commented out ?
#
# If you connect the in view or in use signal, the whole freezes
# becomes stuck after the first callback. :)
# If this is only a Harmattan specific behaviour, it might be possible
# to check for Harmattan and enable it on other platforms.
import sys

print("importing Qt Mobility")
#from QtMobility.Location import QGeoSatelliteInfoSource
print("Qt Mobility imported")

from base_position_source import PositionSource
from core.fix import Fix


class QtMobility(PositionSource):
  def __init__(self, location):
    PositionSource.__init__(self, location)

    self.qtApplication = None # used for headless location support

    # connect to QT Mobility position source
    self.source = None
    #    self.satelliteSource = QGeoSatelliteInfoSource.createDefaultSource(None)
    self.satsInViewCount = None
    self.satsInUseCount = None
    #    if self.satelliteSource is not None:
    ##      self.satelliteSource.satellitesInViewUpdated.connect(self._satsInViewUpdateCB)
    ##      self.satelliteSource.satellitesInViewUpdated.connect(self._satsInUseUpdateCB)
    #      print("location Qt Mobility: satellite info source created")
    #    else:
    #      print("location Qt Mobility: satellite info source creation failed")

  def start(self, startMainLoop=False):
    if startMainLoop:
      from PySide.QtCore import QCoreApplication

      self.qtApplication = QCoreApplication(sys.argv)
      # we import QGeoPositionInfoSource after the Qt Application is
    # created to get rid of the:
    # "
    # QDBusConnection: system D-Bus connection created before QCoreApplication. Application may misbehave.
    # QDBusConnection: session D-Bus connection created before QCoreApplication. Application may misbehave.
    # "
    # warnings
    from QtMobility.Location import QGeoPositionInfoSource

    self.source = QGeoPositionInfoSource.createDefaultSource(None)
    if self.source is not None:
      self.source.positionUpdated.connect(self._positionUpdateCB)
      print("location Qt Mobility: position source created")
      # TODO: custom interval setting
      self.source.setUpdateInterval(1000)
      self.source.startUpdates()
      print("location qt mobility: started")

      # only start the mainloop if the source was created successfully,
      # otherwise it would never end as the signal provided by the source,
      # that stops the main lopp, would never be triggered
      if startMainLoop:
        print("location qt mobility: starting headless mainloop")
        self.qtApplication.exec_()
    else:
      print("location Qt Mobility: source creation failed")
      #    if self.satelliteSource:
      #      print self.satelliteSource.availableSources()
      #      self.satelliteSource.startUpdates()
      #      print("location qt mobility: sat source started")

  def stop(self):
    print("location qt mobility: stopping")
    if self.source:
      self.source.stopUpdates()
      print("location qt mobility: stopped")
    if self.qtApplication:
      print("location qt mobility: stopping headless mainloop")
      self.qtApplication.exit()
      #    if self.satelliteSource:
      #      self.satelliteSource.stopUpdates()
      #      print("location qt mobility: sat source stopped")

  def canSetUpdateInterval(self):
    return True

  def setUpdateInterval(self, interval):
    if self.source:
      self.source.setUpdateInterval(interval)

  def getFix(self):
    return self.fix

  #  def _satsInViewUpdateCB(self, satellites=None):
  #    """update the count of visible GPS satellites"""
  #    if satellites is not None:
  #      self.satsInViewCount = len(satellites)
  #
  #  def _satsInUseUpdateCB(self, satellites=None):
  #    """update the count of GPS satellites in use to
  #     determine the current position"""
  #    if satellites is not None:
  #      self.satsInUseCount = len(satellites)

  def _positionUpdateCB(self, update):
    direction = update.attribute(update.Direction)
    speed = update.attribute(update.GroundSpeed)
    mode = 3 # 3d fix
    if update.coordinate().isValid():
      if update.coordinate().CoordinateType == update.coordinate().Coordinate2D:
        mode = 2 # 2D fix
    else:
      mode = 0 # no fix

    if direction == -1.0:
      direction = 0
    if speed == -1.0:
      speed = 0

    fix = Fix((update.coordinate().latitude(),
               update.coordinate().longitude()),
              update.coordinate().altitude(),
              direction,
              speed,
              mode=mode,
              magnetic_variation=update.attribute(update.MagneticVariation),
              sats=self.satsInViewCount,
              sats_in_use=self.satsInUseCount,
              horizontal_accuracy=update.attribute(update.HorizontalAccuracy),
              vertical_accuracy=update.attribute(update.VerticalAccuracy)
    )
    # print debug message if enabled
    #    self.debug = True
    if self.debug:
      print("Qt-Mobility POS DEBUG")
      print ("%s, %s" % (update.coordinate().latitude(), update.coordinate().longitude()))
      print(update)

    # trigger update in the location module
    self.location.updatePosition(fix)
    self.fix = fix