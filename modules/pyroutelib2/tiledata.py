#!/usr/bin/python
#----------------------------------------------------------------------------
# Download OSM data covering the area of a slippy-map tile 
#
# Features:
#  * Cached (all downloads stored in cache/z/x/y/data.osm)
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
from urllib import *
import os

def DownloadLevel():
  """All primary downloads are done at a particular zoom level"""
  return(15)

def GetOsmTileData(z,x,y):
  """Download OSM data for the region covering a slippy-map tile"""
  if(x < 0 or y < 0 or z < 0 or z > 25):
    print "Disallowed %d,%d at %d" % (x,y,z)
    return
  
  directory = 'cache/%d/%d/%d' % (z,x,y)
  filename = '%s/data.osm' % (directory)
  if(not os.path.exists(directory)):
    os.makedirs(directory)
  
  if(z == DownloadLevel()):
    # Download the data
    URL = 'http://dev.openstreetmap.org/~ojw/api/?/map/%d/%d/%d' % (z,x,y)
     
    if(not os.path.exists(filename)): # TODO: allow expiry of old data
      urlretrieve(URL, filename)
    return(filename)
    
  elif(z > DownloadLevel()):
    # use larger tile
    while(z > DownloadLevel()):
      z = z - 1
      x = int(x / 2)
      y = int(y / 2)
    return(GetOsmTileData(z,x,y))
  return("")

if(__name__ == "__main__"):
  """test mode"""
  print GetOsmTileData(15, 16218, 10741)
