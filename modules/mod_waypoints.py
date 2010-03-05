#!/usr/bin/python
#----------------------------------------------------------------------------
# Handles user-defined waypoints
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
from base_poi import poiModule
import cairo
from datetime import *
import math

def getModule(m,d):
  return(waypoints(m,d))

class waypoints(poiModule):
  """Lookup nearest town or village"""
  def __init__(self, m, d):
    poiModule.__init__(self, m, d)
    self.poi = {'default':[]}
    self.load("data/waypoints.txt")
    self.counter = self.nextWaypoint()

  def firstTime(self):
    #m = self.m.get('menu', None)
    #if(m != None):
    #  m.register("places", "list", self.moduleName)
    #  for type in self.poi.keys():
    #    m.register("poi:"+type, "list", self.moduleName)
    pass

  def save(self, filename):
    f = open(filename, "w")
    for i in self.poi['default']:
      f.write("%f\t%f\t%s\n" % (i['lat'],i['lon'],i['name']))
    f.close()
    
  def load(self, filename):
    self.filename = filename
    try:
      file = open(filename,"r")
      for line in file:
        line = line.strip()
        (lat,lon,name) = line.split("\t")
        self.addItem("default", name, lat, lon)
      self.needUpdate = True # Request update of meta-info
    except IOError:
      return
        
  def newWaypoint(self):
    pos = self.get('pos', None)
    if(pos == None):
      return("ERR:No position")
    (lat,lon) = pos
    name = "%d" % self.counter
    self.addItem("default", name, lat, lon)
    self.save(self.filename)
    self.counter = self.nextWaypoint()
    return(name)

  def nextWaypoint(self):
    used = {}
    for p in self.poi['default']:
      used[p['name']] = True
    for i in range(1, 100000):
      if(not used.has_key("%d"%i)):
        return(i)
    return("ERR:No number")
    

      
      
if(__name__ == "__main__"):
  a = placenames({},{})
  a.load("../places.txt")
  print a.lookup(51.3,-0.5)