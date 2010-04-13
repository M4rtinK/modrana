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
    print "handling"
    if(message == "up"):
      if(self.scroll > 0):
        self.scroll -= 1
        self.set("needRedraw", True)
    if(message == "down"):
      print "down"
      self.scroll += 1
      self.set("needRedraw", True)
    if(message == "reset"):
      self.scroll = 0
      self.set("needRedraw", True)

    if message == 'getElevation':
      print "getting elevation info"
      online = self.m.get("onlineServices",None)
      loadTl = self.m.get('loadTracklogs', None) # get the tracklog module
      loadedTracklogs = loadTl.tracklogs # get list of all tracklogs
      index = int(self.get('activeTracklog', 0)) # get the active tracklog
      activeTracklog = loadedTracklogs[index]
      # generate a list of (lat,lon) tupples
      latLonList = map(lambda x: (x.latitude,x.longitude), activeTracklog.trackpointsList[0])
      # this method returns (lat,lon, elev) tupples, where the elev comes from an online service
      onlineElevList = online.elevFromGeonamesBatch(latLonList)
      index = 0
      for onlinePoint in onlineElevList: # add the new elevation data to the tracklog
        activeTracklog.trackpointsList[0][index].elevation = onlinePoint[2]
        index = index + 1
      activeTracklog.modified() # make the tracklog update
      activeTracklog.replaceFile() # replace the old tracklog file

  def drawMenu(self, cr, menuName):
    # is this menu the correct menu ?
    if menuName == 'tracklogManager' or menuName == 'tracklogInfo':
      # setup the viewport
      menus = self.m.get("menu",None)
      (e1,e2,e3,e4,alloc) = menus.threePlusOneMenuCoords()
      (x1,y1) = e1
      (x2,y2) = e2
      (x3,y3) = e3
      (x4,y4) = e4
      (w1,h1,dx,dy) = alloc
    else:
      return # we arent the active menu so we dont do anything


    if menuName == 'tracklogManager':
      menus = self.m.get("menu",None)
      loadTl = self.m.get('loadTracklogs', None) # get the tracklog module
      loadedTracklogs = loadTl.tracklogs # get list of all tracklogs
  #    tracklistsWithElevation = filter(lambda x: x.elevation == True, loadedTracklogs)
  #    tracklog = tracklistsWithElevation[0].trackpointsList[0]

      # * draw "escape" button
      menus.drawButton(cr, x1, y1, dx, dy, "", "up", "set:menu:main")
      # * scroll up
      menus.drawButton(cr, x2, y2, dx, dy, "", "up_list", "%s:up" % self.moduleName)
      # * scroll down
      menus.drawButton(cr, x3, y3, dx, dy, "", "down_list", "%s:down" % self.moduleName)

      loadTl = self.m.get('loadTracklogs', None) # get the tracklog module
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

#          y = y1 + (row+1) * dy
          y = y4 + (row) * dy
          w = w1 - (x4-x1)

          # Draw background and make clickable
          menus.drawButton(cr,
            x4,
            y,
            w,
            dy,
            "",
            "3h", # background for a 3x1 icon
            onClick)

          border = 20

          self.showText(cr, text1, x4+border, y+border, w-2*border)

          # 2nd line: current value
          self.showText(cr, text2, x4 + 0.15 * w, y + 0.6 * dy, w * 0.85 - border)

          # in corner: row number
          self.showText(cr, "%d/%d" % (index+1, numItems), x4+0.85*w, y+border, w * 0.15 - border, 20)
      return

    elif menuName == 'tracklogInfo':
#      print "tracklogInfo"
      menus = self.m.get("menu",None)
      loadTl = self.m.get('loadTracklogs', None) # get the tracklog module
      loadedTracklogs = loadTl.tracklogs # get list of all tracklogs
      index = int(self.get('activeTracklog', 0)) # get the active tracklog
      activeTracklog = loadedTracklogs[index]
      profile = self.m.get('routeProfile', None)

      w = w1 - (x4-x1)

      track = activeTracklog

      # * draw "escape" button
      menus.drawButton(cr, x1, y1, dx, dy, "", "up", "set:menu:tracklogManager")
      # * draw "tools" button
      menus.drawButton(cr, x2, y2, dx, dy, "tools", "generic", "set:menu:tracklogTools")
      # * draw "show button" button
      firstPoint = track.trackpointsList[0][0]
      (lat,lon) = (firstPoint.latitude, firstPoint.longitude)
      action3 = "mapView:recentre %f %f|set:showTrackFilename:%s|showGPX:toggleVisible|set:menu:None" % (lat, lon, track.tracklogFilename)
      menus.drawButton(cr, x3, y3, dx, dy, "show on map", "generic", action3)
      # * draw "route profile"
      menus.drawButton(cr, x4, y4, w, dy, "", "box480", "set:menu:routeProfile")

      if activeTracklog.elevation == True:
        profile.lineChart(cr, activeTracklog, x4, y4, w, dy)

      # * draw an info box
      menus.drawButton(cr, x4, y4+dy, w, h1-(y4+dy), "", "3h", "set:menu:tracklogInfo")

      text = "number of points: %d|" % len(track.trackpointsList[0])
      if track.elevation == True:
        text += "|maximum elevation: %d meters|minimum elevation: %d meters" % (track.routeInfo['maxElevation'], track.routeInfo['minElevation'])
        text += "|elevation of the first point: %d meters" % track.routeInfo['firstElevation']
        text += "|elevation of the last point: %d meters" % track.routeInfo['lastElevation']

      menus.drawTextToSquare(cr, x4, y4+dy, w, h1-(y4+dy), text)


      # set up the tools submenu
      menus.clearMenu('tracklogTools', "set:menu:tracklogInfo")
      menus.addItem('tracklogTools', 'elevation#get', 'generic', 'tracklogManager:getElevation|set:menu:tracklogInfo')
      menus.addItem('tracklogTools', 'visible#toggle', 'generic', 'set:showTrackFilename:%s|showGPX:toggleVisible|set:menu:tracklogInfo' % track.tracklogFilename)
      menus.addItem('tracklogTools', 'visible#all tracks', 'generic', 'showGPX:allVisible|set:menu:tracklogInfo')
      menus.addItem('tracklogTools', 'visible#no tracks', 'generic', 'showGPX:inVisible|set:menu:tracklogInfo')


#      online = self.m.get('onlineServices', None)
#      online.getGmapsInstance()




  def describeTracklog(self, item, category, loadedTracklogs):
#    longName = name = item.getTracklogName()
#    print filter(lambda x: x.getTracklogName() == longName, loadedTracklogs)
#    print loadedTracklogs.index(item)


#    action = "set:menu:main"
    action = ""
#    action += "|set:menu_poi_location:%f,%f" % (item['lat'], item['lon'])
    action += "set:activeTracklog:%d|set:menu:tracklogInfo" % loadedTracklogs.index(item)
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
