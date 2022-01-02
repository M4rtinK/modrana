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
        self.LTModule = None

    def firstTime(self):
        self.LTModule = self.m.get('loadTracklogs', None)

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