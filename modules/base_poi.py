#!/usr/bin/python
#---------------------------------------------------------------------------
# Base class for any module which displays points of interest
#---------------------------------------------------------------------------
# Copyright 2008, Oliver White
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

class poiModule(ranaModule):
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.poi = {}
    self.needUpdate = False
    self.scroll = 0

  def handleMessage(self, message, type, args):
    if(message == "up"):
      if(self.scroll > 0):
        self.scroll -= 1
        self.set("needRedraw", True)
    if(message == "down"):
      self.scroll += 1
      self.set("needRedraw", True)
    if(message == "reset"):
      self.scroll = 0
      self.set("needRedraw", True)
    self.set("needRedraw", True)

  def describePlaintext(self, item, category,index):
    return(item, "", "")

  def describePoi(self, item, category, index):
    action = "set:menu_poi_category:%s" % category
    action += "|set:menu_poi_location:%f,%f" % (item['lat'], item['lon'])
    action += "|set:menu_poi_item:%d" % index
    action += "|set:menu:poi"
    
    return(
      item['name'],
      "%1.1f km away" % (item['d']),
      action)
  
  def describeCategory(self, item, category, index):
    action = "set:menu:%s_cat_%s" % (self.moduleName, item)
    action += "|%s:reset" % self.moduleName
    return(item, "", action)
  
  def drawList2(self, cr, list, describeFunction, category=None):
    # Find the screen
    if not self.d.has_key('viewport'):
      return
    (x1,y1,w,h) = self.get('viewport', None)



#    if w > h:
#      dx = w / 4
#      dy = h / 4
#    elif w < h:
#      dx = w / 3
#      dy = h / 4
#    elif w == h:
#      dx = w / 4
#      dy = h / 4

    dx = w / 3
    dy = h / 4

    menus = self.m.get("menu",None)
    if(menus):
      # Top row:
#      # * parent menu
#      menus.drawButton(cr, x1, y1, dx, dy, "", "up", "set:menu:%s_categories" % self.moduleName)
      # * main menu for now
      menus.drawButton(cr, x1, y1, dx, dy, "", "up", "set:menu:main")
      # * scroll up
      menus.drawButton(cr, x1+dx, y1, dx, dy, "", "up_list", "%s:up" % self.moduleName)
      # * scroll down
      menus.drawButton(cr, x1+2*dx, y1, dx, dy, "", "down_list", "%s:down" % self.moduleName)

      # One option per row
      for row in (0,1,2):
        index = self.scroll + row
        numItems = len(list)
        if(0 <= index < numItems):

          (text1,text2,onClick) = describeFunction(list[index], category, index)

          y = y1 + (row+1) * dy
          
          # Draw background and make clickable
          menus.drawButton(cr,
            x1,
            y,
            w,
            dy,
            "",
            "generic", # background for a 3x1 icon
            onClick)

          border = 20

          self.showText(cr, text1, x1+border, y+border, w-2*border)

          # 2nd line: current value
          self.showText(cr, text2, x1 + 0.15 * w, y + 0.6 * dy, w * 0.85 - border)

          # in corner: row number
          self.showText(cr, "%d/%d" % (index+1, numItems), x1+0.85*w, y+border, w * 0.15 - border, 20)

            
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
      
  def drawMenu(self, cr, menuName):
    l = len(self.moduleName)
    if(menuName[0:l] != self.moduleName):
      return
    menuName = menuName[l:]

    if(menuName == "_categories"):
      self.drawList2(cr, self.poi.keys(), getattr(self,"describeCategory"))

    elif(menuName[0:5] == "_cat_"):
      category = menuName[5:]

      items = self.poi[category]
      
      items.sort(lambda x, y: int(x.get('d',1E+5)) - int(y.get('d',1E+5)))
      
      self.drawList2(cr, items, getattr(self,"describePoi"), category)

    
  def addItem(self, type, name, lat, lon):
    item = {'name':name, 'lat':float(lat),'lon':float(lon)}
    self.poi[type].append(item)

  def updatePoi(self):
    """Update distances etc. to each POI"""
    if(not self.needUpdate):
      return
    
    pos = self.get("pos", None)
    if(pos == None):
      return(False)

    (ownlat, ownlon) = pos
    degToKm = 40041.0 / 360.0
    for type,items in self.poi.items():
      for item in items:
        dlon = item['lon'] - ownlon
        dlat = item['lat'] - ownlat
        dlon *= math.cos(math.radians(ownlat))

        item['d'] = math.sqrt(dlon * dlon + dlat * dlat) * degToKm
        
    self.needUpdate = False

