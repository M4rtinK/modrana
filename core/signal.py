# -*- coding: utf-8 -*-
# modRana - signal object

## based on: http://code.activestate.com/recipes/576477/
#Author:  Thiago Marcos P. Santos

from weakref import WeakValueDictionary

import sys

PYTHON3 = sys.version_info[0] > 2


class Signal(object):
    def __init__(self):
        self.__slots = WeakValueDictionary()

    def __call__(self, *args, **kargs):
        for key in self.__slots:
            func, _ = key
            func(self.__slots[key], *args, **kargs)

    def connect(self, slot):
        if PYTHON3:
            key = (slot.__func__, id(slot.__self__))
            self.__slots[key] = slot.__self__
        else:
            key = (slot.im_func, id(slot.im_self))
            self.__slots[key] = slot.im_self

    def disconnect(self, slot):
        if PYTHON3:
            key = (slot.__func__, id(slot.__self__))
            if key in self.__slots:
                self.__slots.pop(key)
        else:
            key = (slot.im_func, id(slot.im_self))
            if key in self.__slots:
                self.__slots.pop(key)

    def clear(self):
        self.__slots.clear()

        ## Sample usage:
        #class Model(object):
        #  def __init__(self, value):
        #    self.__value = value
        #    self.changed = Signal()
        #
        #  def set_value(self, value):
        #    self.__value = value
        #    self.changed() # Emit signal
        #
        #  def get_value(self):
        #    return self.__value
        #
        #
        #class View(object):
        #  def __init__(self, model):
        #    self.model = model
        #    model.changed.connect(self.model_changed)
        #
        #  def model_changed(self):
        #    print "New value:", self.model.get_value()
        #
        #
        #model = Model(10)
        #view1 = View(model)
        #view2 = View(model)
        #view3 = View(model)
        #
        #model.set_value(20)
        #
        #del view1
        #model.set_value(30)
        #
        #model.changed.clear()
        #model.set_value(40)
        ### end of http://code.activestate.com/recipes/576477/ }}}