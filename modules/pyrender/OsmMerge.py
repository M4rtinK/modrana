#!/usr/bin/python
#----------------------------------------------------------------------------
# Merge multiple OSM files (in memory) and save to another OSM file
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
import codecs
from parseOsm import *
from xml.sax.saxutils import quoteattr

def pixelSize(z):
  """length of x/y change that represents 1 pixel at a given zoom level"""
  return(1.0 / float(256 * pow(2,z)))

def OsmMerge(dest, z, sources):
  """Merge multiple OSM files together
  
  Usage: 
    OsmMerge('output_filename.osm', 
      ['input_file_1.osm', 
       'input_file_2.osm',
       'input_file_3.osm'])
  """
  
  ways = {}
  poi = []
  node_tags = {}
  nodes = {}
  
  divisor = float(2 ** 31)
  
  # Trawl through the source files, putting everything into memory
  for source in sources:
    osm = parseOsm(source)
    
    for p in osm.poi:
      node_tags[p['id']] = p['t']

    for id,n in osm.nodes.items():
      nodes[id] = n
    for id,w in osm.ways.items():
      ways[id] = w

  # Store the result as an OSM XML file
  f=codecs.open(dest, mode='w', encoding='utf-8')
  f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
  f.write('<osm version="0.5" generator="OsmMerge">\n')
  
  # TODO: Write the nodes
  if(0):
	  for n,data in nodes.items():
	    (lat,lon) = nodes[n]
	    f.write('<node id="%d" lat="%f" lon="%f">' % (n,lat,lon))
	    tags = node_tags.get(n, None)
	    if(tags):
	      for k,v in tags.items():
	        f.write('\n<tag k=%s v=%s/>' % (quoteattr(k),quoteattr(v)))
	    f.write("</node>\n")

  limit = pixelSize(z) * 2.0
  limitSq = limit * limit
  #print "Using limit %e" % limitSq
  
  # Detect 'junction' ways
  usage = {}
  junctions = {}
  countNodes = 0
  for wid,way in ways.items():
    for n in way['n']:
      nid = n['id']
      if(usage.get(nid,0) != 0):
        junctions[nid] = 1
      else:
        usage[nid] = 1
      countNodes = countNodes + 1

  #print "%d nodes, %d junctions" % (countNodes, len(junctions.keys()))

  countUsed = countNotUsed = 0
  # Write the ways
  for id,way in ways.items():
    f.write('<way id="%d">' % id)
    for k,v in way['t'].items():
      f.write('\n<tag k=%s v=%s/>' % (quoteattr(k),quoteattr(v)))

    (lastx,lasty,count) = (0,0,False)
    for n in way['n']:
      lat = n['lat']
      lon = n['lon']
      
      storeThisNode = False
      if(count == 0):
        storeThisNode = True  # Store 1st node
      elif(junctions.get(n['id'], 0) == 1):
        storeThisNode = True  # Store junction nodes
      else:
        dx = lon - lastx
        dy = lat - lasty
        dd = dx * dx + dy * dy
        if(dd > limitSq):
          storeThisNode = True  # Store ever x pixels
          
        #print "Dist2 = %f" % dd
        
      if(storeThisNode):
        (lastx,lasty,count) = (lon,lat,count+1)
      
        f.write("\n<nd id='%d' x='%1.0f' y='%1.0f'/>" % (n['id'], lon * divisor, lat * divisor))
        countUsed = countUsed + 1
      else:
        countNotUsed = countNotUsed + 1
    f.write("</way>\n")
  #print "Used %d, skipped %d" % (countUsed, countNotUsed)
  
  # TODO: Write the relations

  
  f.write("</osm>\n")
  f.close()

