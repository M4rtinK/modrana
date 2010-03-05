#!/usr/bin/python
#---------------------------------------------------------------------------
# Lookup the nearest road
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
import tilenames
import vmap_load

def getModule(m,d):
  return(nearestRoad(m,d))

class nearestRoad(ranaModule):
  """Handles messages"""
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.lastpos = [0,0]
    self.dataFilename = ''
    self.data = None

  def distancePointToLine(self, x,y,x1,y1,x2,y2):
    """http://www.allegro.cc/forums/thread/589720"""
    A = x - x1
    B = y - y1
    C = x2 - x1
    D = y2 - y1
    
    dot = A * C + B * D
    len_sq = C * C + D * D
    if len_sq==0:
      dist= A*A +B*B
      return(dist)

    param = dot / len_sq

    if(param < 0):
      xx = x1
      yy = y1
    elif(param > 1):
      xx = x2
      yy = y2
    else:
      xx = x1 + param * C
      yy = y1 + param * D

    dx = x - xx
    dy = y - yy
    dist = dx * dx + dy * dy
    return(dist)

  def describe(self, lat,lon):
    """Find the way you're nearest to, and return a description of it"""

    z = vmap_load.getVmapBaseZoom(self.d)
    (sx,sy) = tilenames.latlon2xy(lat,lon, z)
    
    # download local data
    filename = vmap_load.getVmapFilename(sx,sy,z,self.d)

    if(filename != self.dataFilename or self.data == None):
      #print "road loading %s" % (filename)
      self.data = vmap_load.vmapData(filename)
     
    # look for nearest way
    (mindist, name) = (1E+10, "not found")
    for wid,way in self.data.ways.items():
      (lastnlon,lastnlat,lastvalid) = (0,0,False)
      
      wayName = ''
      if(way.has_key('N')):
        wayName += way['N'] + " "
      if(way.has_key('r')):
        wayName += way['r'] + " "
      if(not wayName):
        wayName = "Way #%d" % wid

      for n in way['n']: # loop nodes in way
        (nlat,nlon,nid) = n
        if(lastvalid):
          distance =  self.distancePointToLine(nlon, nlat, lastnlon, lastnlat, lon, lat)
          
          if(distance < mindist):
            mindist = distance
            name = wayName
            #print "Selecting %s at %d" % (name, mindist)
            
        (lastnlon,lastnlat,lastvalid) = (lon,lat,True)
    #print "Done"
    return(name)
  
  def update(self):
    """If requested, lookup the nearest road name"""
    if(not self.get('lookup_road', False)):
      return
    if(self.get('noLookupRoads', False)):
      return
    pos = self.get('pos', None)
    if(pos != None):
      if(pos != self.lastpos):
        self.set('nearest_road', self.describe(pos[0], pos[1]))
        self.lastpos = pos

if(__name__ == '__main__'):
  d = {'lookup_road':True, 'pos':[51.678935, -0.826256]}
  a = nearestRoad({},d)
  a.update()
  print d.get('nearest_road')
  