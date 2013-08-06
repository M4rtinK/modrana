# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# A modRana Python Object wrappers
# for use by the QML GUI
#----------------------------------------------------------------------------
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
#
# How to use this
#
# When wrapping a new object, just subclass the AutoQObject class
# (or NestedWrapped if you want to nest QObjects) and add a
# classDef tuple of tuple three member tuples.
# The three members have this meaning:
# 1. name of the property as it will be seen from QML
# 2. type of property (needed by Qt/QML)
# 3. initial value of the property
# - can be either a value or a function
#
# Like this, you should be able to wrap any Python object for
# use from QML easily. Of course, you can also add other properties
# and slots to the subclass.

from PySide import QtCore
from inspect import isfunction
from pprint import pprint
from core.backports import six


class NestedWrapper(QtCore.QObject):
    """NestedWrapped enables to include additional
    QObject based object instances inside this QObject
    The objects are accessed by a simple ListModel based API:
    count - this property county the children of this object
    get(index) - get child with the given index
    """

    def __init__(self, children=None):
        if not children: children = []
        QtCore.QObject.__init__(self)
        self._children = children

    childrenChanged = QtCore.Signal()

    def _get(self):
        return self._data

    def _getCount(self):
        return len(self._children)

    @QtCore.Slot(int, result=QtCore.QObject)
    def get(self, index):
        try:
            return self._children[index]
        except IndexError:
            # index out of bounds
            return None

    childrenCount = QtCore.Property(int, _getCount, notify=childrenChanged)


class MapLayerGroupWrapper(NestedWrapper):
    """Wrapper for MapLayerGroup objects"""

    def __init__(self, group):
        self.wo = group
        NestedWrapper.__init__(self, self.wo.layers)

    @QtCore.Slot(int, result=str)
    def getLayerId(self, index):
        try:
            return self._children[index].id
        except IndexError:
            return None

    @QtCore.Slot(int, result=str)
    def getLayerLabel(self, index):
        try:
            return self._children[index].label
        except IndexError:
            return None

    changed = QtCore.Signal()

    def _getId(self):
        return self.wo.id

    id = QtCore.Property(str, _getId, notify=changed)

    def _getLabel(self):
        return self.wo.label

    label = QtCore.Property(str, _getLabel, notify=changed)

    def _getIcon(self):
        return self.wo.icon

    icon = QtCore.Property(str, _getIcon, notify=changed)


class MapLayerWrapper(QtCore.QObject):
    """Wrapper for MapLayer objects"""

    def __init__(self, wrappedObject):
        self.wo = wrappedObject
        QtCore.QObject.__init__(self)

    changed = QtCore.Signal()

    id = QtCore.Property(str, lambda x: x.wo.id, notify=changed)
    label = QtCore.Property(str, lambda x: x.wo.label, notify=changed)
    url = QtCore.Property(str, lambda x: x.wo.url, notify=changed)
    maxZoom = QtCore.Property(int, lambda x: x.wo.maxZoom, notify=changed)
    minZoom = QtCore.Property(int, lambda x: x.wo.minZoom, notify=changed)
    folderName = QtCore.Property(str, lambda x: x.wo.folderName, notify=changed)
    coordinates = QtCore.Property(str, lambda x: x.wo.coordinates, notify=changed)
    icon = QtCore.Property(str, lambda x: x.wo.icon, notify=changed)

class PointWrapper(QtCore.QObject):
    """Wrapper for Point objects"""

    def __init__(self, wrappedObject):
        self.wo = wrappedObject
        QtCore.QObject.__init__(self)

    changed = QtCore.Signal()

    name = QtCore.Property(six.text_type, lambda x: x.wo.name, notify=changed)
    summary = QtCore.Property(six.text_type, lambda x: x.wo.summary, notify=changed)
    description = QtCore.Property(six.text_type, lambda x: x.wo.description, notify=changed)
    lat = QtCore.Property(float, lambda x: x.wo.lat, notify=changed)
    lon = QtCore.Property(float, lambda x: x.wo.lon, notify=changed)
    elevation = QtCore.Property(float, lambda x: x.wo.elevation, notify=changed)


    # def _get(self):
    #   return self.wo
    #
    #  = QtCore.Property(,)
