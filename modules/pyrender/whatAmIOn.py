#!/usr/bin/python
#----------------------------------------------------------------------------
# Describes the feature you're standing on (road, rail, etc)
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
from parseOsm import parseOsm
import tiledata 
from tilenames import *
import sys

def distancePointToLine(x,y,x1,y1,x2,y2):
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

def describe(lat,lon):
  """Find the way you're nearest to, and return a description of it"""
  (sx,sy) = latlon2relativeXY(lat,lon)

  # download local data
  z = tiledata.DownloadLevel()
  (x,y) = tileXY(lat, lon, z)
  filename = tiledata.GetOsmTileData(z,x,y)

  # load into memory
  a = parseOsm(filename)

  # look for nearest way
  (mindist, name) = (1E+10, "not found")
  for w in a.ways.values():
    (lastx,lasty,lastvalid) = (0,0,False)
    for n in w['n']: # loop nodes in way
      (x,y) = (n['lon'], n['lat'])
      if(lastvalid):
        distance =  distancePointToLine(sx,sy,lastx,lasty,x,y)
        if(distance < mindist):
          tempname = w['t'].get('name', w['t'].get('ref', None))
          if(tempname != None):
            mindist = distance
            name=tempname
      (lastx,lasty,lastvalid) = (x,y,True)
  return(name)

if(__name__ == "__main__"):
  if(len(sys.argv) >= 3):
    print describe(float(sys.argv[1]), float(sys.argv[2]))
  else:
    print "no position supplied, using default"
    print describe(51.678935, -0.826256)