#!/usr/bin/python
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Handles messages between modules (in response to clicks etc)
#---------------------------------------------------------------------------
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
from base_module import ranaModule
import sys
import os
import socket
from time import sleep
import re

def getModule(m,d,i):
  return(messageModule(m,d,i))

class messageModule(ranaModule):
  """Handles messages"""
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)

  def routeMessage(self, messages):
    for message in messages.split('|'):
      try:
        (module, text) = message.split(":", 1)
      except ValueError: # no module name or keyword found
        return

      if module == 'set':
        (key,value) = text.split(":", 1)
        for i in(None, True, False):
          if value == str(i):
            value = i
        self.set(key, value)
        
      elif module == 'toggle':
        self.set(text, not self.get(text,0))

      elif module == "*": # send to all modules
        for m in self.m.items():
          m.handleMessage(text)

      elif module == 'ms': # short for message + single simple string
        (module, key, string) = text.split(':', 2)
        m = self.m.get(module, None)
        if m is not None:
          m.handleMessage(key,'ms',string)
        else:
          print "Message addressed to %s which isn't loaded" % module

      elif module == 'ml': # short for message + list of strings
        tokens = text.split(':', 2)
        module = tokens[0]
        key = tokens[1]
        semicolonSepList = tokens[2]
        list = semicolonSepList.split(';')
        m = self.m.get(module, None)
        if m is not None:
          m.handleMessage(key,'ml',list)
        else:
          print "Message addressed to %s which isn't loaded" % module

      elif module == 'md': # short for message + dictionary of string:string key:value pairs
        tokens = text.split(':', 3)
        module = tokens[0]
        mainKey = tokens[1]
        semicolonSepDict = tokens[2]
        d = {}
        for keyValue in semicolonSepDict.split(';'):
          kvList = keyValue.split('=',1)
          if len(kvList)>=2:
            (key,value) = (kvList[0],kvList[1])
            d[key] = value
        m = self.m.get(module, None)
        if m is not None:
          m.handleMessage(mainKey,'md',d)
        else:
          print "Message addressed to %s which isn't loaded" % module

      elif module == "setWithMode":
        (mode, key, value) = text.split(":", 2)
        for i in(None, True, False):
          if value == str(i):
            value = i
        self.set(key, value, mode=mode)

      else:
        m = self.m.get(module, None)
        if m is not None:
          m.handleMessage(text, None, None)
        else:
          print "Message addressed to %s which isn't loaded" % module