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
    self.filename = self.folder + 'poi.txt'
    self.points = []
#    self.points['GLS'] = []
    self.load()
    
  def update(self):
    pass
#    # Get and set functions are used to access global data
#    self.set('num_updates', self.get('num_updates', 0) + 1)
#    #print "Updated %d times" % (self.get('num_updates'))

  def load(self):
    """load POI from file"""
#    start = time.clock()
    try:
      f = open(self.filename, 'r')
      self.points = cPickle.load(f)
      f.close()
    except:
      print "storePOI: loding POI from file failed"
#    print "Loading POI took %1.2f ms" % (1000 * (time.clock() - start))
  def save(self):
    """save all poi in the main list to file"""
    try:
      f = open(self.filename, 'w')
      cPickle.dump(self.points, f)
      f.close()
    except:
      print "storePoi: saving POI to file failed"


  def storeGLSResult(self, result):
    name = result['titleNoFormatting']
    lat = float(result['lat'])
    lon = float(result['lng'])
    cathegory = "gls"

    newPOI = POI(name, cathegory, lat, lon)

    text = "%s" % (result['titleNoFormatting'])

    try: # the adress can be unknown
      for addressLine in result['addressLines']:
        text += "|%s" % addressLine
    except:
      text += "|%s" % "no adress found"

    try: # it seems, that this entry is no guarantied
      for phoneNumber in result['phoneNumbers']:
        type = ""
        if phoneNumber['type'] != "":
          type = " (%s)" % phoneNumber['type']
        text += "|%s%s" % (phoneNumber['number'], type)
    except:
      text += "|%s" % "no phone numbers found"

    newPOI.setDescription(text)
    
    self.points.append(newPOI)
    self.save()

class POI():
  """A basic class representing a POI."""
  def __init__(self, name, cathegory, lat, lon):
    self.name = name
    self.cathegory = cathegory
    self.description = ""
    self.lat = lat
    self.lon = lon

  def setDescription(self, description):
    self.description = description
#    self.GLSResult = None # optional


if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
