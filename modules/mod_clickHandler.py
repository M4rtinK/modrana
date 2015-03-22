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
import time

def getModule(*args, **kwargs):
    return ClickHandler(*args, **kwargs)


class ClickHandler(RanaModule):
    """handle mouse clicks"""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self.beforeDraw()
        self.ignoreNextClicks = 0
        self._layers = [[],[],[]]
        self.dragAreas = []
        self._scrollAreas = []
        self.dragScreen = None
        self.timedActionInProgress = None
        self._lastSingleActionTimestamp = time.time()
        self._screenClickedNotify = None
        self._messages = None

    def firstTime(self):
        self._messages = self.m.get("messages")

    def beforeDraw(self):
        self._layers = [[],[],[]]
        self.dragAreas = []
        self._scrollAreas = []
        self.dragScreen = None
        self.timedActionInProgress = None
        self._screenClickedNotify = None

    def register(self, rect, action, timedAction, layerNumber, doubleClick=False):
        # NOTE: layers with higher number "cover" layers with lower number
        #       currently layers 0, 1 and 2 are used
        #       -> if a click is "caught" in an upper layer,
        #          it is not propagated to the layer below
        self._layers[layerNumber].append([rect, action, timedAction, doubleClick])

    def registerXYWH(self, x1, y1, dx, dy, action, timedAction=None, layer=0, doubleClick=False):
        if timedAction: # at least one timed action
            self.timedActionInProgress = True
        area = Rectangle(x1, y1, dx, dy)
        self.register(area, action, timedAction, layer, doubleClick)

    def registerXYXY(self, x1, y1, x2, y2, action, timedAction=None, layer=0, doubleClick=False):
        if timedAction: # at least one timed action
            self.timedActionInProgress = True
        area = Rectangle(x1, y1, x2 - x1, y2 - y1)
        self.register(area, action, timedAction, layer, doubleClick)

    def registerScreenClicked(self, message):
        self._screenClickedNotify = message

    def registerScrollXYWH(self, x1, y1, dx, dy, callback):
        area = Rectangle(x1, y1, dx, dy)
        self._scrollAreas.append((area, callback))

    def handleClick(self, x, y, msDuration, doubleClick=False):
        if self._screenClickedNotify:
            self._messages.routeMessage(self._screenClickedNotify)
        if self.ignoreNextClicks > 0:
            self.ignoreNextClicks -= 1
        else:
            for layer in reversed(self._layers):
                for area in layer:
                    if self._processClickArea(area, x, y, doubleClick=doubleClick):
                        break
        self.set('needRedraw', True)

    def handleDoubleClick(self, x, y):
        self.handleClick(x, y, 0, doubleClick=True)

    def handleScrolling(self, event):
        for area in self._scrollAreas:
            rect, callback = area
            if rect.contains(event.x, event.y):
                callback(event)
                break

    def _processClickArea(self, area, x, y, doubleClick=False):
        hit = False
        (rect, action, timedAction, doubleClickRequested) = area
        clickMatching = doubleClickRequested == doubleClick
        if rect.contains(x, y) and clickMatching:
            hit = True
            if doubleClick:
                # prevent double click from triggering if a single click
                # action has just been triggered
                # -> for example rapid clicking on the zoom buttons
                #    should not trigger the double click zoom action
                dt = time.time() - self._lastSingleActionTimestamp
                if dt < 0.2:
                    self.log.info("Skipping double-click")
                    hit = False
                else:
                    self.log.info("DoubleClicked, sending %s", action)
            else:
                self._lastSingleActionTimestamp = time.time()
                self.log.info("Clicked, sending %s", action)
            self.set('lastClickXY', (x, y))
            if hit:
                self._messages.routeMessage(action)
        return hit

    def handleLongPress(self, pressStartEpoch, msCurrentDuration, startX, startY, x, y):
        """handle long press"""
        # make sure subsequent long presses are ignored until release
        if self.ignoreNextClicks == 0:
            for layer in reversed(self._layers):
                for area in layer:
                    if self._processLPArea(area, msCurrentDuration, x, y):
                        break

    def _processLPArea(self, area, msCurrentDuration, x, y):
        hit = False
        (rect, normalAction, timedAction, doubleClickRequested) = area
        if timedAction: # we are interested only in timed actions
            if rect.contains(x, y):
                (givenMsDuration, action) = timedAction
                if givenMsDuration <= msCurrentDuration:
                    self.log.info("Long-clicked (%f ms), sending %s", givenMsDuration, action)
                    hit = True
                    self.set('lastClickXY', (x, y))
                    self.modrana.gui.lockDrag()
                    self._messages.routeMessage(action)
                    self.set('needRedraw', True)
                    self.ignoreNextClicks = self.dmod.lpSkipCount()
        return hit

    def registerDraggable(self, x1, y1, x2, y2, module):
        self.dragAreas.append((Rectangle(x1, y1, x2 - x1, y2 - y1), module))

    def registerDraggableEntireScreen(self, module):
        self.log.info("Entire screen is draggable for %s ", module)
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
                        self.log.error("Drag registered to nonexistent module %s", module)
