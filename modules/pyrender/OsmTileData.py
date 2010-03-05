#!/usr/bin/python
#----------------------------------------------------------------------------
# Download OSM data covering the area of a slippy-map tile 
#
# Features:
#  * Recursive (downloads are all at z15, and merged if necessary to get
#    a larger area)
#  * Cached (all downloads stored in cache/z/x/y/data.osm)
# 
# DON'T RUN THIS ON LARGE AREAS WITHOUT ASKING THE OPERATOR OF THE
# API SERVER.  Currently it's limited to downloading a z-13 area or smaller
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
from tilenames import *
from urllib import *
from OsmMerge import OsmMerge
import os
import os.path

def GetOsmTileData(z,x,y, AllowSplit = False):
  """Download OSM data for the region covering a slippy-map tile"""
  if(x < 0 or y < 0 or z < 0 or z > 25):
    print "Disallowed %d,%d at %d" % (x,y,z)
    return
  
  DownloadLevel = 15  # All primary downloads are done at a particular zoom level
  
  MergeLevels = 2  # How many layers 'below' the download level to go
  
  directory = 'cache/%d/%d' % (z,x)
  filename = '%s/%d.osm' % (directory,y)
  if(not os.path.exists(directory)):
    os.makedirs(directory)
  
  if(z == DownloadLevel):
    # Download the data
    (S,W,N,E) = tileEdges(x,y,z)
    
    
    # Which API to use
    if(1): 
      URL = 'http://%s/api/0.5/map?bbox=%f,%f,%f,%f' % ('api.openstreetmap.org',W,S,E,N)
    else:
      URL = 'http://%s/api/0.5/*[bbox=%f,%f,%f,%f]' % ('www.informationfreeway.org',W,S,E,N)
    
    if(not os.path.exists(filename)): # TODO: allow expiry of old data
      print "Downloading %s\n  from %s" % (filename, URL)
      try:
        urlretrieve(URL, filename)
        print "Done"
      except:
        print "Error downloading " + filename
        unlink(filename)
        return
    else:
      print "Using cached %s" % filename
    return(filename)
    
  elif(z < DownloadLevel - MergeLevels):
    print "Zoom %d not allowed" % z
    return
  
  elif(z < DownloadLevel):  
    # merge smaller tiles
    filenames = []
    for i in (0,1):
      for j in (0,1):
        lx = x * 2 + i
        ly = y * 2 + j
        lz = z + 1
        print "Downloading subtile %d,%d at %d" % (x,y,z)
        # download (or otherwise obtain) each subtile
        filenames.append(GetOsmTileData(lz,lx,ly,AllowSplit))
    # merge them together
    print "Merging tiles together"
    OsmMerge(filename, filenames)
    return(filename)
    
  else: 
    # use larger tile
    while(z > DownloadLevel):
      z = z - 1
      x = int(x / 2)
      y = int(y / 2)
    return(GetOsmTileData(z,x,y))

if(__name__ == "__main__"):
  """test mode"""
  GetOsmTileData(14,7788,6360, True)
  
