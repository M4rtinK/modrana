#!/usr/bin/python
#----------------------------------------------------------------------------
# Library for handling OpenStreetMap data
#
# Optimised for use in the pyrender system
#
# Handles:
#   * Interesting nodes, with tags (store as list)
#   * Ways, with tags (store as list)
#   * Position of all nodes (store as hash)
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
import sys
import os
from xml.sax import make_parser, handler
import xml

class parseOsm(handler.ContentHandler):
  def __init__(self, filename):
    """Load an OSM XML file into memory"""
    self.nodes = {}
    self.ways = {}
    self.poi = []
    self.divisor = float(2 ** 31)
    if(filename != None):
      self.loadOsm(filename)

  def loadOsm(self, filename):
    """Load an OSM XML file into memory"""
    if(not os.path.exists(filename)):
      return
    try:
      parser = make_parser()
      parser.setContentHandler(self)
      parser.parse(filename)
    except xml.sax._exceptions.SAXParseException:
      print "Error loading %s" % filename
    

  def startElement(self, name, attrs):
    """Handle XML elements"""
    if name in('node','way','relation'):
      self.tags = {}
      self.isInteresting = False
      self.waynodes = []
      if name == 'node':
        """Nodes need to be stored"""
        id = int(attrs.get('id'))
        self.nodeID = id
        lat = float(attrs.get('lat'))
        lon = float(attrs.get('lon'))
        self.nodes[id] = (lat,lon)
      elif name == 'way':
        id = int(attrs.get('id'))
        self.wayID = id
    elif name == 'nd':
      """Nodes within a way -- add them to a list"""
      node = {
        'id': int(attrs.get('id')),
        'lat': float(attrs.get('y')) / self.divisor, 
        'lon': float(attrs.get('x')) / self.divisor}
      self.waynodes.append(node)
    elif name == 'tag':
      """Tags - store them in a hash"""
      k,v = (attrs.get('k'), attrs.get('v'))
      
      # Test if a tag is interesting enough to make it worth
      # storing this node as a special "point of interest"
      if not k in ('created_by'): # TODO: better list of useless tags
        self.tags[k] = v
        self.isInteresting = True
  
  def endElement(self, name):
    if name == 'way':
      self.ways[self.wayID] = ({'t':self.tags, 'n':self.waynodes})
    elif name == 'node':
      if(self.isInteresting):
        self.poi.append({'t':self.tags, 'id':self.nodeID})

