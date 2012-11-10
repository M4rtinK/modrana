#!/usr/bin/python
# -*- coding: utf-8 -*-
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
import os

def getModule(m,d,i):
  return tracklogManager(m,d,i)

class tracklogManager(ranaModule):
  """Module for managing tracklogs"""
  
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.scrollDict = {}
    self.currentNumItems = 0
    self.LTModule = None

  def firstTime(self):
    self.LTModule = self.m.get('loadTracklogs', None)
    # we don't know what tracklogs are available yet
    # but we don't need that to setup the categories menu
    self.setupCategoriesMenu()

  def handleMessage(self, message, type, args):
    if message in ["up","down","reset"]:
      currentCat = self.get('currentTracCat', '')
      # is scrolling index for this category set ?
      if not currentCat in self.scrollDict:
        self.scrollDict[currentCat] = 0
      # load scrolling index for category
      scroll = self.scrollDict[currentCat]
      if message == "up":
        if scroll > 0:
          scroll -= 1
          self.set("needRedraw", True)
      elif message == "down":
        if (scroll + 1) < self.currentNumItems:
          scroll += 1
          self.set("needRedraw", True)
      elif message == "reset":
        scroll = 0
        self.set("needRedraw", True)
      # save the result
      self.scrollDict[currentCat] = scroll

    elif message == 'getElevation':
      print("tracklogManage: getting elevation info for active tracklog")
      activeTracklog = self.LTModule.getActiveTracklog()
      # generate a list of (lat,lon) tuples
      latLonList = map(lambda x: (x.latitude,x.longitude), activeTracklog.trackpointsList[0])
      # look-up elevation data using Geonames asynchronously
      online = self.m.get("onlineServices",None)
      if online:
        online.elevFromGeonamesBatchAsync(latLonList, self._handleElevationLookupResults, 'geonamesBatchResults', activeTracklog)


    elif message == 'loadTrackProfile':
      # get the data needed for drawing the dynamic route profile in the osd
      track = self.LTModule.getActiveTracklog()
      self.m.get('showOSD', None).routeProfileData = track.perElevList

    elif message == 'unLoadTrackProfile':
      self.m.get('showOSD', None).routeProfileData = None

    elif message == 'askDeleteActiveTracklog':
      ask = self.m.get('askMenu', None)
      path = self.LTModule.getActiveTracklogPath()
      question = "do you really want to delete:|%s|?" % path
      yesAction = "tracklogManager:deleteActiveTracklog|set:menu:tracklogManager#tracklogManager"
      noAction = "set:menu:tracklogManager#tracklogInfo"
      ask.setupAskYesNo(question, yesAction, noAction)

    elif message == 'deleteActiveTracklog':
      path = self.LTModule.getActiveTracklogPath()
      if path:
        self.deleteTracklog(path)
        self.set('activeTracklogPath', None)

    elif message == 'setActiveTracklogToCurrentCat':
      path = self.LTModule.getActiveTracklogPath()
      currentCategory = self.get('currentTracCat', None)
      if currentCategory:
        print("changing category for:")
        print("%s" % path)
        print("to: %s" % currentCategory)
        self.LTModule.setTracklogPathCategory(path, currentCategory)

    elif message == 'setupColorMenu':
      m = self.m.get('showTracklogs', None)
      if m:
        m.setupChooseDistColorMenu('tracklogTools', '|showTracklogs:colorFromRegister|tracklogManager:setupToolsSubmenu|set:menu:tracklogTools')

    elif message == 'setupToolsSubmenu':
      self.setupToolsSubmenu()

  def getScroll(self):
    currentCat = self.get('currentTracCat', '')
    if not currentCat in self.scrollDict:
        self.scrollDict[currentCat] = 0
    return self.scrollDict[currentCat]

  def deleteTracklog(self, path):
    # delete a tracklog
    print("deleting tracklog:%s" % path)
    # from cache
    self.LTModule.deleteTrackFromCache(path)
    # from loaded tracklogs
    del self.LTModule.tracklogs[path]
    # delete the tracklog file
    os.remove(path)
    
    # relist all tracklogs
    self.LTModule.listAvailableTracklogs()

  def setupCategoriesMenu(self):
    # setup the categories menu

    menus = self.m.get("menu",None)

    # setup the category dashboard
    menu = 'tracklogManagerCategories'
    nextAction = '|set:menu:tracklogManager#tracklogManager'
    menus.clearMenu(menu, "set:menu:main")
    
    categories = self.LTModule.getCatList()
    for category in categories:
      catId = category
      text = category
      icon = "generic"
      menus.addItem(menu, text, icon, "set:currentTracCat:%s" % catId + nextAction)

    # setup the set category menu
    menu = 'tracklogSetCategory'
    nextAction = '|tracklogManager:setActiveTracklogToCurrentCat|set:menu:tracklogManager#tracklogInfo'
    menus.clearMenu(menu, "|tracklogManager:setActiveTracklogToCurrentCat|set:menu:tracklogManager#tracklogInfo")
    for category in categories:
      catId = category
      text = category
      icon = "generic"
      menus.addItem(menu, text, icon, "set:currentTracCat:%s" % catId + nextAction)

  def drawMenu(self, cr, menuName, args=None):
    # is this menu the correct menu ?
    if menuName == 'tracklogManager' or menuName == 'tracklogInfo' or menuName == 'tracklogManagerCategories':
      # setup the viewport
      menus = self.m.get("menu",None)
      (e1,e2,e3,e4,alloc) = menus.threePlusOneMenuCoords()
      (x1,y1) = e1
      (x2,y2) = e2
      (x3,y3) = e3
      (x4,y4) = e4
      (w1,h1,dx,dy) = alloc
    else:
      return # we aren't the active menu so we don't do anything

    if menuName == 'tracklogManagerCategories':
      self.setupCategoriesMenu()


    elif menuName == 'tracklogManager':

      menus = self.m.get("menu",None)

      # * draw "escape" button
      menus.drawButton(cr, x1, y1, dx, dy, "", "back", "set:menu:tracklogManagerCategories")
      # * scroll up
      menus.drawButton(cr, x2, y2, dx, dy, "", "up_list", "%s:up" % self.moduleName)
      # * scroll down
      menus.drawButton(cr, x3, y3, dx, dy, "", "down_list", "%s:down" % self.moduleName)

      # get current category
      cat = self.get('currentTracCat', '')
      list = self.LTModule.getTracPathsInCat(cat)

      # One option per row
      for row in (0,1,2):
        index = self.getScroll() + row
        numItems = len(list)
        self.currentNumItems = numItems
        if 0 <= index < numItems:

          (text1,text2,onClick) = self.describeTracklog(list[index], cat)

          y = y4 + row * dy
          w = w1 - (x4-x1)

          # Draw background and make clickable
          menus.drawButton(cr,
            x4,
            y,
            w,
            dy,
            "",
            "generic", # background for a 3x1 icon
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
      # * draw "escape" button
      menus.drawButton(cr, x1, y1, dx, dy, "", "back", "set:menu:tracklogManager#tracklogManager")
      track = self.LTModule.getActiveTracklog()
      # is there an active tracklog ?
      if track is None:
        """ there is no active tracklog,
           so we don't draw the rest of the menu
           we also don't setup the tools sub menu
           """
        return
      profile = self.m.get('routeProfile', None)

      w = w1 - (x4-x1)

      # * draw "tools" button
      menus.drawButton(cr, x2, y2, dx, dy, "tools", "tools", "set:menu:tracklogTools")

      # * draw "show button" button

      if track.trackpointsList and track.trackpointsList[0]:
        firstPoint = track.trackpointsList[0][0]
        (lat,lon) = (firstPoint.latitude, firstPoint.longitude)
        action3 = "mapView:recentre %f %f|set:showTrackFilename:%s|showTracklogs:makeVisible|set:menu:None" % (lat, lon, track.filename)
        menus.drawButton(cr, x3, y3, dx, dy, "show on map", "generic", action3)
      else:
        menus.drawButton(cr, x3, y3, dx, dy, "can't show on map#no points", "generic", 'set:menu:tracklogManager#tracklogInfo')
      # * draw "route profile"
      menus.drawButton(cr, x4, y4, w, dy, "", "generic", "set:menu:routeProfile#routeProfile")

      if track.elevation == True:
        profile.lineChart(cr, track, x4, y4, w, dy)

      # * draw an info box
      menus.drawButton(cr, x4, y4+dy, w, h1-(y4+dy), "", "generic", "set:menu:tracklogManager#tracklogInfo")

      if track.trackpointsList:
        pointCount = len(track.trackpointsList[0])
      else:
        pointCount = 0

      text = "number of points: %d\n" % pointCount
      if track.elevation == True:
        units = self.m.get('units', None)
        if units:
#          print track.routeInfo['firstElevation']
          maxString = units.m2CurrentUnitString(track.routeInfo['maxElevation'], 2, False)
          minString = units.m2CurrentUnitString(track.routeInfo['minElevation'], 2, False)
          text += "\nmaximum elevation: %s\nminimum elevation: %s" % (maxString, minString)
          text += "\nelevation of the first point: %s" % units.m2CurrentUnitString(track.routeInfo['firstElevation'], 2, False)
          text += "\nelevation of the last point: %s" % units.m2CurrentUnitString(track.routeInfo['lastElevation'], 2, False)

      menus.drawTextToSquare(cr, x4, y4+dy, w, h1-(y4+dy), text)

      self.setupToolsSubmenu()


  def setupToolsSubmenu(self):
    # setup the tools submenu
    menus = self.m.get("menu",None)
    track = self.LTModule.getActiveTracklog()
    
    # is the current track visible ?
    visibleTracklogs = self.get('visibleTracklogsDict', {})
    currentPath = self.LTModule.getActiveTracklogPath()
    isVisible = (currentPath in visibleTracklogs)

    menus.clearMenu('tracklogTools', "set:menu:tracklogManager#tracklogInfo")
    menus.addItem('tracklogTools', 'elevation#get', 'generic', 'tracklogManager:getElevation|set:menu:tracklogManager#tracklogInfo')
    menus.addItem('tracklogTools', 'active#set', 'generic', 'set:currentTrack:%s|tracklogManager:loadTrackProfile|set:menu:None' % track.filename)
    menus.addItem('tracklogTools', 'inactive#set', 'generic', 'set:currentTrack:None|tracklogManager:unLoadTrackProfile|set:menu:None')
    if isVisible:
      menus.addItem('tracklogTools', 'toggle#visible', 'generic', 'set:showTrackFilename:%s|showTracklogs:toggleVisible|tracklogManager:setupToolsSubmenu' % track.filename)
    else:
      menus.addItem('tracklogTools', 'toggle#invisible', 'generic', 'set:showTrackFilename:%s|showTracklogs:toggleVisible|tracklogManager:setupToolsSubmenu' % track.filename)
    menus.addItem('tracklogTools', 'visible#all tracks', 'generic', 'showTracklogs:allVisible|set:menu:tracklogManager#tracklogInfo')
    menus.addItem('tracklogTools', 'visible#no tracks', 'generic', 'showTracklogs:clearVisible|set:menu:tracklogManager#tracklogInfo')

    if isVisible:
      colorName = visibleTracklogs[currentPath]['colorName']
      menus.addItem('tracklogTools', 'change color#%s' % colorName, 'generic', 'tracklogManager:setupColorMenu|set:menu:chooseDistColor')


  def describeTracklog(self, item, category):
    # describe a tracklog item
    action = ""
    action += "set:activeTracklogPath:%s|loadTracklogs:loadActive|set:menu:tracklogManager#tracklogInfo" % item['path']
    name = item['filename']
    description = 'type: ' + item['type'] + '   size:' + item['size'] + '   last modified:' + item['lastModified']

    return(
      name,
      description,
      action)

  def showText(self,cr,text,x,y,widthLimit=None,fontsize=40):
    if text:
      cr.set_font_size(fontsize)
      stats = cr.text_extents(text)
      (textWidth, textHeight) = stats[2:4]

      if widthLimit and textWidth > widthLimit:
        cr.set_font_size(fontsize * widthLimit / textWidth)
        stats = cr.text_extents(text)
        (textWidth, textHeight) = stats[2:4]

      cr.move_to(x, y+textHeight)
      cr.show_text(text)

  def _handleElevationLookupResults(self, key, results):
    onlineElevList, originalTracklog = results
    if onlineElevList:
      index = 0
      for onlinePoint in onlineElevList: # add the new elevation data to the tracklog
        originalTracklog.trackpointsList[0][index].elevation = onlinePoint[2]
        index += 1
      originalTracklog.modified() # make the tracklog update
      originalTracklog.replaceFile() # replace the old tracklog file