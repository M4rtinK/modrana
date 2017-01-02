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
#===========================
# !!! THIS DOES NOT WORK !!!
#===========================
#
# at least with PySide 1.1.1-3 on Ubuntu 12.10
# - it just shows as undefined when the class is accessed from QML
# - the plain example from qt-project wiki works, but
# it is not very handy for the modRana use-case
# - as a result, "manual" wrapping will be used for the time being
#
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


class AutoQObject(QtCore.QObject):
    """
    Automatic Python object -> QObject wrapper
    based on:
    http://qt-project.org/wiki/Auto-generating-QObject-from-template-in-PySide

    Extended to be able to both define the properties of the class and also
    set their initial values from the nested tuple.
    Like this, wrapping python object instances from the modRana core
    is very easy and concentrated to a single place.
    """

    def __init__(self, classDef, className=None):
        QtCore.QObject.__init__(self)
        # if no name is specified, use the name
        # of the (sub)class
        if className is None:
            className = self._getClassName()
        self._name = className
        self._getClassName()
        self._keys = []

        for key, val, source in classDef:
            # is the source method defined ?
            if source:
                # get value from the source method or save the value directly
                if isfunction(source):
                    setattr(self, '_' + key, source())
                else:
                    setattr(self, '_' + key, source)
                    # use default value for the data type
            else:
                setattr(self, '_' + key, val())
            self._keys.append(key)

        for key, value, source in classDef:
            setattr(self, '_nfy_' + key, QtCore.Signal())
            nfy = getattr(self, '_nfy_' + key)

            def _getProperty(key):
                def f(self):
                    return getattr(self, '_' + key)

                return f

            def _setProperty(key):
                def f(self, value):
                    setattr(self, '_' + key, value)
                    getattr(self, '_nfy_' + key).emit()

                return f

            setattr(self, '_set_' + key, _setProperty(key))
            setProperty = getattr(self, '_set_' + key)
            setattr(self, '_get_' + key, _getProperty(key))
            getProperty = getattr(self, '_get_' + key)

            setattr(self, key, QtCore.Property(value, getProperty, setProperty, notify=nfy))


    def __repr__(self):
        values = ('%s=%r' % (key, self.__dict__['_' + key]) \
                  for key in self._keys)
        return '<%s (%s)>' % (self._name, ', '.join(values))

    def _getAttr(self, key):
        return getattr(self, key)

    @classmethod
    def _getClassName(cls):
        return cls.__name__

# return Object

class NestedWrapper(AutoQObject):
    """NestedWrapped enables to include additional
    QObject based object instances inside this QObject
    The objects are accessed by a simple ListModel based API:
    count - this property county the children of this object
    get(index) - get child with the given index
    """

    def __init__(self, classDef, className, children=None):
        if not children: children = []
        AutoQObject.__init__(self, classDef, className)
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
        classDef = (
            ("id", str, group.id),
            ("label", str, group.label),
            ("icon", str, group.icon)
        )
        wrappedLayers = map(lambda x: MapLayerWrapper(x), group.layers)
        NestedWrapper.__init__(self, classDef, None, wrappedLayers)


class MapLayerWrapper(AutoQObject):
    """Wrapper for MapLayer objects"""

    def __init__(self, wrappedObject):
        classDef = (
            ("id", str, wrappedObject.id),
            ("label", str, wrappedObject.label),
            ("url", str, wrappedObject.url),
            ("max_zoom", int, wrappedObject.max_zoom),
            ("min_zoom", int, wrappedObject.min_zoom),
            ("folder_name", str, wrappedObject.folder_name),
            ("coordinates", str, wrappedObject.coordinates),
            ("icon", str, wrappedObject.icon)
        )
        AutoQObject.__init__(self, classDef)
