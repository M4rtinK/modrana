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
from gpod.gpod import LT_OBJDIR
from base_module import ranaModule
import math
import os

def getModule(m,d):
  return(tracklogManager(m,d))

class tracklogManager(ranaModule):
  """Module for managing tracklogs"""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.scroll = 0
    self.currentNumItems = 0
    self.LTModule = None
    self.cathegoriesSetUp = False

  def firstTime(self):
    self.LTModule = self.m.get('loadTracklogs', None)
    # we dont know what tracklogs are awailable yet
    # but we dont need that to setup the cathegories menu
    self.setupCathegoriesMenu()


    
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
    elif(message == "down"):
      if (self.scroll + 1) < self.currentNumItems:
        print "down"
        self.scroll += 1
        self.set("needRedraw", True)
    elif(message == "reset"):
      self.scroll = 0
      self.set("needRedraw", True)

    elif message == 'getElevation':
      print "getting elevation info"
      online = self.m.get("onlineServices",None)
#      loadTl = self.m.get('loadTracklogs', None) # get the tracklog module
#      loadedTracklogs = loadTl.tracklogs # get list of all tracklogs
#      index = int(self.get('activeTracklog', 0)) # get the active tracklog
      activeTracklog = self.getActiveTracklog()
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

    elif message == 'loadTrackProfile':
      # get the data needed for drawing the dynamic route profile in the osd
      filename = self.get('currentTrack', None)
#      loadTl = self.m.get('loadTracklogs', None) # get the tracklog module
#      loadedTracklogs = loadTl.tracklogs
#      track = filter(lambda x: x.tracklogFilename == filename, loadedTracklogs).pop()
      track = self.getActiveTracklog()
      self.m.get('showOSD', None).routeProfileData = track.perElevList

    elif message == 'unLoadTrackProfile':
      self.m.get('showOSD', None).routeProfileData = None

    elif message == 'askDeleteActiveTracklog':
      ask = self.m.get('askMenu', None)
      path = self.LTModule.getActiveTracklogPath()
      question = "do you really want to delete:|%s|?" % path
      yesAction = "tracklogManager:deleteActiveTracklog|set:menu:tracklogManager"
      noAction = "set:menu:tracklogInfo"
      ask.setupAskYesNo(question, yesAction, noAction)

    elif message == 'deleteActiveTracklog':
      path = self.LTModule.getActiveTracklogPath()
      if path:
        self.deleteTracklog(path)
        self.set('activeTracklog', None)


  def deleteTracklog(self, path):
    # delete a tracklog
    print "deleting tracklog:%s" % path
    # from cache
    self.LTModule.deleteTrackFromCache(path)
    # from loaded tracklogs
    del self.LTModule.tracklogs[path]
    # delete the tracklog file
    os.remove(path)
    
    # relist all tracklogs
    self.LTModule.listAvailableTracklogs()

  def setDefaultCathegories(self):
    # set a default set of cathegories and return it
    defaultCathegories = [('misc',"misc",'generic'),
                          ('online',"online",'generic'),
                          ('log',"logs",'generic')
                          ]
    self.set('tracklogCathegories', defaultCathegories)
    return defaultCathegories


  def setupCathegoriesMenu(self):
    # setup the cathegories menu
    menus = menus = self.m.get("menu",None)
    cathegories = self.get('tracklogCathegories', None)
    if cathegories == None:
      cathegories = self.setDefaultCathegories()
    menu = 'tracklogManagerCathegories'

    menus.clearMenu(menu, "set:menu:main")
    for cathegory in cathegories:
      catId = cathegory[0]
      text = cathegory[1]
      icon = cathegory[2]
      menus.addItem(menu, text, icon, "set:currentTracCat:%s|set:menu:tracklogManager" % catId)

  def drawMenu(self, cr, menuName):
    # is this menu the correct menu ?
    if menuName == 'tracklogManager' or menuName == 'tracklogInfo' or menuName == 'tracklogManagerCathegories':
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

    if menuName == 'tracklogManagerCathegories':
      if not self.cathegoriesSetUp:
        self.setupCathegoriesMenu()
        self.cathegoriesSetUp = True

    elif menuName == 'tracklogManager':
      # are there any tracklogs in the tracklog folder ?
      if self.LTModule.tracklogList == None:
        # list available tracklogs
        self.LTModule.listAvailableTracklogs()

      menus = self.m.get("menu",None)

      # * draw "escape" button
      menus.drawButton(cr, x1, y1, dx, dy, "", "up", "set:menu:tracklogManagerCathegories")
      # * scroll up
      menus.drawButton(cr, x2, y2, dx, dy, "", "up_list", "%s:up" % self.moduleName)
      # * scroll down
      menus.drawButton(cr, x3, y3, dx, dy, "", "down_list", "%s:down" % self.moduleName)

      cathegory = self.get('currentTracCat', 'misc')
      print cathegory
      list = filter(lambda x: x['cat'] == cathegory, self.LTModule.tracklogList)

      # One option per row
      for row in (0,1,2):
        index = self.scroll + row
        numItems = len(list)
        self.currentNumItems = numItems
        if(0 <= index < numItems):

          (text1,text2,onClick) = self.describeTracklog(list[index], cathegory)

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

          self.showText(cr, text1, x4+border, y+2*border, w-3*border)

          # 2nd line: current value
          self.showText(cr, text2, x4 + 0.1 * w, y + 0.65 * dy, w * 0.87 - border)

          # in corner: row number
          self.showText(cr, "%d/%d" % (index+1, numItems), x4+0.85*w, y+border, w * 0.15 - border, 20)
      return

    elif menuName == 'tracklogInfo':
      menus = self.m.get("menu",None)
      track = self.getActiveTracklog()
      profile = self.m.get('routeProfile', None)

      w = w1 - (x4-x1)

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

      if track.elevation == True:
        profile.lineChart(cr, track, x4, y4, w, dy)

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
      menus.addItem('tracklogTools', 'active#set', 'generic', 'set:currentTrack:%s|tracklogManager:loadTrackProfile|set:menu:None' % track.tracklogFilename)
      menus.addItem('tracklogTools', 'inactive#set', 'generic', 'set:currentTrack:None|tracklogManager:unLoadTrackProfile|set:menu:None')
      menus.addItem('tracklogTools', 'visible#all tracks', 'generic', 'showGPX:allVisible|set:menu:tracklogInfo')
      menus.addItem('tracklogTools', 'visible#no tracks', 'generic', 'showGPX:inVisible|set:menu:tracklogInfo')
      menus.addItem('tracklogTools', 'tracklog#delete', 'generic', 'tracklogManager:askDeleteActiveTracklog')


#      online = self.m.get('onlineServices', None)
#      online.getGmapsInstance()


  def getActiveTracklog(self):
    path = self.LTModule.getActiveTracklogPath()
    if path not in self.LTModule.tracklogs:
      self.LTModule.loadTracklog(path)
      self.LTModule.save()
    return self.LTModule.tracklogs[path]


  def describeTracklog(self, item, category):
    # describe a tracklog item
    action = ""
    action += "set:activeTracklog:%s|loadTracklogs:loadActive|set:menu:tracklogInfo" % item['index']
#    action += "|set:menu:poi"
    name = item['filename']
    description = 'type: ' + item['type'] + '   size:' + item['size'] + '   last modified:' + item['lastModified']

    return(
      name,
      description,
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
