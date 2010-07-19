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
import os
import cPickle
#import marshal
from time import clock
from time import gmtime, strftime
#from time import clock

def getModule(m,d):
  return(loadTracklogs(m,d))

class loadTracklogs(ranaModule):
  """A sample pyroute module"""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.tracklogs = {} # dictionary of all loaded tracklogs, path is the key
    #self.set('tracklogs', self.tracklogs) # now we make the list easily acessible to other modules
    self.cachePath = 'cache/tracklogs/tracklog_cache.txt'
    self.cache = {}
    self.tracklogFolder = 'tracklogs/'
    self.tracklogList = None
    self.tracklogPathList = None
    self.tracklogFilenameList = None

  def firstTime(self):
    folder = self.get('tracklogFolder', 'tracklogs/')

    if folder != None:
      self.tracklogFolder = folder
    else:
      self.tracklogFolder = 'tracklogs/'

#    self.load()

  def handleMessage(self, message):
    if message == 'loadActive':
      # load the active tracklog
      index = int(self.get('activeTracklog', None))
      if index != None and self.tracklogList:
        activeTracklog = self.tracklogList[index]
        filename = activeTracklog['filename']
        path = activeTracklog['path']
        print "loading tracklog: %s" % filename

        # Zeroeth, is the tracklog already loaded ?
        if path not in self.tracklogs.keys():
          # First, is the cache loaded ?
          if self.cache == {}:
            self.loadCache()
          else:
            print "not loading cache (already loaded)"
          # Second, try to load the tracklog (if its not loaded)

          try:
            self.loadTracklog(path)
            print "tracklog successfully loaded"
          except:
            print "loading tracklog failed: %s" % path

          # Third, assure consistency of the cache
          print "assuring cache consistency"
          self.save()
          self.cleanCache()
          print "cache consistency assured"


  def update(self):
    # Get and set functions are used to access global data
    self.set('num_updates', self.get('num_updates', 0) + 1)
    #print "Updated %d times" % (self.get('num_updates'))

  def loadCache(self):
    # unpickle the cache from file
    print "loading cache"
    start = clock()
    try:
      f = open(self.cachePath, 'r')
      self.cache = cPickle.load(f)
    except:
      print "loadTracklogs: loading cache from file failed"
      self.cache = {}
    print "Loading cache took %1.2f ms" % (1000 * (clock() - start))

  def cleanCache(self):
    """remove files that are not present from the cache"""
    paths = [x['path'] for x in self.tracklogList]
    garbage = filter(lambda x: x not in paths, self.cache)
    print garbage

    for g in garbage:
      del self.cache[g]

  def deleteTrackFromCache(self, file):
    # self explanatory
    del self.cache[file]

#  def getActiveTracklog(self):
#    index = int(self.get('activeTracklog', 0))
#    self.getTracklogForIndex(index)
#
#  def getTracklogForIndex(self,index):
#    path = self.tracklogList[index]['path']
##    print self.tracklogs
#    print path
##    print self.tracklogs[path]
#    tracklog = self.tracklogs[path]
#    return tracklog

  def getIndexForPath(self,path):
    """get index for the tracklog with corresponding path
       from the main tracklog lists"""
       
    return self.tracklogPathList.index(path)


  def getActiveTracklogPath(self):
    index = int(self.get('activeTracklog', 0))
    path = self.tracklogList[index]['path']
    return path

  def setTracklogPathCathegory(self,path,cathegory):
    catData = self.get('tracklogPathCathegory', {})
    catData[path] = cathegory
    # update the persistent list
    self.set('tracklogPathCathegory', catData)

    index = self.getIndexForPath(path)
    # update the current in memmory list
    self.tracklogList[index]['cat'] = cathegory

  def listAvailableTracklogs(self):
    print "** making a list of available tracklogs"
    files = []
    if os.path.exists(self.tracklogFolder):
      files = os.listdir(self.tracklogFolder)
      files = filter(lambda x: x != '.svn', files)
      catData = self.get('tracklogPathCathegory', {})
      newFiles = []
      pathList = []
      for file in files:
        path = self.tracklogFolder + file
        filename = file
        lastModifiedEpochSecs = os.path.getmtime(path)
        lastModified = strftime("%d.%m.%Y %H:%M:%S",gmtime(lastModifiedEpochSecs))
        size = self.convertBytes(os.path.getsize(path))
        splitFilename = filename.split('.')
        extension = ""
        if len(splitFilename)>=2:
          extension = splitFilename[-1]

        if path in catData:
          cat = catData[path]
        else:
          catData[path] = 'misc'
          cat = 'misc'

        item={'path':path,
              'filename':filename,
              'lastModified':lastModified,
              'size':size,
              'type':extension,
              'index':files.index(file),
              'cat':cat
               }
        newFiles.append(item)
        pathList.append(path)

      print "*  using this tracklog folder:"
      print self.tracklogFolder
      print "*  does it exist ?"
      print os.path.exists(self.tracklogFolder)
      print "*  there are %d tracklogs available" % len(files)
      self.tracklogFilenameList = files
      self.tracklogPathList = pathList
      self.tracklogList = newFiles
      self.set('tracklogPathCathegory', catData)

  # from:
  # http://www.5dollarwhitebox.org/drupal/node/84
  def convertBytes(self, bytes):
      bytes = float(bytes)
      if bytes >= 1099511627776:
          terabytes = bytes / 1099511627776
          size = '%.2fTB' % terabytes
      elif bytes >= 1073741824:
          gigabytes = bytes / 1073741824
          size = '%.2fGB' % gigabytes
      elif bytes >= 1048576:
          megabytes = bytes / 1048576
          size = '%.2fMB' % megabytes
      elif bytes >= 1024:
          kilobytes = bytes / 1024
          size = '%.2fKB' % kilobytes
      else:
          size = '%.2fb' % bytes
      return size

#  def load(self):
#    start = clock()
#
#    try:
#      f = open(self.cachePath, 'r')
#      cache = cPickle.load(f)
#
#      self.cache = cache
#    except:
#      print "loadTracklogs: loading cache from file failed"
#      self.cache = {}
#
#    print "Loading from cache took %1.2f ms" % (1000 * (clock() - start))
#
#    files = []
#    if os.path.exists(self.tracklogFolder):
#      files = os.listdir(self.tracklogFolder)
#      files = filter(lambda x: x != '.svn', files)
#
#
#      print self.tracklogFolder
#      print os.path.exists(self.tracklogFolder)
#      for file in files:
#        try:
#          self.loadTracklog(self.tracklogFolder + file)
#        except:
#          "loading tracklog failed: %s" % file
#
#    self.cleanCache(files)
#    self.save()
#    print "Loading tracklogs took %1.2f ms" % (1000 * (clock() - start))

  def save(self):
    try:
      f = open(self.cachePath, 'w')
      cPickle.dump(self.cache, f)
      f.close()
    except:
      print "loadTracklogs: cant store tracklog data to cache, tracklogs wil be loaded from files next time"

#  def saveClusters(self, clusters):

  def loadPathList(self, pathList):
    print "loading path list"
    start = clock()
    count = len(pathList)
    index = 1
    self.sendMessage('notification:loading %d tracklogs#1' % count)
    for path in pathList:
      self.loadTracklog(path, False)
      self.sendMessage('notification:%d of %d loaded#1' % (index, count))
      index = index + 1

    elapsed = (1000 * (clock() - start))
    print "Loading tracklogs took %1.2f ms" % elapsed
    self.save()
    self.cleanCache()
    self.sendMessage('notification:%d tracks loaded in %1.2f ms#1' % (count, elapsed) )


  def loadTracklog(self, path, notify=True):
    """load a GPX file to datastructure"""
    if self.cache == {}:
      self.loadCache()
    if self.tracklogList == None:
      self.listAvailableTracklogs()
    start = clock()
    self.filename = path
    file = open(path, 'r')

    if notify:
      self.sendMessage('notification:loading %s#1' % path)

    if(file): # TODO: add handling of other than GPX files
      track = gpx.Trackpoints() # create new Trackpoints object
      track.import_locations(file) # load a gpx file into it
      file.close()
      self.tracklogs[path] = (GPXTracklog(track, path, self.cache, self.save))

    else:
      print "No file"

    print "Loading %s took %1.2f ms" % (path,(1000 * (clock() - start)))
    if notify:
      self.sendMessage('notification:loaded in %1.2f ms' % (1000 * (clock() - start)))

  def storeRoute(self, route, name=""):
    """store a route, found by Google Directions to a GPX file, then load this file to tracklogs list"""
    newTracklog = gpx.Trackpoints()
    trackpoints = map(lambda x: gpx.Trackpoint(x[0],x[1]), route)
    newTracklog.append(trackpoints)
    xmlTree = newTracklog.export_gpx_file()

    timeString = strftime("%Y%m%d#%H-%M-%S", gmtime())
    folder = self.tracklogFolder
    # gdr = Google Directions Result, TODO: alternate prefixes when we have more routing providers
    name = name.encode('ascii', 'ignore')
    path = "" + folder + "gdr_" + name + timeString + ".gpx"
    f = open(path, 'w') # TODO: handle the exception that occurs when there is not tracklog folder :)
    xmlTree.write(f)
    f.close()
    
    self.setTracklogPathCathegory(path, 'online')
    self.listAvailableTracklogs()
    index = self.tracklogPathList.index(path)
    self.set('activeTracklog', index)
    # TODO: incremental addition of new tracklogs



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
  def __init__(self, trackpointsList, tracklogFilename, cache, save):
    tracklog.__init__(self, trackpointsList, tracklogFilename)
    tracklog.tracklogType = 'gpx'
    self.routeInfo = None # a dictionary for storing route information
    # TODO: set this automaticaly

    filename = self.tracklogFilename

    self.cache = cache
    self.save = save

    self.elevation = None

    self.perElevList = None

    if filename in cache:
      print "loading from cache"
      self.clusters = cache[filename].clusters
      self.routeInfo = cache[filename].routeInfo
      if self.routeInfo != None:
        self.elevation = True
      self.perElevList = cache[filename].perElevList
      
    else:
      print "creating clusters,routeInfo and perElevList: %s" % filename
      clusterDistance = 5 # cluster points to clusters about 5 kilometers in diameter
      self.clusters = []

      rawClusters = geo.clusterTrackpoints(trackpointsList, clusterDistance) # we cluster the points
      for cluster in rawClusters: # now we find for each cluster a circle encompasing all points
        (centreX,centreY,radius) = geo.circleAroundPointCluster(cluster)
        self.clusters.append(clusterOfPoints(cluster, centreX, centreY, radius))

      self.checkElevation()

      if self.elevation == True:
        self.getPerElev()
      else:
        self.perElevList = None

      ci = CacheItem(self.clusters, self.routeInfo, self.perElevList)
      cache[filename] = ci
      

#    self.checkElevation()
#
#    if self.elevation == True:
#      self.getPerElev()


  def modified(self):
    """the tracklog has been modified, recount all the statistics and clusters"""
    # TODO: implement this ? :D
    self.checkElevation() # update the elevation statistics
    if self.elevation == True:
      self.getPerElev() # update the periodic elevation data

  def checkElevation(self):
    pointsWithElevation = filter(lambda x: x.elevation != None, self.trackpointsList[0])
    if pointsWithElevation: # do we have some points with known elevation ?
      self.elevation = True
      self.routeInfo = {}
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
#      self.routeInfo['firstPoint'] = firstPoint
#      self.routeInfo['lastPoint'] = lastPoint
#      self.routeInfo['maxElevationPoint'] = maxElevationPoint
#      self.routeInfo['minElevationPoint'] = minElevationPoint
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
    print "%s has been replaced by the current in memory version" % self.tracklogFilename
    del self.cache[self.tracklogFilename] # the file has been modified, so it must be cached again
    self.save() # save the cache to disk


  def getPerElev(self):
    self.perElevList = geo.perElevList(self.trackpointsList)



class CacheItem():
  """class representing a cache item"""
  def __init__(self, clusters, routeInfo=None, perElevList=None):
    self.clusters = clusters
    self.routeInfo = routeInfo
    self.perElevList = perElevList

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
