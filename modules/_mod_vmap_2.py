## -*- coding: utf-8 -*-
##----------------------------------------------------------------------------
## Display map vectors
##----------------------------------------------------------------------------
## Copyright 2008, Oliver White
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##---------------------------------------------------------------------------
#from modules.base_module import ranaModule
#import cairo
#import os
#import sys
#import urllib
#import tilenames
#import vmap_load
#from math import *
#from time import time
#
#def getModule(m,d,i):
#  return vmap(m,d,i)
#
#class vmap(ranaModule):
#  """Display map vectors"""
#  def __init__(self, *args, **kwargs):
#    ranaModule.__init__(self, *args, **kwargs)
#    self.tiles = {}
#    self.style_d = 0
#    self.style_c = 0
#    self.lastColour = (-1,-1,-1)
#    self.lastWidth = -1
#    self.line_d = 0
#    self.line_c = 0
#
#  def firstTime(self):
#    self.loadEnums()
#    self.setupStyles()
#
#  def getTile(self,x,y,z):
#    # Use filename as dictionary key, so that zooms which happen to
#    # use the dataset don't get loaded twice
#    filename = vmap_load.getVmapFilename(x,y,z,self.d)
#    if not filename:
#      return None
#
#    # If it doesn't already exist, then load it
#    if not self.tiles.has_key(filename):
#      #print("Loading %s" % (filename))
#      self.tiles[filename] = vmap_load.vmapData(filename)
#
#    return self.tiles[filename]
#
#  def setupStyles(self):
#    self.highways = {
#      'motorway':     ((0.5, 0.5, 1.0), 6, {'shields':True}),
#      'trunk':        ((0.0, 0.8, 0.0), 6, {'shields':True}),
#      'primary':      ((0.8, 0.0, 0.0), 6, {'shields':True}),
#      'secondary':    ((0.8, 0.8, 0.0), 6, {'shields':True}),
#      'tertiary':     ((0.8, 0.8, 0.0), 6, {}),
#      'unclassified': ((1.0, 1.0, 1.0), 4, {}),
#      'service':      ((1.0, 1.0, 1.0), 2, {}),
#      'footway':      ((1.0, 0.5, 0.5), 2, {'dashed':True}),
#      'cycleway':     ((0.5, 1.0, 0.5), 2, {'dashed':True}),
#      'bridleway':    ((0.5, 1.0, 0.5), 2, {'dashed':True}),
#      }
#
#  def loadEnums(self):
#    try:
#      filename = "%s/enums.txt" % vmap_load.getVmapBaseDir(self.d)
#      f = open(filename, "r")
#      self.enums = {}
#      for line in f:
#        k,v = line.rstrip().split("\t")
#        k = int(k)
#        #print("%d = '%s'" % (k,v))
#        self.enums[k] = v
#    except IOError:
#      print("Couldn't find vector map data. Expected enum file in %s" % filename)
#      sys.exit(-1)
#
#
#  def setStyle(self, style, cr):
#    styleDef = self.highways.get(style, None)
#    start = time()
#    if not styleDef:
#      return False
#    (colour,width,options) = styleDef
#    width *= self.scale
#
#    if colour != self.lastColour:
#      (r,g,b) = colour
#      cr.set_source_rgb(r,g,b)
#      self.lastColour = colour
#
#    if width != self.lastWidth:
#      cr.set_line_width(width)
#      self.lastWidth = width
#
#    duration = time() - start
#    self.style_d += duration
#    self.style_c += 1
#    return True
#
#  def drawTile(self,cr,tx,ty,tz,proj,mapBounds):
#    start = time()
#    mapData = self.getTile(tx,ty,tz)
#    #print(" - Map data: %1.3fms" % ((time() - start) * 1000.0))
#
#    cWays = 0
#    cDone = 0
#    cNodes = 0
#    cOob = 0
#
#    (minLat,maxLat,minLon,maxLon) = mapBounds
#    #print(" - Map: %1.3f to %1.3f, %1.3f to %1.3f"%(minLat,maxLat,minLon,maxLon))
#
#    if mapData:
#      #print(mapData.ways)
#      for wayID, way in mapData.ways.items():
#        if not self.waysDrawn.get(wayID, False): # if not drawn already as part of another tile
#
#          (lon1,lon2,lat1,lat2) = way['bounds']
#
#          offMap = (lon2 < minLon
#            or lon1 > maxLon
#            or lat2 < minLat
#            or lat1 > maxLat)
#
#          #print("   - Way: %1.3f to %1.3f, %1.3f to   %1.3f - %s"%(lat1,lat2,lon1,lon2, text))
#
#          if offMap:
#            cOob += 1
#          else:
#            if self.setStyle(self.enums[way['style']], cr):
#              count = 0
#              cWays += 1
#              line_start = time()
#              for node in way['n']:
#                cNodes += 1
#                (lat,lon,nid) = node
#                x,y = proj.ll2xy(lat,lon)
#                if count == 0:
#                  cr.move_to(x,y)
#                else:
#                  cr.line_to(x,y)
#                count += 1
#              cr.stroke()
#              line_duration = time() - line_start
#              self.line_d += line_duration
#              self.line_c += 1
#
#          # Note: way['N'] and way['r'] are name and ref respectively
#          self.waysDrawn[wayID] = True
#        else:
#          cDone += 1
#    else:
#      print("No map data")
#
#    #if(tx == 16342 and ty == 10803):
#    #print(" - %d,%d,%d: %d ways, %d done, %d oob, %d nd, %1.3fms" % (tx,ty,tz, cWays, cDone, cOob, cNodes, 1000.0 * (time() - start)))
#
#  def drawMap(self, cr):
#    (sx,sy,sw,sh) = self.get('viewport')
#    proj = self.m.get('projection', None)
#    if not proj or not proj.isValid():
#      return
#
#    self.z = int(self.get('z', 15))
#
#    start = time()
#    count = 0
#
#    self.scale = self.get("scaleLines", 1.0)
#    if self.get("zoomLines", True) and self.z > 14:
#      self.scale *= self.z - 14
#
#    #x1,y1 = proj.pxpy2xy(proj.px1,proj.py2)
#    #y1,x1 = proj.xy2ll(x1,y1)
#    #x2,y2 = proj.pxpy2xy(proj.px2,proj.py1)
#    #y2,x2 = proj.xy2ll(x2,y2)
#    #print("%1.3f to %1.3f, %1.3f to %1.3f" % (x1,x2,y1,y2))
#    bounds = (proj.S,proj.N, proj.W,proj.E)
#    #print("%1.3f to %1.3f, %1.3f to %1.3f" % bounds)
#
#    # Render each 'tile' in view
#    self.waysDrawn = {}
#    for x in range(int(floor(proj.px1)), int(ceil(proj.px2))):
#      for y in range(int(floor(proj.py1)), int(ceil(proj.py2))):
#        self.drawTile(cr,x,y,self.z,proj,bounds)
#        count += 1
#
#    duration = time() - start
#    #print("Z%d %d tiles, %f seconds" % (self.z, count, duration))
#    #print("%f - %f" % (proj.px1, proj.px2))
#
#    if self.get("benchmarkLines"):
#      print("Style: %1.3fms, line %1.3fms" % (
#        1000.0 * self.style_d / self.style_c,
#        1000.0 * self.line_d / self.line_c))
#
#  def update(self):
#    pass
#
#if(__name__ == "__main__"):
#  a = vmap({},{"vmapTileDir":"../../tiledata3/output"})
#  a.loadEnums()