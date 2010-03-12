#!/usr/bin/python
#----------------------------------------------------------------------------
# Log position as GPX, draw the track traveled
#----------------------------------------------------------------------------
# Copyright 2008, Oliver White
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
#import re
import random
from time import *

def getModule(m,d):
  return(tracklog(m,d))

class tracklog(ranaModule):
  """Record and display tracklogs"""
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.nodes = []
    self.updateTime = 0
    self.startupTimestamp = strftime("%Y%m%dT%H%M%S")
    self.lastx = 0
    self.lasty = 0

  def saveMinimal(self, filename):
    try:
      f = open(filename, "w")
      for n in self.nodes:
        f.write("%f,%f\n"%n)
      f.close();
    except IOError:
      print "Error saving tracklog" # TODO: error reporting
    
  def load(self, filename):
    # TODO: share this with replayGpx
    self.nodes = []
    file = open(filename, 'r')
    if(file):
      track = gpx.Trackpoints() # create new Trackpoints object
      track.import_locations(file) # load a gpx file into it
      for point in track[0]: #iterate over the points, track[0] is list of all points in file
        lat = point.latitude
        lon = point.longitude
        self.nodes.append([lat,lon])
      file.close()
      self.numNodes = len(self.nodes)
      self.set("centreOnce", True)
      self.pos = int(self.get("replayStart",0) * self.numNodes)
      
#only for GPX 1.0, the above works for GPX 1.1
#      regexp = re.compile("<trkpt lat=['\"](.*?)['\"] lon=['\"](.*?)['\"]")
#      for text in file:
#        matches = regexp.match(text)
#        if(matches):
#          lat = float(matches.group(1))
#          lon = float(matches.group(2))
#          self.nodes.append([lat,lon])
#      file.close()

  def scheduledUpdate(self):
    pos = self.get('pos', None)
    if(pos != None):
      self.nodes.append(pos)
      #(lat,lon) = pos
      #print "Logging %f, %f" % (lat,lon)
    self.saveMinimal("data/tracklogs/%s.txt" % self.startupTimestamp);

  def drawMapOverlay(self, cr):
    # Where is the map?
    proj = self.m.get('projection', None)
    if(proj == None):
      return
    if(not proj.isValid()):
      return

    # Draw all trackpoints as lines (TODO: optimisation)
    cr.set_source_rgb(0,0,0.5)
    first = True
    for n in self.nodes:
      (lat,lon) = n
      (x,y) = proj.ll2xy(lat,lon)
      if(proj.onscreen(x,y)):
        if first: #the first coordintes are wrong co we skip them
          self.line(cr, x, y)
          first = False
        else:
          self.line(cr, x, y)
          
      cr.fill()
    
  def point(self, cr, x, y):
    s = 2 #default 2
    cr.rectangle(x-s,y-s,2*s,2*s)
    #print(x,y)

  def line(self, cr, x, y):
    """ draws a line from xb*yb to xe*ye """
    cr.set_line_width(5)
    #cr.set_source_rgb(0.0, 0.0, 0.8)
    cr.line_to(x,y)
    cr.stroke()
    self.lastx = x
    self.lasty = y

#    s = 2 #default 2
#    cr.rectangle(x-s,y-s,2*s,2*s)
#    last_x = x
#    last_y = y
    #print("bod")

  def update(self):
    # Run scheduledUpdate every second
    t = time()
    dt = t - self.updateTime
    if(dt > self.get("logPeriod", 2)):
      self.updateTime = t
      self.scheduledUpdate()


