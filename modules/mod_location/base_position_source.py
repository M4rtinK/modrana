# -*- coding: utf-8 -*-
# Base class for a position source
#---------------------------------------------------------------------------
# Copyright 2012, Martin Kolman
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
from core.fix import Fix


class PositionSource(object):
    """
    An abstract position source class
    """

    def __init__(self, location):
        self.location = location
        self.fix = Fix() # position fix
        self.debug = False

    def start(self):
        """
        start positioning
        """
        pass

    def stop(self):
        """
        stop positioning
        """

    def isRunning(self):
        """
        report is positioning is running
        """
        return False

    def getFix(self):
        """
        return the Fix object instance
        """
        return self.fix

    def canSetUpdateInterval(self):
        """
        report whether the position source can set update interval
        """
        return False

    def setUpdateInterval(self, interval):
        """
        set update interval, return whether interval was successfully set
        """
        return False

    def setDebug(self, value):
        self.debug = value
