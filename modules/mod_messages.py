#!/usr/bin/python
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

def getModule(m,d):
  return(messageModule(m,d))

class messageModule(ranaModule):
  """Handles messages"""
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)

  def routeMessage(self, messages):
    for message in messages.split('|'):
      (module, text) = message.split(":", 1)
      
      if(module == 'set'):
        (key,value) = text.split(":", 1)
        for i in(None, True, False):
          if(value == str(i)):
            value = i
        self.set(key, value)
        
      elif(module == 'toggle'):
        self.set(text, not self.get(text,0))
      elif(module == "*"):
        for m in self.m.items():
          m.handleMessage(text)
      else:
        m = self.m.get(module, None)
        if(m != None):
          m.handleMessage(text)
        else:
          print "Message addressed to %s which isn't loaded" % module