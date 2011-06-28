# supplies position info from the GPS daemon
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
from __future__ import with_statement # for python 2.5
from base_module import ranaModule
import threading
from time import *
import gps_module as gps

def getModule(m,d,i):
  return(gpsd2(m,d,i))

class gpsd2(ranaModule):
  """Supplies position info from GPSD"""
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.tt = 0
    self.connected = False
    self.set('speed', None)
    self.set('metersPerSecSpeed', None)
    self.set('bearing', None)
    self.set('elevation', None)
    self.status = "Unknown"
    self.locationUpdate = self.nop

    # GPSD support
    self.GPSDConsumer = None

  def nop(self):
    """navigation update function placeholder"""
    pass

  def firstTime(self):
    # start screen update 1 per second screen update
    # TODO: event based redrawing
    cron = self.m.get('cron', None)
    if cron:
      cron.addTimeout(self.screenUpdateCB, 1000, self, "screen and GPSD update")

    # start location if persistantly enabled
    if self.get('GPSEnabled', True): # is GPS enabled ?
      self.startLocation()

  def screenUpdateCB(self):
    """update the screen and also GPSD location if enabled
    TODO: more efficient screen updates"""
#    print "updating screen"
    self.locationUpdate()
    self.set('needRedraw', True)

  def startGPSD(self):
    """start the GPSD based location update method"""
    try:
      self.GPSDConsumer = GPSDConsumer()
      self.GPSDConsumer.start()
      self.connected = True
      self.locationUpdate = self.updateGPSD
    except Exception, e:
      print("location: connecting to GPSD failed", e)
      self.status = "No GPSD running"

  def stopGPSD(self):
    """stop the GPSD based location update method"""
    self.GPSDConsumer.shutdown()
    self.locationUpdate = self.nop
    self.status = "No GPSD running"

  def handleMessage(self, message, type, args):
    if message == "setPosLatLon" and type == "ml":
      if args and len(args) == 2:
        lat = float(args[0])
        lon = float(args[1])
        print "gps:setting current position to: %f,%f" % (lat,lon)
        self.set('pos',(lat,lon))
    elif message == "checkGPSEnabled":
        state = self.get('GPSEnabled', True)
        if state == True:
          self.startLocation()
        elif state == False:
          self.stopLocation()

  def startLocation(self):
    """start location - device based or gpsd"""
    print "location: enabling location"
    if self.dmod.handlesLocation():
      self.dmod.startLocation()
    else:
      self.startGPSD()

  def stopLocation(self):
    """stop location - device based or gpsd"""
    print "location: disabling location"
    if self.dmod.handlesLocation():
      self.dmod.stopLocation()
    else:
      self.stopGPSD()
 
  def socket_cmd(self, cmd):
    try:
      self.s.send("%s\r\n" % cmd)
    except:
      print "something is wrong with the gps daemon"
    result = self.s.recv(8192)
    #print "Reply: %s" % result
    expect = 'GPSD,' + cmd.upper() + '='
    if(result[0:len(expect)] != expect):
      print "Fail: received %s after sending %s" % (result, cmd)
      return(None)
    remainder = result[len(expect):]
    if(remainder[0:1] == '?'):
      print "Fail: Unknown data in " + cmd
      return(None)
    return(remainder)
    
  def test_socket(self):
    for i in ('i','p','p','p','p'):
      print "%s = %s" % (i, self.socket_cmd(i))
      sleep(1)
      
  def gpsStatus(self):
    return(self.socket_cmd("M"))

  def bearing(self):
    """return bearing as reported by gpsd"""
    return self.socket_cmd("t")
    
  def elevation(self):
    """return elevation as reported by gpsd
    (meters above mean sea level)"""
    return self.socket_cmd("a")

  def speed(self):
    """return speed in knots/sec as reported by gpsd"""
    return self.socket_cmd("v")

  def GPSTime(self):
    """return a string representing gps time
    in this format: D=yyyy-mm-ddThh:nmm:ss.ssZ (fractional seccond are not guarantied)
    (for tagging trackpoints with acurate timestamp ?)"""
    timeFromGPS = self.socket_cmd("d")
    return timeFromGPS

  def satellites(self):
    list = self.socket_cmd('y')
    if(not list):
      return
    parts = list.split(':')
    (spare1,spare2,count) = parts[0].split(' ')
    count = int(count)
    self.set("gps_num_sats", count)
    for i in range(count):
      (prn,el,az,db,used) = [int(a) for a in parts[i+1].split(' ')]
      self.set("gps_sat_%d"%i, (db,used,prn))
      #print "%d: %d, %d, %d, %d, %d" % (i,prn,el,az,db,used)

  def quality(self):
    result = self.socket_cmd('q')
    if(result):
      (count,dd,dx,dy) = result.split(' ')
      count = int(count)
      (dx,dy,dd) = [float(a) for a in (dx,dy,dd)]
      print "%d sats, quality %f, %f, %f" % (count,dd,dx,dy)

  def updateGPSD(self):    
    fix = self.GPSDConsumer.getFix()
    if fix:
      (lat,lon,elevation,bearing,speed,timestamp) = fix

      # position
      self.set('pos', (lat,lon))
      self.set('pos_source', 'GPSD')
      self.status = "OK"
      # bearing
      self.set('bearing', float(bearing))
      # speed
      if speed != None:
        # normal gpsd reports speed in knots per second
        gpsdSpeed = self.get('gpsdSpeedUnit', 'knotsPerSecond')
        if gpsdSpeed == 'knotsPerSecond':
          # convert to meters per second
          speed = float(speed) * 0.514444444444444 # knots/sec to m/sec
        self.set('metersPerSecSpeed', speed)
        self.set('speed', float(speed) * 3.6)
      else:
        self.set('metersPerSecSpeed', None)
        self.set('speed', None)
      # elevation
      if elevation:
        self.set('elevation', elevation)
      else:
        self.set('elevation', None)

    # make the screen refresh after the update
    # even when centering is turned off
    # TODO: make this more efficinet !
    # * only redraw when the position actually changes
    # * do we need to dedraw when we momentarily dont know the position ?
    # * redraw only the needed part of the screen
    # -> make scrolling more efficinet
    #  * reuse the alredy drawn area ?
    #  * dont overdraw the whole screen for a simple nudge ?
    #  * draw the new area with a delay/after the drag ended ?

  def shutdown(self):
    try:
      self.stopLocation()
    except Exception, e:
      print "location: stopping location failed", e

class GPSDConsumer(threading.Thread):
  """consume data as they come in from the GPSD and store last known fix"""
  def __init__(self):
    threading.Thread.__init__(self)
    self.lock = threading.RLock()
    self.stop = False
    self.session = gps.gps(host="localhost", port="2947")
    self.session.stream(flags=gps.client.WATCH_JSON)
    self.verbose = False
    # vars
    self.fix = None

  def run(self):
    print("GPSDConsumer: starting")
    while True:
      if self.stop == True:
        print "breaking"
        break
      r = self.session.next()
      if self.verbose:
        print r
      if r["class"] == "TPV":
        with self.lock:
          try:
            self.fix = (r['lat'],r['lon'],r['alt'],r['track'],r['speed'], time())
          except Exception, e:
            print("GPSDConsumer: eror reading data", e)

    print("GPSDConsumer: stoped")

  def shutdown(self):
    print("GPSDConsumer: stopping")
    self.stop = True

  def getFix(self):
    with self.lock:
      return self.fix

  def setVerbose(self, value):
    with self.lock:
      self.verbose = value
