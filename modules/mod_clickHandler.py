# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Allows areas of screen to be registered as clickable, sending a message
#----------------------------------------------------------------------------
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
#---------------------------------------------------------------------------
from modules.base_module import RanaModule
from core.rectangle import Rectangle


def getModule(m, d, i):
    return ClickHandler(m, d, i)


class ClickHandler(RanaModule):
    """handle mouse clicks"""

    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)
        self.beforeDraw()
        self.ignoreNextClicks = 0

    def beforeDraw(self):
        self.layers = {2: [], 0: []}
        self.dragAreas = []
        self.dragScreen = None
        self.timedActionInProgress = None

    def register(self, rect, action, timedAction, layerNumber):
        #NOTE: layers with higher number "cover" layers with lower number
        #currently layers 0 and 2 are used
        # -> if a click is "caught" in in upper layer, it is not propagated to the layer below
        self.layers[layerNumber].append([rect, action, timedAction])

    def registerXYWH(self, x1, y1, dx, dy, action, timedAction=None, layer=0):
        if timedAction: # at least one timed action
            self.timedActionInProgress = True
        area = Rectangle(x1, y1, dx, dy)
        self.register(area, action, timedAction, layer)

    def registerXYXY(self, x1, y1, x2, y2, action, timedAction=None, layer=0):
        if timedAction: # at least one timed action
            self.timedActionInProgress = True
        area = Rectangle(x1, y1, x2 - x1, y2 - y1)
        self.register(area, action, timedAction, layer)

    def handleClick(self, x, y, msDuration):
    #    print("Clicked at %d,%d for %d" % (x,y,msDuration))
        if self.ignoreNextClicks > 0:
            self.ignoreNextClicks -= 1
        #      print("ignoring click, %d remaining" % self.ignoreNextClicks)
        else:
            hit = False
            for area in self.layers[2]:
                hit = self._processClickArea(area, x, y)
                if hit:
                    break
            if not hit: # no hit in upper layer, continue to lower layer
                for area in self.layers[0]:
                    self._processClickArea(area, x, y)

        self.set('needRedraw', True)

    def _processClickArea(self, area, x, y):
        hit = False
        (rect, action, timedAction) = area
        if rect.contains(x, y):
            m = self.m.get("messages", None)
            if m:
                print("Clicked, sending %s" % action)
                hit = True
                self.set('lastClickXY', (x, y))
                m.routeMessage(action)
            else:
                print("No message handler to receive clicks")
        return hit

    def handleLongPress(self, pressStartEpoch, msCurrentDuration, startX, startY, x, y):
        """handle long press"""
        # make sure subsequent long presses are ignored until release
        if self.ignoreNextClicks == 0:
            hit = False
            for area in self.layers[2]:
                hit = self._processLPArea(area, msCurrentDuration, x, y)
            if not hit: # no hit in upper layer, continue to lower layer
                for area in self.layers[0]:
                    self._processLPArea(area, msCurrentDuration, x, y)

    def _processLPArea(self, area, msCurrentDuration, x, y):
        hit = False
        (rect, normalAction, timedAction) = area
        if timedAction: # we are interested only in timed actions
            if rect.contains(x, y):
                (givenMsDuration, action) = timedAction
                if givenMsDuration <= msCurrentDuration:
                    m = self.m.get("messages", None)
                    if m:
                        print("Long-clicked (%f ms), sending %s" % (givenMsDuration, action))
                        hit = True
                        self.set('lastClickXY', (x, y))
                        self.modrana.gui.lockDrag()
                        m.routeMessage(action)
                        self.set('needRedraw', True)
                    else:
                        print("No message handler to receive clicks")
                    self.ignoreNextClicks = self.dmod.lpSkipCount()
        return hit

    def registerDraggable(self, x1, y1, x2, y2, module):
        self.dragAreas.append((Rectangle(x1, y1, x2 - x1, y2 - y1), module))

    def registerDraggableEntireScreen(self, module):
        print("Entire screen is draggable for %s " % module)
        self.dragScreen = module

    def handleDrag(self, startX, startY, dx, dy, x, y, msDuration):
        # react on timed actions interactively
        if self.dragScreen:
            m = self.m.get(self.dragScreen, None)
            if m is not None:
                m.dragEvent(startX, startY, dx, dy, x, y)
        else:
            for area in self.dragAreas:
                (rect, module) = area
                if rect.contains(startX, startY):
                    m = self.m.get(module, None)
                    if m is not None:
                        m.dragEvent(startX, startY, dx, dy, x, y)
                    else:
                        print("Drag registered to nonexistent module %s" % module)
