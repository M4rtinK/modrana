# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Allows searching by place name
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
from base_poi import poiModule
import cairo
from datetime import *
import math


def getModule(m, d, i):
    return Placenames(m, d, i)


class Placenames(poiModule):
    """Lookup nearest town or village"""

    def __init__(self, m, d, i):
        poiModule.__init__(self, m, d, i)
        self.poi = {'villages': [], 'cities': [], 'towns': []} # village, city, town
        self.load("places.txt")
        self.lastpos = (None, None)

    def load(self, filename):
        file = open(filename, "r")
        types = {'v': 'villages', 'c': 'cities', 't': 'towns'}
        for line in file:
            line = line.strip()
            (lat, lon, id, typeID, name) = line.split("\t")
            type = types.get(typeID, None)
            if type is not None:
                self.addItem(type, name, lat, lon)
        self.needUpdate = True # Request update of meta-info

    def lookup(self, lat, lon):
        limits = {'villages': 10.0, 'towns': 30.0, 'cities': 150.0}
        kmToDeg = 360.0 / 40041.0

        nearest = None
        nearestDist = None

        for type, places in self.poi.items():
            limit = limits.get(type, 0) * kmToDeg
            limit *= limit

            for place in places:
                plat = place['lat']
                plon = place['lon']
                dx = plon - lon
                dy = plat - lat
                dist = dx * dx + dy * dy
                if dist < limit:
                    if nearestDist is None or dist < nearestDist:
                        nearestDist = dist
                        nearest = place['name']
        return nearest

    def update(self):
        """If requested, lookup the nearest place name"""
        self.updatePoi()
        if self.get('lookup_place', False):
            pos = self.get('pos', None)
            if pos is not None:
                if pos != self.lastpos:
                    place = self.lookup(pos[0], pos[1])
                    if place:
                        self.set('nearest_place', place)
                    self.lastpos = pos