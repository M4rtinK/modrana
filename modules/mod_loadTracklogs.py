# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Sample of a Rana module.
# ----------------------------------------------------------------------------
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
# ---------------------------------------------------------------------------
from modules.base_module import RanaModule
from core import geo
from core import utils
import math
import os
import glob

try:
    import cPickle as pickle  # Python 2
except ImportError:
    import pickle  # Python 3
import shutil
from time import clock
from time import gmtime, strftime

import logging
gpx_log = logging.getLogger("core.loadTracklogs.gpx_tracklog")

def getModule(*args, **kwargs):
    return LoadTracklogs(*args, **kwargs)


class LoadTracklogs(RanaModule):
    """A sample pyroute module"""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self.tracklogs = {}  # dictionary of all loaded tracklogs, path is the key
        self.cache = {}
        self._tracklog_list = []
        self._tracklog_path_list = []
        self._category_list = []

    def firstTime(self):
        self._create_basic_folder_structure()

    def handleMessage(self, message, messageType, args):
        if message == 'loadActive':
            # load the active tracklog
            path = self.get('activeTracklogPath', None)
            if path is not None and self._tracklog_list:
                self.log.info("* loading tracklog:\n%s", path)

                # Zeroth, is the tracklog already loaded ?
                if path not in self.tracklogs.keys():
                    # First, is the cache loaded ?
                    if self.cache == {}:
                        self._load_cache()
                    else:
                        self.log.warning("not loading tracklog cache (already loaded)")
                        # Second, try to load the tracklog (if its not loaded)

                    try:
                        self.load_tracklog(path)
                        self.log.info("tracklog successfully loaded")
                    except Exception:
                        self.log.exception("loading tracklog from path: %s failed", path)

                    # Third, assure consistency of the cache
                    self.log.info("** Assuring tracklog cache consistency")
                    self.save()
                    self._clean_cache()
                    self.log.info("** Tracklog cache consistency assured")
                #    elif message == 'renameActiveTracklog':
                #      activeTracklog = self.get_active_tracklog()
                #      if activeTracklog:
                #        pass
                #        # get current tracklog filename, sans extension
                #        # start an entry box

    def _get_tf_sub_path(self, subPath):
        """Return a tracklog folder sub path.

        Also assure the patch exists before returning it.
        """
        tracklogFolderPath = self.modrana.paths.tracklog_folder_path
        if tracklogFolderPath is None:
            self.log.error("can't get tracklog sub path - tracklog folder path is unknown")
            return None  # tracklog folder path is unknown
        else:
            TFSubPath = os.path.join(tracklogFolderPath, subPath)
            utils.create_folder_path(TFSubPath)
            return TFSubPath

    def _create_basic_folder_structure(self):
        """Trigger creation of the logs, misc and online folders.

        Also copy example tracklogs, if necessary.
        """
        self._get_tf_sub_path("logs")
        self._get_tf_sub_path("online")
        self._get_tf_sub_path("misc")
        # if there is no example folder, create it
        # and copy example tracklogs into it
        tfp = self.modrana.paths.tracklog_folder_path
        examplesDestinationPath = os.path.join(tfp, 'examples')
        if not os.path.exists(examplesDestinationPath):
            utils.create_folder_path(examplesDestinationPath)
            self.log.info(' ** copying example tracklogs')
            try:
                examplesSourcePath = 'data/tracklog_examples'
                # copy all files from this folder
                for item in os.listdir(examplesSourcePath):
                    path = os.path.join(examplesSourcePath, item)
                    if os.path.isfile(path):
                        self.log.info(' ** copying: %r', item)
                        shutil.copy(path, os.path.join(examplesDestinationPath, item))
                self.log.info(' ** DONE')
            except Exception:
                self.log.exception("could not copy example tracklogs")

    # tracklog cache

    def _load_cache(self):
        """Unpickle the cache from file."""
        self.log.info("** Loading tracklog cache")
        start = clock()
        try:
            f = open(self.get_tracklog_cache_path(), 'rb')
            self.cache = pickle.load(f)
            f.close()
        except Exception:
            self.log.exception("loading cache from file failed")
            self.cache = {}
        self.log.info("** Loading tracklog cache took %1.2f ms", 1000 * (clock() - start))

    def _clean_cache(self):
        """Remove files that are not present from the cache."""
        paths = self._tracklog_path_list
        garbage = filter(lambda x: x not in paths, self.cache)
        for g in garbage:
            del self.cache[g]

    def delete_tracklog_from_cache(self, tracklogFile):
        """Self explanatory."""
        if tracklogFile in self.cache:
            del self.cache[tracklogFile]

    def get_tracklog_cache_path(self):
        return os.path.join(self.modrana.paths.cache_folder_path, 'tracklog_cache.txt')

    # active tracklog

    def get_active_tracklog(self):
        path = self.get_active_tracklog_path()
        # is the tracklog loaded ?
        if path not in self.tracklogs.keys():
            self.load_tracklog(path)
            self.save()
            # was the tracklog loaded successfully ?
        if path not in self.tracklogs.keys():
            return None
        else:
            return self.tracklogs[path]

    def get_active_tracklog_path(self):
        path = self.get('activeTracklogPath', None)
        return path

    def set_path_as_active_tracklog(self, path):
        self.set('activeTracklogPath', path)

    def get_tracklog_for_path(self, path):
        """Return a tracklog corresponding to the path specified."""
        if path in self.tracklogs.keys():
            return self.tracklogs[path]
        else:
            # try to load the track
            track = self.load_tracklog(path)
            if track:  # return the loaded track
                return track
            else:  # something went wrong, return None
                return None

    def get_tracklog_points_for_path(self, path):
        # used by Qt 5 UI - let's ignore the clusters for now
        #                   and just return full list of points

        # this should be ideally done better in the future
        track = self.get_tracklog_for_path(path)
        track_points = [{'latitude': point.latitude, 'longitude': point.longitude} for point in track.trackpointsList[0]]
        return track_points

    def get_tracklog_list(self):
        if self._tracklog_list:
            return self._tracklog_list
        else:
            self.list_available_tracklogs()
            return self._tracklog_list

    def get_tracklog_path_list(self):
        if self._tracklog_path_list:
            return self._tracklog_path_list
        else:
            self.list_available_tracklogs()
            return self._tracklog_path_list

    def get_loaded_tracklog_path_list(self):
        """Return a list of loaded tracklog paths."""
        return self.tracklogs.keys()

    def get_index_for_path(self, path):
        """Get index for the tracklog with corresponding path from the main tracklog lists."""

        return self._tracklog_path_list.index(path)

    def list_available_tracklogs(self):
        self.log.info("** making a list of available tracklogs")

        tf = self.modrana.paths.tracklog_folder_path
        # does the tracklog folder exist ?
        if tf is None or not os.path.exists(tf):
            return  # no tracklog folder, nothing to list
            # get the available directories,
        # each directory represents a category
        currentFolders = os.listdir(tf)
        # leave just folders (that are not hidden)
        currentFolders = list(filter(lambda x: os.path.isdir(os.path.join(tf, x)) and not x.startswith('.'), currentFolders))
        # add files from all available folders
        availableFiles = []
        pathList = []
        for folder in currentFolders:
            # TODO: support other tracklogs
            folderFiles = glob.glob(os.path.join(tf, folder, '*.gpx'))
            folderFiles.extend(glob.glob(os.path.join(tf, folder, '*.GPX')))
            # remove possible folders
            folderFiles = filter(lambda x: os.path.isfile(x), folderFiles)
            for file in folderFiles:
                path = file
                filename = os.path.split(file)[1]
                lastModifiedEpochSecs = os.path.getmtime(path)
                lastModified = strftime("%d.%m.%Y %H:%M:%S", gmtime(lastModifiedEpochSecs))
                size = utils.bytes_to_pretty_unit_string(os.path.getsize(path))
                extension = os.path.splitext(path)[1]
                cat = folder
                item = {'path': path,
                        'filename': filename,
                        'lastModified': lastModified,
                        'size': size,
                        'type': extension[1:],
                        'cat': cat}
                availableFiles.append(item)
            pathList.extend(folderFiles)

        self._category_list = currentFolders

        self.log.info("*  using this tracklog folder:")
        self.log.info("* %s" % self.modrana.paths.tracklog_folder_path)
        self.log.info("*  there are %d tracklogs available" % len(availableFiles))
        self.log.info("**")
        self._tracklog_path_list = pathList
        self._tracklog_list = availableFiles

    def get_category_list(self):
        """Return the list of available categories."""
        if not self._category_list:
            self.list_available_tracklogs()
        return self._category_list

    def get_category_dict_list(self):
        # get dictionary describing tracklog categories
        category_dict_list = []

        tracklog_folder = self.modrana.paths.tracklog_folder_path
        for category in self.get_category_list():
            tracklog_count = 0
            for item in os.listdir(os.path.join(tracklog_folder, category)):
                item_path = os.path.join(tracklog_folder, category, item)
                if os.path.isfile(item_path) and os.path.splitext(item_path)[1].lower() == ".gpx":
                    tracklog_count += 1
            category_dict_list.append({"name": category,
                                       "tracklog_count": tracklog_count})
        return category_dict_list

    def get_tracklogs_list_for_category(self, category_name):
        # get list of dictionaries describing tracklogs in a category
        tracklogs = []
        for tracklog_dict in self.get_tracklog_paths_for_category(category_name):
            tracklogs.append({"name": tracklog_dict["filename"],
                              "path": tracklog_dict["path"],
                              "size": tracklog_dict["size"]
                              })
        return tracklogs

    def get_tracklog_paths_for_category(self, cat):
        """Return a list of tracklogs in a given category."""
        if not self._tracklog_list:
            self.list_available_tracklogs()
        return list(filter(lambda x: x['cat'] == cat, self._tracklog_list))

    def setTracklogPathCategory(self, path, category):
        pass

    #    """set a category for tracklog identified by path"""
    #    # does the path/tracklog exist ?
    #    if path not in self.tracklogPathList:
    #      # we try to reload the tracklog list
    #      self.list_available_tracklogs()
    #      if path not in self.tracklogPathList:
    #        return # tracklog does not exist, so we return
    #
    #    # tracklog exists so we can set its cathegory
    #    catData = self.get('tracklogPathCathegory', {})
    #    catData[path] = cathegory
    #    # update the persistent list
    #    self.set('tracklogPathCathegory', catData)
    #
    #    index = self.get_index_for_path(path)
    #    # update the current in memmory list
    #    self.tracklogList[index]['cat'] = cathegory


    #  def load(self):
    #    start = clock()
    #
    #    try:
    #      f = open(self.cachePath, 'r')
    #      cache = cPickle.load(f)
    #
    #      self.cache = cache
    #    except:
    #      print("loadTracklogs: loading cache from file failed")
    #      self.cache = {}
    #
    #    print("Loading from cache took %1.2f ms" % (1000 * (clock() - start)))
    #
    #    files = []
    #    if os.path.exists(self.tracklogFolder):
    #      files = os.listdir(self.tracklogFolder)
    #      files = filter(lambda x: x != '.svn', files)
    #
    #
    #      print(self.tracklogFolder)
    #      print(os.path.exists(self.tracklogFolder))
    #      for file in files:
    #        try:
    #          self.load_tracklog(self.tracklogFolder + file)
    #        except:
    #          "loading tracklog failed: %s" % file
    #
    #    self._clean_cache(files)
    #    self.save()
    #    print("Loading tracklogs took %1.2f ms" % (1000 * (clock() - start)))

    def save(self):
        try:
            f = open(self.get_tracklog_cache_path(), 'w')
            pickle.dump(self.cache, f)
            f.close()
        except Exception:
            self.log.exception("can't store tracklog data to cache, tracklogs will be loaded from files next time")

    # load tracklogs

    def loadPathList(self, pathList):
        self.log.info("** Loading tracklogs list")
        start = clock()
        count = len(pathList)
        index = 1
        self.sendMessage('notification:loading %d tracklogs#1' % count)
        for path in pathList:
            self.load_tracklog(path, False)
            self.sendMessage('notification:%d of %d loaded#1' % (index, count))
            index += 1

        elapsed = (1000 * (clock() - start))
        self.log.info("** Loading tracklogs took %1.2f ms", elapsed)
        self.save()
        self._clean_cache()
        self.sendMessage('notification:%d tracks loaded in %1.2f ms#1' % (count, elapsed))

    def load_tracklog(self, path, notify=True):
        """Load a GPX file to datastructure."""
        # is the cache loaded
        if self.cache == {}:
            # load the cache
            self._load_cache()

        # just to be sure, refresh the tracklog list if needed
        if self._tracklog_list == []:
            self.list_available_tracklogs()

        start = clock()
        self.filename = path

        file = None

        try:
            file = open(path, 'rt')
        except Exception:
            self.log.exception("loading tracklog failed: %s", path)

        if notify:
            self.sendMessage('notification:loading %s#1' % path)

        if file:  # TODO: add handling of other than GPX files
            # import the GPX module only when really needed
            from upoints import gpx

            track = gpx.Trackpoints()  # create new Trackpoints object
            # lets assume we have only GPX 1.1 files TODO: 1.1 and 1.0
            try:
                track.import_locations(file)  # load a gpx file into it
            except Exception:
                self.log.exception("loading tracklog failed")
                if notify:
                    self.sendMessage('notification:loading tracklog failed#2')
                return
            file.close()

            type = "GPX"  # TODO: more formats support

            track = GPXTracklog(track, path, type, self.cache, self.save)
            self.tracklogs[path] = track
            self.log.info("Loading tracklog \n%s\ntook %1.2f ms", path, (1000 * (clock() - start)))
            if notify:
                self.sendMessage('notification:loaded in %1.2f ms' % (1000 * (clock() - start)))
            return track
        else:
            self.log.info("No tracklog file")

    # store tracklogs

    def store_route_and_set_active(self, route, name='', cat='misc'):
        path = self.store_route(route, name, cat)
        self.set('activeTracklogPath', path)

    def store_route(self, route, name="", cat='misc'):
        """store a route, found by Google Directions to a GPX file,
           then load this file to tracklogs list,
           return resulting path
           or None when storing fails"""
        # import the GPX module only when really needed
        from upoints import gpx

        newTracklog = gpx.Trackpoints()
        trackpoints = map(lambda x: gpx.Trackpoint(x[0], x[1]), route)
        newTracklog.append(trackpoints)

        timeString = strftime("%Y%m%d#%H-%M-%S", gmtime())
        # gdr = Google Directions Result, TODO: alternate prefixes when we have more routing providers

        name = name.encode('ascii', 'ignore')
        filename = "gdr_%s%s.gpx" % (name, timeString)
        # TODO: store to more formats ?
        return self.store_tracklog(newTracklog, filename, cat, "GPX")

    def store_tracklog(self, tracklog, filename, cat, type, refresh="True"):
        """Store tracklog and return the resulting path."""
        folder = self.modrana.paths.tracklog_folder_path
        if folder is None:
            self.log.error("can't store tracklog - path to tracklog folder is unknown or unusable")
            return None
        path = os.path.join(folder, cat)
        # is it a directory ?
        if not os.path.isdir(path):
            self.sendMessage("can't store tracklog - tracklog folder is not a directory")
            return None

        if type == "GPX":
            # try to create the file
            try:
                xmlTree = tracklog.export_gpx_file()
                f = open(os.path.join(path, filename), 'w')
                xmlTree.write(f)
                f.close()
            except Exception:
                self.log.exception("saving tracklog failed")
                self.sendMessage('notification:Error: saving tracklog failed#3')
                return None

        # refresh the available tracklog list,
        # so the new tracklog shows up
        if refresh:
            self.list_available_tracklogs()
            # TODO: incremental addition of new tracklogs without relisting
        self.log.info("tracklog: %s", filename)
        self.log.info("tracklog saved successfully")
        return os.path.join(path, filename)

    # helper functions

    # TODO: move this to the geo module ?
    def simple_pythagorean_distance(self, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        return math.sqrt(dx ** 2 + dy ** 2)

    # found on:
    # http://www.quanative.com/2010/01/01/server-side-marker-clustering-for-google-maps-with-python/
    def cluster_trackpoints(self, trackpointsList, cluster_distance):
        """
        Groups points that are less than cluster_distance pixels apart at
        a given zoom level into a cluster.
        """
        points = [{'latitude': point.latitude, 'longitude': point.longitude} for point in trackpointsList[0]]
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


class Tracklog():
    """A basic class representing a tracklog."""

    def __init__(self, trackpointsList, filename, type):
        self.trackpointsList = trackpointsList  # here will be the actual list of trackpoints
        self.filename = filename  # the filename as used when loading the list from file
        self.type = type
        # tracklog types: (for now)
        # 'gpx'= a GPX tracklog
        # 'kml'= a KML tracklog
        # 'nmea' = a NMEA log file
        self.tracklogName = filename  # custom name for the tracklog, by default the filename
        self.tracklogDescription = ""  # description of the tracklog

    def getFilename(self):
        return self.filename

    def getName(self):
        """returns tracklog name"""
        return self.tracklogName

    def setName(self, name):
        """sets tracklog name"""
        self.tracklogName = name

    def getType(self):
        """returns tracklog name"""
        return self.type

    def getDescription(self):
        """returns tracklog description"""
        return self.tracklogDescription

    def setDescription(self, description):
        """sets tracklog description"""
        self.tracklogDescription = description

    def getLength(self):
        """return length of the tracklog if known, None else"""
        return None

class GPXTracklog(Tracklog):
    """A class representing a GPX tracklog."""

    def __init__(self, trackpointsList, filename, type, cache, save):
        Tracklog.__init__(self, trackpointsList, filename, type)
        Tracklog.type = 'GPX'
        self.routeInfo = None  # a dictionary for storing route information
        # TODO: set this automatically

        filename = self.filename

        self.cache = cache
        self.save = save

        self.clusters = []

        self.elevation = None

        self.perElevList = None

        # do we have any points to process ?
        if self.trackpointsList == []:
            # no points, we are done :)
            return

        if filename in cache:
            gpx_log.info("** loading tracklog from cache")
            self.clusters = cache[filename].clusters
            self.routeInfo = cache[filename].routeInfo
            if self.routeInfo is not None:
                self.elevation = True
            self.perElevList = cache[filename].perElevList

        else:
            gpx_log.info("* creating clusters,routeInfo and per_elev_list: %s", filename)
            clusterDistance = 5  # cluster points to clusters about 5 kilometers in diameter
            self.clusters = []

            try:
                rawClusters = geo.cluster_trackpoints(trackpointsList, clusterDistance)  # we cluster the points
                for cluster in rawClusters:  # now we find for each cluster a circle encompassing all points
                    (centreX, centreY, radius) = geo.circle_around_point_cluster(cluster)
                    self.clusters.append(ClusterOfPoints(cluster, centreX, centreY, radius))

                self.checkElevation()

                if self.elevation is True:
                    self.getPerElev()
                else:
                    self.perElevList = None
            except Exception:
                gpx_log.exception("tracklog post-processing failed")

            ci = CacheItem(self.clusters, self.routeInfo, self.perElevList)
            cache[filename] = ci

    def modified(self):
        """the tracklog has been modified, recount all the statistics and clusters"""
        # TODO: implement this ? :D
        self.checkElevation()  # update the elevation statistics
        if self.elevation is True:
            self.getPerElev()  # update the periodic elevation data

    def checkElevation(self):
        pointsWithElevation = list(filter(lambda x: x.elevation is not None, self.trackpointsList[0]))
        if pointsWithElevation:  # do we have some points with known elevation ?
            self.elevation = True
            self.routeInfo = {}
            # there we have the points, that contain the highest, lowest, first and last point
            firstPoint = pointsWithElevation[0]
            lastPoint = pointsWithElevation[len(pointsWithElevation) - 1]
            # now we use some lambdas, to find the lowest and highest point
            maxElevationPoint = (max(pointsWithElevation, key=lambda x: x.elevation))
            minElevationPoint = (min(pointsWithElevation, key=lambda x: x.elevation))
            # just the highest/lowest elevations in numerical form
            maxElevation = float(maxElevationPoint.elevation)
            minElevation = float(minElevationPoint.elevation)
            difference = maxElevation - minElevation
            middle = minElevation + (difference / 2)
            firstElevation = float(firstPoint.elevation)
            lastElevation = float(lastPoint.elevation)
            # because there are many possible statistics about a given route with elevation,
            # we will store them in a dictionary, so new ones can be quickly added as needed
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
        this can also mean, that some info that we didn't load to the tree will be lost
        also attributes that were changed after the initial load will be written in the current (changed) state
        """
        f = open(self.filename, "w")  # open the old file
        xmlTree = self.trackpointsList.export_gpx_file()  # get the element tree
        xmlTree.write(f)  # overwrite the old file with the new structure
        gpx_log.info("%s has been replaced by the current in memory version", self.filename)
        del self.cache[self.filename]  # the file has been modified, so it must be cached again
        self.save()  # save the cache to disk

    def getPerElev(self):
        self.perElevList = geo.per_elev_list(self.trackpointsList)


class CacheItem():
    """class representing a cache item"""

    def __init__(self, clusters, routeInfo=None, perElevList=None):
        self.clusters = clusters
        self.routeInfo = routeInfo
        self.perElevList = perElevList


class ClusterOfPoints():
    """A basic class representing a cluster of nearby points."""

    def __init__(self, pointsList, centreX, centreY, radius):
        self.pointsList = pointsList  # points in the cluster
        """coordinates of the circle encompassing all points"""
        self.centreX = centreX
        self.centreY = centreY
        self.radius = radius  # radius of the circle
