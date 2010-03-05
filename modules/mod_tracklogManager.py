#!/usr/bin/python
#----------------------------------------------------------------------------
# Module for managing tracklogs.
#----------------------------------------------------------------------------
# Copyright 2010, Martin Kolman
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
import math

def getModule(m,d):
  return(tracklogManager(m,d))

class tracklogManager(ranaModule):
  """Module for managing tracklogs"""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.scroll = 0
    
  def update(self):
    # Get and set functions are used to access global data
    self.set('num_updates', self.get('num_updates', 0) + 1)
    #print "Updated %d times" % (self.get('num_updates'))

  def handleMessage(self, message):
    if(message == "up"):
      if(self.scroll > 0):
        self.scroll -= 1
    if(message == "down"):
      self.scroll += 1
    if(message == "reset"):
      self.scroll = 0
    self.set("needRedraw", True)

  def drawMenu(self, cr, menuName):
    # is this menu the correct menu ?
    if menuName != 'tracklogManager':
      return # we arent the active menu so we dont do anything
    (x1,y1,w,h) = self.get('viewport', None)
    menus = self.m.get("menu",None)
    loadTl = self.m.get('loadTracklog', None) # get the tracklog module
    loadedTracklogs = loadTl.tracklogs # get list of all tracklogs
#    tracklistsWithElevation = filter(lambda x: x.elevation == True, loadedTracklogs)
#    tracklog = tracklistsWithElevation[0].trackpointsList[0]

#    if w > h:
#      cols = 4
#      rows = 3
#    elif w < h:
#      cols = 3
#      rows = 4
#    elif w == h:
#      cols = 4
#      rows = 4
#
#    dx = w / cols
#    dy = h / rows

    dx = w / 3
    dy = h / 4
    # * draw "escape" button
    menus.drawButton(cr, x1, y1, dx, dy, "", "up", "set:menu:main")
    # * scroll up
    menus.drawButton(cr, x1+dx, y1, dx, dy, "", "up_list", "%s:up" % self.moduleName)
    # * scroll down
    menus.drawButton(cr, x1+2*dx, y1, dx, dy, "", "down_list", "%s:down" % self.moduleName)

    loadTl = self.m.get('loadTracklog', None) # get the tracklog module
    loadedTracklogs = loadTl.tracklogs # get list of all tracklogs
    list = loadedTracklogs
    category = ""
#    describeFunction = self.describeTracklog(self, item, category, index)


    # One option per row
    for row in (0,1,2):
      index = self.scroll + row
      numItems = len(list)
      if(0 <= index < numItems):

        (text1,text2,onClick) = self.describeTracklog(list[index], category, loadedTracklogs)

        y = y1 + (row+1) * dy

        # Draw background and make clickable
        menus.drawButton(cr,
          x1,
          y,
          w,
          dy,
          "",
          "3h", # background for a 3x1 icon
          onClick)

        border = 20

        self.showText(cr, text1, x1+border, y+border, w-2*border)

        # 2nd line: current value
        self.showText(cr, text2, x1 + 0.15 * w, y + 0.6 * dy, w * 0.85 - border)

        # in corner: row number
        self.showText(cr, "%d/%d" % (index+1, numItems), x1+0.85*w, y+border, w * 0.15 - border, 20)
    return

  def describeTracklog(self, item, category, loadedTracklogs):
#    longName = name = item.getTracklogName()
#    print filter(lambda x: x.getTracklogName() == longName, loadedTracklogs)
#    print loadedTracklogs.index(item)


    action = "set:menu:main"
#    action += "|set:menu_poi_location:%f,%f" % (item['lat'], item['lon'])
    action += "|set:activeTracklog:%d" % loadedTracklogs.index(item)
#    action += "|set:menu:poi"
    name = item.getTracklogName().split('/').pop()
    elevation = ""
    if item.elevation == True:
      elevation = "elevation available"
    else:
      elevation = "no elevation data"

    return(
      name,
      elevation,
      action)

  def showText(self,cr,text,x,y,widthLimit=None,fontsize=40):
    if(text):
      cr.set_font_size(fontsize)
      stats = cr.text_extents(text)
      (textwidth, textheight) = stats[2:4]

      if(widthLimit and textwidth > widthLimit):
        cr.set_font_size(fontsize * widthLimit / textwidth)
        stats = cr.text_extents(text)
        (textwidth, textheight) = stats[2:4]

      cr.move_to(x, y+textheight)
      cr.show_text(text)


if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
