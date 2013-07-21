# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Library for handling "simple-packed" OpenStreetMap vector data
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
import os
import struct
from core import tilenames


def getVmapBaseDir(options=None):
    if not options: options = {}
    return options.get("vmapTileDir", "data/tiledata")


def getVmapBaseZoom(options=dict()):
    return 14


def getVmapTileNum(x, y, z, options={}):
    ourZ = getVmapBaseZoom(options)
    if z >= ourZ:
        while z > ourZ:
            x = int(x / 2)
            y = int(y / 2)
            z -= 1
        return x, y, z


def getVmapFilename(xi, yi, zi, options={}):
    xyz = getVmapTileNum(xi, yi, zi, options)
    if xyz is not None:
        (x, y, z) = xyz
        xdir = int(x / 64)
        ydir = int(y / 64)
        filename = "%s/%d_%d/%d_%d.bin" % (getVmapBaseDir(options), xdir, ydir, x, y)
        return filename


class MapData(object):
    def __init__(self, filename=None):
        """Load an OSM XML file into memory"""
        self.ways = {}
        if filename is not None:
            self.load(filename)

    def optimise(self):
        for k, way in self.ways.items():
            (x1, x2, y1, y2) = (None, None, None, None)
            for n in way['n']:
                (lat, lon, nid) = n
                if y1 is None or lat < y1:
                    y1 = lat
                if y2 is None or lat > y2:
                    y2 = lat
                if x1 is None or lon < x1:
                    x1 = lon
                if x2 is None or lon > x2:
                    x2 = lon
                #print("%1.3f to %1.3f, %1.3f to %1.3f" % (x1,x2,y1,y2))
            way['bounds'] = (x1, x2, y1, y2)


    def load(self, filename, optimise=True):
        """Load an OSM XML file into memory"""
        if not os.path.exists(filename):
            print("File doesn't exist: '%s'" % filename)
            return []
        f = file(filename, "rb")

        size = os.path.getsize(filename)
        while f.tell() < size:
            way = {'n': []}

            wayID = struct.unpack("I", f.read(4))[0]

            numNodes = struct.unpack("I", f.read(4))[0]
            for n in range(numNodes):
                (x, y, nid) = struct.unpack("III", f.read(3 * 4))
                (lat, lon) = tilenames.pxpy2ll(x, y, 31)
                way['n'].append((lat, lon, nid))
            way['style'] = struct.unpack("I", f.read(4))[0]
            way['layer'] = struct.unpack("b", f.read(1))[0]

            tagSize = struct.unpack("H", f.read(2))[0]

            c = 0
            while c < tagSize:
                k = f.read(1)
                s = struct.unpack("H", f.read(2))[0]
                v = f.read(s)
                way[k] = v
                c += 3 + s
            self.ways[wayID] = way

        if optimise:
            self.optimise()