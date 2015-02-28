# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Menu for quickly adding waypoints when on move
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
import cairo
from time import time
from math import pi


def getModule(*args, **kwargs):
    return ClickMenu(*args, **kwargs)


class ClickMenu(RanaModule):
    """Overlay info on the map"""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self.lastWaypoint = "(none)"
        self.lastWaypointAddTime = 0
        self.messageLingerTime = 2

    def handleMessage(self, message, messageType, args):
        if message == "addWaypoint":
            m = self.m.get("waypoints", None)
            if m is not None:
                self.lastWaypoint = m.newWaypoint()
                self.lastWaypointAddTime = time()

    def drawMapOverlay(self, cr):
        """Draw an overlay on top of the map, showing various information
        about position etc."""

    #    waypoins will be done in another way, so this is disabled for the time being
    #    (x,y,w,h) = self.get('viewport')
    #
    #    dt = time() - self.lastWaypointAddTime
    #    if(dt > 0 and dt < self.messageLingerTime):
    #      self.drawNewWaypoint(cr, x+0.5*w, y+0.5*h, w*0.3)
    #    else:
    #	    m = self.m.get('clickHandler', None)
    #	    if(m != None):
    #	      m.registerXYWH(x+0.25*w,y+0.25*h,w*0.5,h*0.5, "clickMenu:addWaypoint")

    def drawNewWaypoint(self, cr, x, y, size):
        text = self.lastWaypoint
        cr.set_font_size(200)
        extents = cr.text_extents(text)
        (w, h) = (extents[2], extents[3])

        cr.set_source_rgb(0, 0, 0.5)
        cr.arc(x, y, size, 0, 2 * pi)
        cr.fill()

        x1 = x - 0.5 * w
        y1 = y + 0.5 * h
        border = 20

        cr.set_source_rgb(1, 1, 1)
        cr.move_to(x1, y1)
        cr.show_text(text)
        cr.fill()
