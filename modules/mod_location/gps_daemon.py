# -*- coding: utf-8 -*-
# Supplies position info from the GPS daemon
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
import threading
from time import sleep, time

from base_position_source import PositionSource, Fix

class GPSD(PositionSource):
  def __init__(self,location):
    PositionSource.__init__(self, location)
#  def __init__(self, location):
#    PositionSource.__init__(location)

  def start(self):
    """start the GPSD based location update method"""
    try:
      self.GPSDConsumer = GPSDConsumer()
      self._checkVerbose() # check if verbose debugging is enabled
      self.GPSDConsumer.daemon = True
      self.GPSDConsumer.start()
      self.connected = True
    except Exception, e:
      print("location GPSD: connecting to GPSD failed", e)
      self.status = "No GPSD running"

  def stop(self):
    """stop the GPSD based location update method"""
    self.GPSDConsumer.shutdown()
    self.connected = False
    self.status = "No GPSD running"

  def _updateGPSD(self):
    # only update if connected to GPSD
    if self.connected:
      fix = self.GPSDConsumer.getFix()
      if fix:
        """
        as the GPSD consumer updates its values very often, it probably better to use a simple
        tuple instead of a Fix object and only convert to the Fix object once the position data
        is actually requested
        """
        (lat,lon,elevation,bearing,speed,timestamp) = fix
        fix = Fix( (lat,lon),
                   elevation,
                   bearing,
                   speed )
        self.fix = fix

  def _checkVerbose(self):
    verbose = self.location.get('gpsdDebugVerbose', False)
#    verbose = True
    if self.GPSDConsumer:
      if verbose:
        self.GPSDConsumer.setVerbose(True)
        print "location: gpsd debugging output turned ON"
      else:
        self.GPSDConsumer.setVerbose(False)
        print "location: gpsd debugging output turned OFF"
    else:
      print("location: gpsd not used, so there is no debug output to enable")


### Old commands for direct socket access to GPSD
#
#  def socket_cmd(self, cmd):
#    try:
#      self.s.send("%s\r\n" % cmd)
#    except:
#        print "something is wrong with the gps daemon"
#    result = self.s.recv(8192)
#    #print "Reply: %s" % result
#    expect = 'GPSD,' + cmd.upper() + '='
#    if(result[0:len(expect)] != expect):
#      print "Fail: received %s after sending %s" % (result, cmd)
#      return(None)
#    remainder = result[len(expect):]
#    if(remainder[0:1] == '?'):
#      print "Fail: Unknown data in " + cmd
#      return(None)
#    return(remainder)
#
#  def test_socket(self):
#    for i in ('i','p','p','p','p'):
#      print "%s = %s" % (i, self.socket_cmd(i))
#      sleep(1)
#
#  def gpsStatus(self):
#    return(self.socket_cmd("M"))
#
#  def bearing(self):
#    """return bearing as reported by gpsd"""
#    return self.socket_cmd("t")
#
#  def elevation(self):
#    """return elevation as reported by gpsd
#  (meters above mean sea level)"""
#    return self.socket_cmd("a")
#
#  def speed(self):
#    """return speed in knots/sec as reported by gpsd"""
#    return self.socket_cmd("v")
#
#  def GPSTime(self):
#    """return a string representing gps time
#  in this format: D=yyyy-mm-ddThh:nmm:ss.ssZ (fractional seccond are not guarantied)
#  (for tagging trackpoints with accurate timestamp ?)"""
#    timeFromGPS = self.socket_cmd("d")
#    return timeFromGPS
#
#  def satellites(self):
#    list = self.socket_cmd('y')
#    if(not list):
#      return
#    parts = list.split(':')
#    (spare1,spare2,count) = parts[0].split(' ')
#    count = int(count)
#    self.set("gps_num_sats", count)
#    for i in range(count):
#      (prn,el,az,db,used) = [int(a) for a in parts[i+1].split(' ')]
#      self.set("gps_sat_%d"%i, (db,used,prn))
#      #print "%d: %d, %d, %d, %d, %d" % (i,prn,el,az,db,used)
#
#  def quality(self):
#    result = self.socket_cmd('q')
#    if result:
#      (count,dd,dx,dy) = result.split(' ')
#      count = int(count)
#      (dx,dy,dd) = [float(a) for a in (dx,dy,dd)]
#      print "%d sats, quality %f, %f, %f" % (count,dd,dx,dy)

class GPSDConsumer(threading.Thread):
  """consume data as they come in from the GPSD and store last known fix"""
  def __init__(self):
    threading.Thread.__init__(self)
    self.lock = threading.RLock()
    self.stop = False
    import gps_module as gps
    self.session = gps.gps(host="localhost", port="2947")
    self.session.stream(flags=gps.client.WATCH_JSON)
    self.verbose = False
    # vars
    self.fix = None

  def run(self):
    import gps_module as gps
    print("GPSDConsumer: starting\n")
    while True:
      if self.stop == True:
        print "GPSDConsumer: breaking\n"
        break
      self.session.next() # this function blocks until a new fix is available
      sf = self.session.fix
      if sf.mode != gps.MODE_NO_FIX:
        with self.lock:
          self.fix = (sf.latitude,sf.longitude,sf.altitude,sf.track,sf.speed, time())
          if self.verbose:
#          if 1:
            print self.fix
      else:
        if self.verbose:
          print("GPSDConsumer: NO FIX, will retry in 1 s")
        sleep(1)
    print("GPSDConsumer: stopped\n")

  #      if r["class"] == "TPV":
  #        with self.lock:
  #          try:
  #            self.fix = (r['lat'],r['lon'],r['alt'],r['track'],r['speed'], time())
  #          except Exception, e:
  #            print("GPSDConsumer: error reading data", e)

  def shutdown(self):
    print("GPSDConsumer: stopping")
    self.stop = True

  def getFix(self):
    with self.lock:
      return self.fix

  def setVerbose(self, value):
    with self.lock:
      self.verbose = value