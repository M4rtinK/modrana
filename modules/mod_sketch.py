# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Sketching on touchscreen
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
from modules.base_module import RanaModule
from time import time
# only import GKT libs if GTK GUI is used
from core import gs

if gs.GUIString == "GTK":
    import cairo


def getModule(m, d, i):
    return Sketch(m, d, i)


class Sketch(RanaModule):
    """Sketching functionality"""

    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)
        self.points = []

        if 0: # to test
            m = self.m.get("menu", None)
            if m:
                m.clearMenu('sketch', "set:menu:None")
                self.set("menu", "sketch")

    def drawMenu(self, cr, menuName, args=None):
        if self.get("menu", "") == "sketch":
            (x, y, w, h) = self.get('viewport')

            count = 0
            for p in self.points:
                if count == 0:
                    cr.move_to(p[0], p[1])
                else:
                    cr.line_to(p[0], p[1])
                count += 1
            cr.stroke()

            mod = self.m.get("clickHandler", None)
            if mod:
                mod.registerDraggableEntireScreen("sketch")

    def dragEvent(self, startX, startY, dx, dy, x, y):
        self.points.append((x, y))
  