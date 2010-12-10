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
from base_module import ranaModule
import sys
import os
import socket
from time import *
import re

def getModule(m,d):
  return(gpsd2(m,d))

class gpsd2(ranaModule):
  """Supplies position info from GPSD"""
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.tt = 0
    self.position_regexp = re.compile('P=(.*?)\s*$')
    self.connected = False
    self.set('speed', None)
    self.set('metersPerSecSpeed', None)
    self.set('bearing', None)
    self.set('elevation', None)
    self.lControl = None
    self.lDevice = None
    self.location = None
    self.status = "Unknown"


  def firstTime(self):
    if self.device == 'n900':
      # start libLocation on the N900
      if self.get('GPSEnabled', True): # is GPS enabled ?
        self.libLocationStart()

    else:

      try:
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(("127.0.0.1", 2947)) #TODO: set this from options
        self.connected = True
      except socket.error:
        self.status = "No GPSD running"

  def libLocationStart(self):
      try:
        import location
        self.location = location
        try:
          self.lControl = location.GPSDControl.get_default()
          self.lDevice = location.GPSDevice()
        except Exception, e:
          print "gpsd:N900 - cant create location objects: %s" % e

        try:
          self.lControl.set_properties(preferred_method=location.METHOD_USER_SELECTED)
        except Exception, e:
          print "gpsd:N900 - cant set prefered location method: %s" % e

        try:
          self.lControl.set_properties(preferred_interval=location.INTERVAL_1S)
        except Exception, e:
          print "gpsd:N900 - cant set prefered location interval: %s" % e
        try:
          self.lControl.start()
          print "** gpsd:N900 - GPS successfully activated **"
          self.connected = True
        except Exception, e:
          print "gpsd:N900 - opening the GPS device failed: %s" % e
          self.status = "No GPSD running"
      except:
        self.status = "No GPSD running"
        print "gpsd:N900 - importing location module failed, please install the python-location package"
        self.sendMessage('notification:install python-location package to enable GPS#7')

  def libLocationStop(self):
    # stop the libLocation on N900
    if self.lControl:
      self.lControl.stop()
      # cleanup
      self.lControl = None
      self.lDevice = None
      self.location = None

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
          print "gps: enabling GPS"
          if self.device == 'n900':
            self.libLocationStart()
        elif state == False:
          print "gps: disabling GPS"
          if self.device == 'n900':
            self.set('fixType', 0) # a disabled GPS device can't see any satellites
            self.libLocationStop()

  def sendMessage(self,message):
    m = self.m.get("messages", None)
    if(m != None):
      print "mapData: Sending message: " + message
      m.routeMessage(message)
    else:
      print "mapData: No message handler, cant send message."

 
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

# it seems that at least with gpsfake, wee get only Empty as response
#  def DOP(self):
#    """return (three) estimated position errors in meters (DOP)"""
#    dop = self.socket_cmd("e")
#    print dop

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

  def update(self):
    dt = time() - self.tt
    #print(dt)
    if(dt < 1): #default 2
      return
    self.tt = time()
    if self.get('GPSEnabled', True) == False:
      # just make sure the screen updates atleast once per seccond
      self.set('needRedraw', True)
      return

    if(not self.connected):
      self.status = "Not connected"
      #print("not connected")
    elif self.device == 'n900':
      """
    from:  http://wiki.maemo.org/PyMaemo/Using_Location_API
    result tupple in order:
    * mode: The mode of the fix
    * fields: A bitfield representing which items of this tuple contain valid data
    * time: The timestamp of the update (location.GPS_DEVICE_TIME_SET)
    * ept: Time accuracy
    * latitude: Fix latitude (location.GPS_DEVICE_LATLONG_SET)
    * longitude: Fix longitude (location.GPS_DEVICE_LATLONG_SET)
    * eph: Horizontal position accuracy
    * altitude: Fix altitude in meters (location.GPS_DEVICE_ALTITUDE_SET)
    * double epv: Vertical position accuracy
    * track: Direction of motion in degrees (location.GPS_DEVICE_TRACK_SET)
    * epd: Track accuracy
    * speed: Current speed in km/h (location.GPS_DEVICE_SPEED_SET)
    * eps: Speed accuracy
    * climb: Current rate of climb in m/s (location.GPS_DEVICE_CLIMB_SET)
    * epc: Climb accuracy

      """
      location = self.location
      try:
        if self.lDevice.fix:
          fix = self.lDevice.fix

          self.set('fix', fix[0])
          """from liblocation reference:
          0 =	The device has not seen a satellite yet.
          1 =	The device has no fix.
          2 =	The device has latitude and longitude fix.
          3 =	The device has latitude, longitude, and altitude. 
          """

          if fix[1] & location.GPS_DEVICE_LATLONG_SET:
            (lat,lon) = fix[4:6]
            self.set('pos', (lat,lon))

          if fix[1] & location.GPS_DEVICE_TRACK_SET:
            bearing = fix[9]
            self.set('bearing', bearing)

          if fix[1] & location.GPS_DEVICE_SPEED_SET:
            self.set('speed', fix[11]) # km/h
            metersPerSecSpeed = fix[11]/3.6 # km/h -> metres per second
            self.set('metersPerSecSpeed', metersPerSecSpeed) # m/s

          if fix[1] & location.GPS_DEVICE_ALTITUDE_SET:
            elev = fix[7]
            self.set('elevation', elev)

          # TODO: remove when not needed
          if self.get('n900GPSDebug', False):
            print "## N900 GPS debugging info ##"
            print "fix tupple from the Location API:"
            print fix
            print "position,bearing,speed (in descending order):"
            print self.get('pos', None)
            print self.get('bearing', None)
            print self.get('speed', None)
            print "#############################"

        else:
          self.status = "Unknown"
          print "gpsd:N900 - getting fix failed (on a regular update)"
      except Exception, e:
        self.status = "Unknown"
        print "gpsd:N900 - getting fix failed (on a regular update + exception: %s)" % e

    else:
      result = self.socket_cmd("p")
      if(not result):
        self.status = "Unknown"
        #print("unknown")
      else:
        lat,lon = [float(ll) for ll in result.split(' ')]
        self.set('pos', (lat,lon))
        self.set('pos_source', 'GPSD')
#        self.set('needRedraw', True)
        self.status = "OK"

        bearing = self.bearing()
        if bearing != None:
          self.set('bearing', float(bearing))

        speed = self.speed()

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
             
#        self.satellites()

        elevation = self.elevation()
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
    self.set('needRedraw', True)
        #print(self.get('pos', None))
        #print(time())

  def shutdown(self):
    if self.device == 'n900':
      try:
        self.libLocationStop()
        print "gpsd:N900 - GPS device successfully stopped"
      except:
        print "gpsd:N900 - closing the GPS device failed"



if __name__ == "__main__":
  d = {}
  a = gpsd2({},d)
  print a.gpsStatus()
  #print a.quality()
  print a.satellites()

  if(0):
    for i in range(2):
      a.update()
      print "%s: %s" %(a.status, d.get('pos', None))
      sleep(2)

