#!/usr/bin/python
#----------------------------------------------------------------
# load OSM data file into memory
#
#------------------------------------------------------
# Copyright 2007, Oliver White
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
#------------------------------------------------------
# Changelog:
#  2007-11-04  OJW  Modified from pyroute.py
#  2007-11-05  OJW  Multiple forms of transport
#------------------------------------------------------
import sys
import os
import tiledata
import tilenames
import re
import weights

class LoadOsm:
  """Parse an OSM file looking for routing information, and do routing with it"""
  def __init__(self, transport):
    """Initialise an OSM-file parser"""
    self.routing = {}
    self.rnodes = {}
    self.transport = transport
    self.tiles = {}
    self.weights = weights.RoutingWeights()
  
  def getArea(self, lat, lon):
    """Download data in the vicinity of a lat/long"""
    
    z = tiledata.DownloadLevel()
    (x,y) = tilenames.tileXY(lat, lon, z)

    tileID = '%d,%d'%(x,y)
    if(self.tiles.get(tileID,False)):
      #print "Already got %s" % tileID
      return
    self.tiles[tileID] = True
    
    filename = tiledata.GetOsmTileData(z,x,y)
    #print "Loading %d,%d at z%d from %s" % (x,y,z,filename)
    return(self.loadOsm(filename))

  def loadOsm(self, filename):
    if(not os.path.exists(filename)):
      print "No such data file %s" % filename
      return(False)
    fp = open(filename, "r")
    re_way = re.compile("<way id='(\d+)'>\s*$")
    re_nd = re.compile("\s+<nd id='(\d+)' x='(\d+)' y='(\d+)' />\s*$")
    re_tag = re.compile("\s+<tag k='(.*)' v='(.*)' />\s*$")
    re_endway = re.compile("</way>$")
    in_way = 0

    way_tags = {}
    way_nodes = []

    for line in fp:
      result_way = re_way.match(line)
      result_endway = re_endway.match(line)
      if(result_way):
        in_way = True
        way_tags = {}
        way_nodes = []
        way_id = int(result_way.group(1))
      elif(result_endway):
        in_way = False
        self.storeWay(way_id, way_tags, way_nodes)
      elif(in_way):
        result_nd = re_nd.match(line)
        if(result_nd):
          node_id = int(result_nd.group(1))
          x = float(result_nd.group(2))
          y = float(result_nd.group(3))

          (lat,lon) = tilenames.xy2latlon(x,y,31)
          
          way_nodes.append([node_id,lat,lon])
        else:
          result_tag = re_tag.match(line)
          if(result_tag):
            way_tags[result_tag.group(1)] = result_tag.group(2)
    return(True)
  
  def storeWay(self, wayID, tags, nodes):
    highway = self.equivalent(tags.get('highway', ''))
    railway = self.equivalent(tags.get('railway', ''))
    oneway = tags.get('oneway', '')
    reversible = not oneway in('yes','true','1')

    # Calculate what vehicles can use this route
    # TODO: just use getWeight != 0
    access = {}
    access['cycle'] = highway in ('primary','secondary','tertiary','unclassified','minor','cycleway','residential', 'track','service')
    access['car'] = highway in ('motorway','trunk','primary','secondary','tertiary','unclassified','minor','residential', 'service')
    access['train'] = railway in('rail','light_rail','subway')
    access['foot'] = access['cycle'] or highway in('footway','steps')
    access['horse'] = highway in ('track','unclassified','bridleway')

    # Store routing information
    last = [None,None,None]

    if(wayID == 41 and 0):
      print nodes
      sys.exit()
    for node in nodes:
      (node_id,x,y) = node
      if last[0]:
        if(access[self.transport]):
          weight = self.weights.get(self.transport, highway)
          self.addLink(last[0], node_id, weight)
          self.makeNodeRouteable(last)
          if reversible or self.transport == 'foot':
            self.addLink(node_id, last[0], weight)
            self.makeNodeRouteable(node)
      last = node

  def makeNodeRouteable(self,node):
    self.rnodes[node[0]] = [node[1],node[2]]
    
  def addLink(self,fr,to, weight=1):
    """Add a routeable edge to the scenario"""
    try:
      if to in self.routing[fr].keys():
        return
      self.routing[fr][to] = weight
    except KeyError:
      self.routing[fr] = {to: weight}

  def equivalent(self,tag):
    """Simplifies a bunch of tags to nearly-equivalent ones"""
    equivalent = { \
      "primary_link":"primary",
      "trunk":"primary",
      "trunk_link":"primary",
      "secondary_link":"secondary",
      "tertiary":"secondary",
      "tertiary_link":"secondary",
      "residential":"unclassified",
      "minor":"unclassified",
      "steps":"footway",
      "driveway":"service",
      "pedestrian":"footway",
      "bridleway":"cycleway",
      "track":"cycleway",
      "arcade":"footway",
      "canal":"river",
      "riverbank":"river",
      "lake":"river",
      "light_rail":"railway"
      }
    try:
      return(equivalent[tag])
    except KeyError:
      return(tag)
    
  def findNode(self,lat,lon):
    """Find the nearest node that can be the start of a route"""
    self.getArea(lat,lon)
    maxDist = 1E+20
    nodeFound = None
    posFound = None
    for (node_id,pos) in self.rnodes.items():
      dy = pos[0] - lat
      dx = pos[1] - lon
      dist = dx * dx + dy * dy
      if(dist < maxDist):
        maxDist = dist
        nodeFound = node_id
        posFound = pos
    #print "found at %s"%str(posFound)
    return(nodeFound)
      
  def report(self):
    """Display some info about the loaded data"""
    print "Loaded %d nodes" % len(self.rnodes.keys())
    print "Loaded %d %s routes" % (len(self.routing.keys()), self.transport)

# Parse the supplied OSM file
if __name__ == "__main__":
  data = LoadOsm("cycle")
  if(not data.getArea(52.55291,-1.81824)):
    print "Failed to get data"
  data.getArea(52.55291,-1.81824)
  data.report()

  print "Searching for node: found " + str(data.findNode(52.55291,-1.81824))
