# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Replay a GPX file as position data
#----------------------------------------------------------------------------
# Copyright 2007-2008, Oliver White
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
from time import *

from upoints import gpx


def getModule(m, d, i):
    return ReplayGpx(m, d, i)


class ReplayGpx(RanaModule):
    """Replay a GPX"""

    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)
        self.nodes = []
        self.pos = 0
        self.numNodes = 0
        self.updateTime = 0
        self.replayPeriod = 1 # second

    def load(self, filename):
        self.nodes = []

        file = open(filename, 'r')

        if file:
            track = gpx.Trackpoints() # create new Trackpoints object
            track.import_locations(file) # load a gpx file into it
            for point in track[0]: #iterate over the points, track[0] is list of all points in file
                lat = point.latitude
                lon = point.longitude
                self.nodes.append([lat, lon])
            file.close()
            self.numNodes = len(self.nodes)
            self.set("centreOnce", True)
            self.pos = int(self.get("replayStart", 0) * self.numNodes)


        #this seems to work only with GPX 1.0
        #      regexp = re.compile("<trkpt lat=['\"](.*?)['\"] lon=['\"](.*?)['\"]")
        #      for text in file:
        #        matches = regexp.match(text)
        #        if(matches):
        #          lat = float(matches.group(1))
        #          lon = float(matches.group(2))
        #          self.nodes.append([lat,lon])
        #      file.close()
        #      self.numNodes = len(self.nodes)
        #      self.set("centreOnce", True)
        #      self.pos = int(self.get("replayStart",0) * self.numNodes)

        else:
            print("No file")

    def dump(self):
        print("%d nodes:" % len(self.nodes))
        for n in self.nodes:
            print("%1.4f, %1.4f" % (n[0], n[1]))

    def scheduledUpdate(self):
        if self.numNodes < 1:
            return
        self.pos += 1
        if self.pos >= self.numNodes:
            self.pos = 0
        (lat, lon) = self.nodes[self.pos]
        self.set('pos', (lat, lon))
        self.set('pos_source', 'replay')
        self.set('needsRedraw', True)

    def update(self):
        # Run scheduledUpdate every second
        t = time()
        dt = t - self.updateTime
        if dt > self.replayPeriod:
            self.updateTime = t
            self.scheduledUpdate()

