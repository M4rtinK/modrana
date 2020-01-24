# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Module for managing tracklogs.
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
from modules.base_module import RanaModule
import os


def getModule(*args, **kwargs):
    return TracklogManager(*args, **kwargs)


class TracklogManager(RanaModule):
    """Module for managing tracklogs"""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self.scrollDict = {}
        self.currentNumItems = 0
        self.LTModule = None

    def firstTime(self):
        self.LTModule = self.m.get('loadTracklogs', None)

    def handleMessage(self, message, messageType, args):

        if message == 'getElevation':
            self.log.info("getting elevation info for active tracklog")
            activeTracklog = self.LTModule.get_active_tracklog()
            # generate a list of (lat,lon) tuples
            latLonList = map(lambda x: (x.latitude, x.longitude), activeTracklog.trackpointsList[0])
            # look-up elevation data using Geonames asynchronously
            online = self.m.get("onlineServices", None)
            if online:
                online.elevFromGeonamesBatchAsync(latLonList, self._handleElevationLookupResults,
                                                  'geonamesBatchResults', activeTracklog)


        elif message == 'loadTrackProfile':
            # get the data needed for drawing the dynamic route profile in the osd
            track = self.LTModule.get_active_tracklog()
            self.m.get('showOSD', None).routeProfileData = track.perElevList

        elif message == 'unLoadTrackProfile':
            self.m.get('showOSD', None).routeProfileData = None

        elif message == 'askDeleteActiveTracklog':
            ask = self.m.get('askMenu', None)
            path = self.LTModule.get_active_tracklog_path()
            question = "do you really want to delete:|%s|?" % path
            yesAction = "tracklogManager:deleteActiveTracklog|set:menu:tracklogManager#tracklogManager"
            noAction = "set:menu:tracklogManager#tracklogInfo"
            ask.setupAskYesNo(question, yesAction, noAction)

        elif message == 'deleteActiveTracklog':
            path = self.LTModule.get_active_tracklog_path()
            if path:
                self.deleteTracklog(path)
                self.set('activeTracklogPath', None)

        elif message == 'setActiveTracklogToCurrentCat':
            path = self.LTModule.get_active_tracklog_path()
            currentCategory = self.get('currentTracCat', None)
            if currentCategory:
                self.log.info("changing category for:\n%s\nto %s" % path, currentCategory)
                self.LTModule.setTracklogPathCategory(path, currentCategory)

    def deleteTracklog(self, path):
        # delete a tracklog
        self.log.info("deleting tracklog:%s", path)
        # from cache
        self.LTModule.delete_tracklog_from_cache(path)
        # from loaded tracklogs
        del self.LTModule.tracklogs[path]
        # delete the tracklog file
        os.remove(path)

        # relist all tracklogs
        self.LTModule.list_available_tracklogs()

    def _handleElevationLookupResults(self, key, results):
        onlineElevList, originalTracklog = results
        if onlineElevList:
            index = 0
            for onlinePoint in onlineElevList: # add the new elevation data to the tracklog
                originalTracklog.trackpointsList[0][index].elevation = onlinePoint[2]
                index += 1
            originalTracklog.modified() # make the tracklog update
            originalTracklog.replaceFile() # replace the old tracklog file