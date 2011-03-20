#!/usr/bin/python
#----------------------------------------------------------------------------
# This module provides notification support.
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
from base_module import ranaModule
import time

def getModule(m,d,i):
  return(notification(m,d,i))

class notification(ranaModule):
  """This module provides notification support."""
  
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.notificationText = ""
    self.timeout = 5
    self.position = 'middle'
    self.expirationTimestamp = time.time()
    self.draw = False
    self.redrawn = None
    self.backgroundWorkNotify = False
    """this indicates if the notification about background processing should be shown"""

  def handleMessage(self, message, type, args):
    """the first part is the message, that will be displayed,
       there can also by some parameters, delimited by #
       NEW: you can also use a message list for the notification
            fitst goes the message, then the timeout in seconds
       """

    if type=='ml' and message=='m':
      """advanced message list based notification"""
      if args:
        if self.dmod: # if some module sends a notification during init, the device module might not be loaded
          if self.dmod.hasNativeNotificationSupport(): # use platform specific method
            timeout = self.timeout
            if len(args) >= 2:
              timeout=int(args[1])
            notificationText = args[0]
            self.dmod.notify(notificationText,timeout*1000)
            print "timeout",timeout*1000
        else:
          timeout = self.timeout
          self.position = 'middle'
          self.notificationText = args[0]
          self.draw = True # enable drawing of notifications
          if len(args) >= 2:
            timeout=int(args[1])
            self.expirationTimestamp = time.time() + timeout

          self.set('needRedraw', True) # make sure the notification is displayed
    elif type=='ml' and message=='backgroundWorkNotify':
      if args:
        if args[0] == "enable":
          self.backgroundWorkNotify = True
        if args[0] == "disable":
          self.backgroundWorkNotify = False
    else:
      list = message.split('#')
      if self.dmod: # if some module sends a notification during init, the device module might not be loaded
        if self.dmod.hasNativeNotificationSupport():  # use platform specific method
          timeout = self.timeout
          if len(list) == 2:
            try:
              timeout = int(list[1]) # override the default timeout
            except:
              print "notification: wrong timeout, using default 5 secconds"
          notificationText = list[0]

          self.dmod.notify(notificationText,timeout*1000)
      else:
        timeout = self.timeout
        self.position = 'middle'
        self.notificationText = list[0]
        self.draw = True # enable drawing of notifications
        if len(list) == 2:
          try:
            timeout = int(list[1]) # override the default timeout
          except:
            print "notification: wrong timeout, using default 5 secconds"
        self.expirationTimestamp = time.time() + timeout
        self.set('needRedraw', True) # make sure the notification is displayed


  def drawMasterOverlay(self,cr):
    """this function is called by the menu module, both in map mode and menu mode
    -> its bit of a hack, but we can """
    self.drawNotification(cr)
    if self.backgroundWorkNotify:
      online = self.m.get('onlineServices', None)
      if online:
        online.drawOpInProgressOverlay(cr)

  def drawNotification(self, cr):
    """Draw the notifications on the screen on top of everything."""
    timestamp = time.time()
    expirationTimestamp = self.expirationTimestamp
    if timestamp <= expirationTimestamp:
      proj = self.m.get('projection', None)
      (x1,y1) = proj.screenPos(0.5, 0.5) # middle fo the screen
      cr.set_font_size(30)
      text = self.notificationText
      cr.set_source_rgba(0, 0, 1, 0.45) # trasparent blue
      extents = cr.text_extents(text)
      (w,h) = (extents[2], extents[3])
      (x,y) = (x1-w/2.0,y1-h/2.0)
      cr.set_line_width(2)
      cr.set_source_rgba(0, 0, 1, 0.45) # trasparent blue
      (rx,ry,rw,rh) = (x-0.25*w, y-h*1.5, w*1.5, (h*2))
      cr.rectangle(rx,ry,rw,rh) # create the transparent background rectangle
      cr.fill()
      cr.set_source_rgba(1, 1, 1, 0.95) # slightly trasparent white
      cr.move_to(x+10,y)
      cr.show_text(text) # show the trasparent notification text
      cr.stroke()
      cr.fill()
    else:
      self.draw = False # we are finished, disable drawing notifications

if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
