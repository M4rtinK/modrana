#!/usr/bin/python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# A modRana module providing various kinds of information.
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
import os

def getModule(m,d,i):
  return(info(m,d,i))

class info(ranaModule):
  """A modRana information handling module"""
  
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.versionString = "unknown version"
    currentVersionString = self.modrana.paths.getVersionString()
    if currentVersionString is not None:
      # check version string validity
      self.versionString = currentVersionString

  def getPayPalUrl(self):
    return "https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=martin%2ekolman%40gmail%2ecom&lc=CZ&item_name=The%20modRana%20project&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donate_LG%2egif%3aNonHosted"

  def getDiscussionUrls(self):
    return [("http://talk.maemo.org/showthread.php?t=58861","Discussion@TMO")]

  def drawMenu(self, cr, menuName, args=None):
    if menuName == 'infoAbout':
      menus = self.m.get('menu', None)
      if menus:
        nop = "set:menu:info#infoAbout"
        button1 = ('Discussion', 'generic', "ms:menu:openUrl:%s" % self.getDiscussionUrls()[0][0])
        button2 = ('Donate', 'generic', "ms:menu:openUrl:%s" % self.getPayPalUrl())
        web = " <u>www.modrana.org</u> "
        email = " modrana@gmail.com "
        text = "modRana version:\n\n%s\n\n\n\nFor questions or feedback,\n\ncontact the <b>modRana</b> project:\n\n%s\n\n%s\n\n" % (self.versionString,web,email)
        box = (text ,"ms:menu:openUrl:http://www.modrana.org")
        menus.drawThreePlusOneMenu(cr, 'infoAbout', 'set:menu:info', button1, button2, box)

if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
