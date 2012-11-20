#!/usr/bin/python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Load GPX file and show the track on map
#----------------------------------------------------------------------------
# Copyright 2010, Martin Kolman
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
from modules.base_module import ranaModule
from upoints import gpx

def getModule(m,d,i):
  return ShowTracklogs(m,d,i)

class ShowTracklogs(ranaModule):
  """draws a GPX track on the map"""
  
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    
    self.tracks = {} #dictionary of tracklists TODO: support tracklists with same filenames
    #self.tracks_filelist = {} #dictionary in form of filename:key_in_tracks
    
  def load(self, filename):
    """load a GPX file to datastructure"""
    file = open(filename, 'r')

    if(file):
      track = gpx.Trackpoints() # create new Trackpoints object
      track.import_locations(file) # load a gpx file into it
      self.tracks[filename] = track
      file.close()
    else:
      print "No file"
  def drawMapOverlay(self, cr):
    pass

      

if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
