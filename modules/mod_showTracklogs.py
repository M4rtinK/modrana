# -*- coding: utf-8 -*-
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
from modules.base_module import RanaModule
from core import geo
import math


def getModule(*args, **kwargs):
    return ShowTracklogs(*args, **kwargs)


class ShowTracklogs(RanaModule):
    """draws a GPX track on the map"""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)

        self.lineWidth = 7 #with of the line denoting GPX tracks
        self.distinctColors = [
            'black',
            'blue',
            'green',
            'pink',
            'cyan',
            'red',
            'gold',
            'magenta',
            'yellow'
        ]
        self.colorIndex = 0


    def getDistinctColorName(self):
        """loop over a list of distinct colors"""
        distinctColor = self.distinctColors[self.colorIndex]
        colorCount = len(self.distinctColors)
        self.colorIndex = (self.colorIndex + 1) % colorCount
        return distinctColor

    def getDistinctColorList(self):
        if self.distinctColors:
            return self.distinctColors
        else:
            return ['navy'] # one navy ought be enough for anybody

    def removeNonexistentTracks(self, tracks):
        """remove tracks that don't exist,
           both from "tracks" and the persistent list,
           then return the tracks that do exist """
        loadTl = self.m.get('loadTracklogs', None) # get the tracklog module
        if loadTl:
            availablePaths = loadTl.get_tracklog_path_list()

            # look which files exist and which don't
            nonexistent = filter(lambda x: x not in availablePaths, tracks)
            # remove nonexistent tracks:

            # from the persistent list
            visibleTracklogs = self.get('visibleTracklogsDict', {})
            for nItem in nonexistent:
                if nItem in visibleTracklogs:
                    del visibleTracklogs[nItem]
            self.set('visibleTracklogsDict', visibleTracklogs)

            # from the input list
            tracks = filter(lambda x: x not in nonexistent, tracks)

            # return the existing tracks
            return tracks


    def makeTrackVisible(self, path):
        """
        make a tracklog visible
        """
        visibleTracklogs = self.get('visibleTracklogsDict', {})
        if path in visibleTracklogs:
            return
        else:
            visibleTracklogs[path] = {'colorName': self.getDistinctColorName()}
            self.set('visibleTracklogsDict', visibleTracklogs)
        self.set('showTracklog', 'simple')
        return


    def makeTrackInvisible(self, path):
        """
        make a tracklog invisible = don't draw it
        """
        visibleTracklogs = self.get('visibleTracklogsDict', {})
        if path in visibleTracklogs:
            del visibleTracklogs[path]
        self.set('visibleTracklogsDict', visibleTracklogs)


    def isVisible(self, path):
        """check if a tracklog is visible
           returns False or True"""
        visibleTracklogs = self.get('visibleTracklogsDict', {})
        return path in visibleTracklogs

    def setTrackColor(self, path, colorName):
        visibleTracklogs = self.get('visibleTracklogsDict', {})
        if path in visibleTracklogs:
            visibleTracklogs[path]['colorName'] = colorName
            self.set('visibleTracklogsDict', visibleTracklogs)

    def getNat(self, x):
        """return number if positive, return 0 if negative; 0 is positive"""
        if x < 0:
            return 0
        else:
            return x
