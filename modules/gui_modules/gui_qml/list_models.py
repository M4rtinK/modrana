# -*- coding: utf-8 -*-
# QML list model handling
from PySide.QtCore import *

class BaseListModel(QAbstractListModel):
  def __init__(self, mList):
    QAbstractListModel.__init__(self)
    self._items=mList

  def rowCount(self, parent = QModelIndex()):
    return len(self._items)
