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
from modules.base_module import ranaModule
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

  def getFlattrUrl(self):
    return "https://flattr.com/thing/678708/modRana-flexible-GPS-navigation-system"

  def getBitcoinAddress(self):
    return "14DXzkqqYCfSG5vZNYPnPiZzg3wW2hXsE8"

  def getDiscussionUrls(self):
    """
    return a list of modRana-relevant discussions, with the most relevant discussion on top
    """
    return [("http://talk.maemo.org/showthread.php?t=58861","talk.maemo.org thread")]

  def getMainDiscussionUrl(self):
    """
    return Url to the most relevant modRana discussion
    """
    return self.getDiscussionUrls()[0]

  def getWebsiteUrl(self):
    """
    return Url to the modRana website
    """
    return "http://www.modrana.org"

  def getSourceRepositoryUrl(self):
    return "https://github.com/M4rtinK/modrana"

  def getEmailAddress(self):
    """
    return the project email address
    """
    return "modrana@gmail.com"

  def getAboutText(self):
    www = self.getWebsiteUrl()
    email = self.getEmailAddress()
    source = self.getSourceRepositoryUrl()
    discussion, name = self.getDiscussionUrls()[0]
    text= "<p><b>main developer:</b> Martin Kolman</p>"
    text+= '<p><b>email</b>: <a href="mailto:%s">%s</a></p>' % (email, email)
    text+= '<p><b>www</b>: <a href="%s">%s</a></p>' % (www, www)
    text+= '<p><b>source</b>:\n<a href="%s">%s</a></p>' % (source, source)
    text+= '<p><b>discussion</b>: check <a href="%s">%s</a></p>' % (discussion, name)
    return text

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
