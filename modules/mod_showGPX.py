#!/usr/bin/python
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
from base_module import ranaModule
#from upoints import gpx
#import random
import geo
import math
from time import clock

def getModule(m,d):
  return(showGPX(m,d))

class showGPX(ranaModule):
  """draws a GPX track on the map"""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.linewidth = 7 #with of the line denoting GPX tracks

  def drawMapOverlay(self, cr):
    """get a file, load it and display it on the map"""
    proj = self.m.get('projection', None)
    if(proj == None):
      return
    if(not proj.isValid()):
      return

#    mapDt = self.m.get('mapData', None) # get the mapdata module
#    tilesToDownload = mapDt.currentTilesToGet

#    if tilesToDownload != None and self.get('debugSquares', False) == True:
#      cr.set_source_rgb(0,0, 0.5)
#      cr.set_line_width(self.linewidth)
#      for tile in tilesToDownload:
#        (lat,lon) = proj.num2deg(tile[0],tile[1])
#        (x,y) = proj.ll2xy(lat, lon)
#        #print (tile[0],tile[1])
#        #print proj.num2deg(x,y)
#        #self.point(cr, x, y)
#        if (15 - proj.zoom) > 0:
#          size = 256/2**(15 - proj.zoom)
#        else:
#          size = 256 * (2**(proj.zoom - 15))
#        #print size
#        self.boxFromULCorner(cr, x, y, size)
#        cr.stroke()
#        cr.fill()
#      cr.stroke()
#      cr.fill()
#    print proj.zoom

#    testRadius = 5 # 5 km
#    """ Znojmo cooridnates """
#    testLat = 48.855556
#    testLon = 16.048889
#    (px1,py1,px2,py2) = (proj.radiusEdges(testLat, testLon, testRadius))

#    self.point(cr, px1, py1)
#    self.point(cr, px2, py2)
#    cr.stroke()
#    cr.fill()

    visibleTracklogs = self.get('visibleTracklogs', set())
    loadTl = self.m.get('loadTracklogs', None) # get the tracklog module
    loadedTracklogs = loadTl.tracklogs # get list of all loaded tracklogs

    # find what tracklogs are not loaded and load them
    notLoaded = filter(lambda x: x not in loadedTracklogs.keys(), visibleTracklogs)
    if notLoaded:
      # remove possible nonexitant tracks from the not loaded tracks
      self.removeNonexistentTracks(notLoaded)
      # load the existing not loaded tracks
      loadTl.loadPathList(notLoaded)

    for path in visibleTracklogs:
      GPXTracklog = loadedTracklogs[path]
      if self.get('showTracklog', None) == 'simple':
        self.drawSimpleTrack(cr, GPXTracklog)

      elif self.get('showTracklog', None) == 'colored':
        self.drawColoredTracklog(cr, GPXTracklog)

      if self.get('debugCircles', None) == True:
        self.drawDebugCircles(cr, GPXTracklog)

      if self.get('debugSquares', None) == True:
        self.drawDebugSquares(cr, GPXTracklog)

  def removeNonexistentTracks(self, tracks):
    """remove tracks that dont exist,
       both from "tracks" and the persistent list,
       then return the tracks that do exist """
    loadTl = self.m.get('loadTracklogs', None) # get the tracklog module
    if loadTl:
      # do we know which tracks exist ?
      if loadTl.tracklogPathList == None:
        # look what tracklogs are available
        loadTl.listAvailableTracklogs()
      # look which files exist and which dont
      nonexistent = filter(lambda x: x not in loadTl.tracklogPathList, tracks)
      # remove nonexistent treacks:
      
      # from the persistent list
      visibleTracklogs = self.get('visibleTracklogs', set())
      visibleTracklogs = filter(lambda x: x not in nonexistent, visibleTracklogs)
      self.set('visibleTracklogs', visibleTracklogs)

      # from the input list
      tracks = filter(lambda x: x not in nonexistent, tracks)

      # return the existing tracks
      return tracks





  def point(self, cr, x, y):
    s = 10 #default 2
    cr.rectangle(x-s,y-s,2*s,2*s)

  def boxFromULCorner(self, cr, x, y, side):
    cr.rectangle(x, y, side, side)

  def simplePythagoreanDistance(self, x1,y1,x2,y2):
        dx = x2 - x1
        dy = y2 - y1
        return math.sqrt(dx**2 + dy**2)

  def drawSimpleTrack(self, cr, GPXTracklog):
#    pointsDrawn = 0
#    start = clock()
    proj = self.m.get('projection', None)
    (screenCentreX,screenCentreY,screenRadius) = proj.screenRadius()
    cr.set_source_rgb(0,0, 0.5)
    cr.set_line_width(self.linewidth)
    numberOfClusters = len(GPXTracklog.clusters) # how many clusters do we have in this tracklog ?
    for cluster in GPXTracklog.clusters: # we draw all clusters in tracklog

      """do we see this cluster ?"""
      clusterCentreX = cluster.centreX
      clusterCentreY = cluster.centreY
      clusterRadius = cluster.radius
      screenToClusterDistance = geo.distance(screenCentreX, screenCentreY, clusterCentreX, clusterCentreY)
      if (screenToClusterDistance - (screenRadius + clusterRadius)) >= 0:
        continue # we dont see this cluster se we skip it
      clusterNr = GPXTracklog.clusters.index(cluster)
      #print "Cluster nr %d" % clusterNr
      """now we need to draw lines to connect neighboring clusters"""
      prevClusterNr = clusterNr - 1
      nextClusterNr = clusterNr + 1
      if prevClusterNr >=0: # the 0th cluster has no previous cluster
        prevCluster = GPXTracklog.clusters[prevClusterNr]
        thisClusterLen = len(cluster.pointsList)
        prevClusterFirstPoint = prevCluster.pointsList[0]
        thisClusterLastPoint = cluster.pointsList[thisClusterLen - 1]
        (x1,y1) = proj.ll2xy(thisClusterLastPoint['latitude'], thisClusterLastPoint['longitude'])
        (x2,y2) = proj.ll2xy(prevClusterFirstPoint['latitude'], prevClusterFirstPoint['longitude'])
        self.drawLineSegment(cr, x1, y1, x2, y2) # now we connect the two clusters
        #self.point(cr, x1, y1)
        #self.point(cr, x2, y2)

      if nextClusterNr <= (numberOfClusters - 1): # the last cluster has no next cluster
        nextCluster = GPXTracklog.clusters[nextClusterNr]
        nextClusterLen = len(nextCluster.pointsList)
        nextClusterLastPoint = nextCluster.pointsList[nextClusterLen - 1]
        thisClusterFirstPoint = cluster.pointsList[0]
        (x1,y1) = proj.ll2xy(thisClusterFirstPoint['latitude'], thisClusterFirstPoint['longitude'])
        (x2,y2) = proj.ll2xy(nextClusterLastPoint['latitude'], nextClusterLastPoint['longitude'])
        self.drawLineSegment(cr, x1, y1, x2, y2) # now we connect the two clusters
        #self.point(cr, x1, y1)
        #self.point(cr, x2, y2)

      # get a list of onscreen coordinates
#      points = map(lambda x: proj.ll2xy(x['latitude'], x['longitude']), cluster.pointsList)
      points = [proj.ll2xy(x['latitude'], x['longitude']) for x in cluster.pointsList]
      # draw these coordinates
      (x,y) = points[0]
      cr.move_to(x,y) # go the the first point
      [cr.line_to(x[0],x[1])for x in points[1:]] # extend the line over the other points in the cluster

    cr.stroke()
    cr.fill()

  #    if pointsDrawn > 0:
  #    print "Nr of trackpoints drawn: %d" % pointsDrawn
  #    print "Redraw took %1.2f ms" % (1000 * (clock() - start))


  def drawColoredTracklog(self, cr, GPXTracklog):
    # show color depending on height
    if GPXTracklog.elevation == False: # we cant draw clored tracklog withou elevation data
      self.drawSimpleTrack(cr, GPXTracklog)
      return
    proj = self.m.get('projection', None)
    cr.set_source_rgb(0,0, 0.5)
    cr.set_line_width(self.linewidth)
    first = True
    last_x = 0
    last_y = 0

    currentRouteInfo = GPXTracklog.routeInfo # we load dictionary with route info
    max_elev = currentRouteInfo['maxElevation']
    min_elev = currentRouteInfo['minElevation']
    difference = max_elev - min_elev
    middle = min_elev + (difference/2.0)
    first = currentRouteInfo['firstElevation']
    last = currentRouteInfo['lastElevation']

    for point in GPXTracklog.trackpointsList[0]:
      (lat,lon) = (point.latitude, point.longitude)
      (x,y) = proj.ll2xy(lat,lon) # point on the map to screen coordinates
      #print("first point:%s m ,last point:%s m , max:%s m min:%s m") % (first_point.elevation, last_point.elevation, max_elev_point.elevation, min_elev_point.elevation)
      if first:
        #cr.move_to(x,y)
        last_x = x
        lasty_y = y
        first = False
      else:
        #a single color thicker line under the colored line (to make it more readable)
        #TODO: optimize this
        cr.set_line_width(self.linewidth + 5)
        cr.set_source_rgb(0.7 , 0.7, 0.7)
        cr.move_to(last_x,lasty_y)
        cr.line_to(x,y)
        cr.stroke()
        cr.fill()

        cr.set_line_width(self.linewidth)
        current_elevation = float(point.elevation)
        """the maximum height is solid red, that is 1,0,0 in RGB,
        the mid-heght is 0,0,1 and the minimum height is 0,1,0
        we use the folowing functions to get apropriate numbers for coloring"""
        # max color goes from 1 at max to 0 at the middle and after
        max_color = self.getNat(((current_elevation - difference)/(min_elev/2)) - 1)
        # is 1 in the middle, goes to 0 both to max and min
        middle_color = ( 1 - abs(middle - current_elevation)/(difference/2) )
        # max color goes from 1 at min to 0 at the middle and after
        min_color = self.getNat(1 - (current_elevation - difference)/(min_elev/2))
        cr.set_source_rgb(max_color , min_color, middle_color)
        cr.move_to(last_x,lasty_y)
        cr.line_to(x,y)
        cr.stroke()
        cr.fill()
        last_x = x
        last_y = y

  def drawDebugCircles(self, cr, GPXTracklog):
    proj = self.m.get('projection', None)
    for cluster in GPXTracklog.clusters:
      radius = proj.km2px(cluster.radius)
      (x,y) = proj.ll2xy(cluster.centreX,cluster.centreY)
      cr.arc(x, y, radius, 0, 2.0 * math.pi)
      cr.set_source_rgb(0, 0, 0)
      cr.stroke()
      cr.fill()

  def drawDebugSquares(self, cr, GPXTracklog):
    proj = self.m.get('projection', None)
    points = GPXTracklog.perElevList

    for point in points:
      (lat,lon) = point[2:4]
      (x,y) = proj.ll2xy(lat, lon)
      cr.move_to(x,y)
      self.point(cr, x, y)
      cr.stroke()

    cr.fill()

  def drawLineSegment(self, cr, x1, y1, x2, y2):
    cr.move_to(x1,y1)
    cr.line_to(x2,y2)
    cr.stroke()
    cr.fill()

  def getNat(self, x):
    """return number if positive, return 0 if negative; 0 is positive"""
    if x < 0:
      return 0
    else:
      return x

  def update(self):
    # Get and set functions are used to access global data
    self.set('num_updates', self.get('num_updates', 0) + 1)
    #print "Updated %d times" % (self.get('num_updates'))

  def handleMessage(self, message):
    if message == "toggleVisible":
      loadTl = self.m.get('loadTracklogs', None)
      if loadTl == None:
        return
      path = loadTl.getActiveTracklogPath()
      visibleTracklogs = self.get('visibleTracklogs', set())
      if path in visibleTracklogs:
        visibleTracklogs.remove(path)
      else:
        visibleTracklogs.add(path)
      self.set('visibleTracklogs', visibleTracklogs)
      self.set('showTracklog', 'simple')

    elif message == 'allVisible':
      loadTl = self.m.get('loadTracklogs', None)
      if loadTl == None:
        return
      paths = [x['path'] for x in loadTl.tracklogList]
      self.set('visibleTracklogs', set(paths))
      self.set('showTracklog', 'simple')
      
    elif message == 'inVisible':
      self.set('visibleTracklogs', set())
      self.set('showTracklog', None)

if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
