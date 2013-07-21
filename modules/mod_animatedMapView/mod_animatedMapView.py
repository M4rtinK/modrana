# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Sample of a Rana module.
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
from . import tile


def getModule(m, d, i):
    return AnimatedMapView(m, d, i)


class AnimatedMapView(RanaModule):
    """A sample pyroute module"""

    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)
