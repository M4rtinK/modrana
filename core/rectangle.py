# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Rectangle object
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
#----------------------------------------------------------------------------
class Rectangle(object):
    def __init__(self, x, y, dx, dy):
        self.x1 = x;
        self.y1 = y;
        self.x2 = x + dx;
        self.y2 = y + dy;
        self.w = dx
        self.h = dy
        self.cx = x + 0.5 * dx
        self.cy = y + 0.5 * dy

    def xc(self, p):
        """Returns centre (x) of an area"""
        return (self.x1 + p * self.w)

    def yc(self, p):
        """Returns centre (y) of an area"""
        return (self.y1 + p * self.h)

    def copyself(self, px1, py1, px2, py2):
        """Returns a rectangle containing part of this rectangle's area.
        Specify coordinates where the limits of the parent rect are (0,0 - 1,1)"""
        x1 = self.xc(px1)
        y1 = self.yc(py1)
        return (Rectangle( \
            self.cr,
            x1,
            y1,
            self.xc(px2) - x1,
            self.yc(py2) - y1,
            self.modules,
            self.iconSet))

    def copyAndExtendTo(self, otherRect):
        """Return a rectangle containing the area between (and including)
        this rectange and another one (think of it like colspan or rowspan)"""
        return (Rectangle( \
            self.cr,
            self.x1,
            self.y1,
            otherRect.x2 - self.x1,
            otherRect.y2 - self.y1,
            self.modules,
            self.iconSet))

    def xsplit(self, p):
        """Split a rectangle into two by some portion (0,1) of the width"""
        a = self.copyself(0, 0, p, 1)
        b = self.copyself(p, 0, 1, 1)
        return (a, b)

    def ysplit(self, p):
        """Split a rectangle into two by some portion (0,1) of the height"""
        a = self.copyself(0, 0, 1, p)
        b = self.copyself(0, p, 1, 1)
        return (a, b)

    def xsplitn(self, px1, py1, px2, py2, n):
        """Split a rectangle into many horizontal parts"""
        dpx = (px2 - px1) / n
        cells = []
        for i in range(0, n - 1):
            px = px1 + i * dpx
            cells.append(self.copyself(px, py1, px + dpx, py2))
        return (cells)

    def ysplitn(self, px1, py1, px2, py2, n):
        """Split a rectangle into many vertical parts"""
        dpy = (py2 - py1) / n
        cells = []
        for i in range(0, n):
            py = py1 + i * dpy
            cells.append(self.copyself(px1, py, px2, py + dpy))
        return (cells)

    def contains(self, x, y):
        """Test if the point is within this rectangle"""
        if (x > self.x1 and x < self.x2 and y > self.y1 and y < self.y2):
            return (1)

