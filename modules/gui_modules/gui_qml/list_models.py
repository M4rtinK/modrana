# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# A modRana QML GUI list models
#----------------------------------------------------------------------------
# Copyright 2013, Martin Kolman
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
# QML list model handling
from PySide import QtCore


# partially based on the gPodderListModel
# list model
class BaseListModel(QtCore.QAbstractListModel):
  def __init__(self, objects=None):
    QtCore.QAbstractListModel.__init__(self)
    if objects is None:
        objects = []
    self._objects = objects
    # self.setRoleNames({0: 'data', 1: 'section'})
    self.setRoleNames({0: 'data'})

  def sort(self):
    # Unimplemented for the generic list model
    self.reset()

  def insert_object(self, o):
    self._objects.append(o)
    self.sort()

  def remove_object(self, o):
    self._objects.remove(o)
    self.reset()

  def set_objects(self, objects):
    self._objects = objects
    self.sort()

  def get_objects(self):
    return self._objects

  def get_object(self, index):
    return self._objects[index.row()]

  def rowCount(self, parent=QtCore.QModelIndex()):
    return len(self.get_objects())

  def data(self, index, role):
    if index.isValid():
      if role == 0:
        return self.get_object(index)
      elif role == 1:
        return self.get_object(index).qsection
    return None

class NestedListModel(BaseListModel):
  def __init__(self):
    BaseListModel.__init__(self)

class ListItem(QtCore.QObject):
  def __init__(self, data, children=None):
    if not children: children = []
    QtCore.QObject.__init__(self)
    self._data = data
    self._children = children

  changed = QtCore.Signal()
  childrenChanged = QtCore.Signal()

  def _getData(self):
    return self._data

  def _getChildCount(self):
    return len(self._children)

  @QtCore.Slot(int, result=QtCore.QObject)
  def _getChild(self, index):
    try:
      return self._children[index]
    except IndexError:
      # index out of bounds
      return None

  data = QtCore.Property(QtCore.QObject, _getData, notify=changed)
  childrenCount = QtCore.Property(QtCore.QObject, _getChildCount, notify=childrenChanged)

class ListItem(QtCore.QObject):
  pass
