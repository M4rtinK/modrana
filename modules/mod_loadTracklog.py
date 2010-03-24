#!/usr/bin/python
#----------------------------------------------------------------------------
# Sample of a Rana module.
#----------------------------------------------------------------------------
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
#---------------------------------------------------------------------------
#from dbus.service import Object
from base_module import ranaModule
from upoints import gpx
import geo
#from time import clock

def getModule(m,d):
  return(loadTracklog(m,d))

class loadTracklog(ranaModule):
  """A sample pyroute module"""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.tracklogs = [] # this list will store the object representing tracklists
    #self.set('tracklogs', self.tracklogs) # now we make the list easily acessible to other modules
    
  def update(self):
    # Get and set functions are used to access global data
    self.set('num_updates', self.get('num_updates', 0) + 1)
    #print "Updated %d times" % (self.get('num_updates'))

  def load(self, filename):
    """load a GPX file to datastructure"""
    self.filename = filename
    file = open(filename, 'r')

    if(file): # TODO: add handling of other than GPX files
      track = gpx.Trackpoints() # create new Trackpoints object
      track.import_locations(file) # load a gpx file into it
      file.close()
      self.tracklogs.append(GPXTracklog(track, filename))

#      # TODO: testing code, remove this
#      cluster_distance = 5
#      cl = self.clusterTrackpoints(track, cluster_distance)
#      self.set("tempClusters", cl)

    else:
      print "No file"

  def simplePythagoreanDistance(self, x1,y1,x2,y2):
      dx = x2 - x1
      dy = y2 - y1
      return math.sqrt(dx**2 + dy**2)

#  def adjustAproximateCircle(self, points, radius):
#    """test wheter all points are inside the preliminary circle,
#    if not, adjust the radius acordingly"""
##    for point in points:

  # found on:
  # http://www.quanative.com/2010/01/01/server-side-marker-clustering-for-google-maps-with-python/
  def clusterTrackpoints(self, trackpointsList , cluster_distance):
    """
    Groups points that are less than cluster_distance pixels apart at
    a given zoom level into a cluster.
    """
    points = [{'latitude': point.latitude,'longitude': point.longitude} for point in trackpointsList[0]]
    self.set('clPoints', points)
    clusters = []
    while len(points) > 0:
        point1 = points.pop()
        cluster = []
        for point2 in points[:]:

            pixel_distance = geo.distance(point1['latitude'],
                                           point1['longitude'],
                                            point2['latitude'],
                                           point2['longitude'])

            if pixel_distance < cluster_distance:
                points.remove(point2)
                cluster.append(point2)

        # add the first point to the cluster
        if len(cluster) > 0:
            cluster.append(point1)
            clusters.append(cluster)
        else:
            clusters.append([point1])

    return clusters



class tracklog():
  """A basic class representing a tracklog."""
  def __init__(self, trackpointsList, tracklogFilename):
    self.trackpointsList = trackpointsList # here will be the actual list of trackpoints
    self.tracklogFilename = tracklogFilename # the filename as used when loading the list from file
    self.tracklogType = None
    """
  tracklog types: (for now)
  'gpx'= a GPX tracklog
  'kml'= a KML tracklog
  'nmea' = a NMEA log file
  """
    self.tracklogName = tracklogFilename # custom name for the tracklog, by default the filename
    self.tracklogDescription = "" # description of the tracklog

  def getTracklogFilename(self):
    return self.tracklogFilename

  def getTracklogName(self):
    """returns tracklog name"""
    return self.tracklogName

  def setTracklogName(name):
    """sets tracklog name"""
    self.tracklogName = name

  def getTracklogDescription(self):
    """returns tracklog description"""
    return self.tracklogDescription

  def setTracklogDescription(description):
    """sets tracklog description"""
    self.tracklogDescription = description

class GPXTracklog(tracklog):
  """A class representing a GPX tracklog."""
  def __init__(self, trackpointsList, tracklogFilename):
    tracklog.__init__(self, trackpointsList, tracklogFilename)
    tracklog.tracklogType = 'gpx'
    self.routeInfo = {} # a dictionary for storing route information
    # TODO: set this automaticaly
    clusterDistance = 5 # cluster points to clusters about 5 kilometers in diameter
    self.clusters = []

    rawClusters = geo.clusterTrackpoints(trackpointsList, clusterDistance) # we cluster the points
    for cluster in rawClusters: # now we find for erach cluster a circle encompasing all points
      (centreX,centreY,radius) = geo.circleAroundPointCluster(cluster)
      self.clusters.append(clusterOfPoints(cluster, centreX, centreY, radius))

    self.checkElevation()

  def checkElevation(self):
    pointsWithElevation = filter(lambda x: x.elevation != None, self.trackpointsList[0])
    if pointsWithElevation: # do we have some points with known elevation ?
      self.elevation = True
      # there we have the poinsts, that contain the highest, lowest, first and last point
      firstPoint = pointsWithElevation[0]
      lastPoint = pointsWithElevation[len(pointsWithElevation)-1]
      # now we use some lambdas, to find the lowest and highest point
      maxElevationPoint = (max(pointsWithElevation, key=lambda x: x.elevation))
      minElevationPoint = (min(pointsWithElevation, key=lambda x: x.elevation))
      # just the highest/lowest elevations in numerical form
      maxElevation = float(maxElevationPoint.elevation)
      minElevation = float(minElevationPoint.elevation)
      difference = maxElevation - minElevation
      middle = minElevation + (difference/2)
      firstElevation = float(firstPoint.elevation)
      lastElevation = float(lastPoint.elevation)
      """because there are many possible statiastics about a given route with elevation,
      we will store them in a disctionary, so new onec can be quickly added as needed"""
      self.routeInfo['firstPoint'] = firstPoint
      self.routeInfo['lastPoint'] = lastPoint
      self.routeInfo['maxElevationPoint'] = maxElevationPoint
      self.routeInfo['minElevationPoint'] = minElevationPoint
      self.routeInfo['maxElevation'] = maxElevation
      self.routeInfo['minElevation'] = minElevation
      self.routeInfo['middle'] = middle
      self.routeInfo['firstElevation'] = firstElevation
      self.routeInfo['lastElevation'] = lastElevation
    else:
      self.elevation = False

  def replaceFile(self):
    """
    we output the tree structure of the gpx xml back to the file
    this can also meen, that some info that we didnt load to the tree will be lost
    also atributes that were changed after the initial load will be written in the current (changed) state
    """
    f = open(self.tracklogFilename, "w") # open the old file
    xmlTree = self.trackpointsList.export_gpx_file() # get the element tree
    xmlTree.write(f) # overwrite the old file with the new structure
    print "%s has been replaced by current in memory version" % self.tracklogFilename


class clusterOfPoints():
  """A basic class representing a cluster of nearby points."""
  def __init__(self, pointsList, centreX, centreY, radius):
    self.pointsList = pointsList # points in the cluster
    """coordinates of the circle encompasing all points"""
    self.centreX = centreX
    self.centreY = centreY
    self.radius = radius #radius of the circle


if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
