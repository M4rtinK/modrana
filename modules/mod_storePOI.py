#!/usr/bin/python
#----------------------------------------------------------------------------
# Store POI data.
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
from base_module import ranaModule
import time
import cPickle
import os

def getModule(m,d):
  return(storePOI(m,d))

class storePOI(ranaModule):
  """Store POI data."""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.folder = self.get('POIFolder', 'data/poi/')
    self.GLSResultFolder = self.folder + 'gls/'
    self.points = {}
    self.points['GLS'] = []
    self.load()
    
  def update(self):
    pass
#    # Get and set functions are used to access global data
#    self.set('num_updates', self.get('num_updates', 0) + 1)
#    #print "Updated %d times" % (self.get('num_updates'))

  def load(self):
    # load GLS Results from files
#    start = time.clock()
    GLSfiles = os.listdir(self.GLSResultFolder)
    for file in GLSfiles:
      f = open(self.GLSResultFolder + file,'r')
      result = cPickle.load(f)
      f.close()
      self.points['GLS'].append(result)
#    print "Loading POI took %1.2f ms" % (1000 * (time.clock() - start))
    pass

  def storeGLSResult(self, GLSResult):
    timestamp = time.strftime("%Y%m%dT%H%M%S")
    self.GLSResultExtension = '.gls'
    path = self.folder + timestamp + self.GLSResultFolder
    print path
    f = open(path, 'w')
    cPickle.dump(GLSResult,f)
    f.close()

  def loadGLSResultFromFile(self, f):
    GLSResult = cPickle.load(f)
    return GLSResult

class POI():
  """A basic class representing a POI."""
  def __init__(self, trackpointsList, tracklogFilename):
    self.name = None
    self.description = None
    self.cathegory = None
    self.lat = None
    self.lon = None
    self.GLSResult = None # optional


if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
