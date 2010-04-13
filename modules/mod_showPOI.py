#!/usr/bin/python
#----------------------------------------------------------------------------
# Show POI on the map and in the menu.
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

def getModule(m,d):
  return(showPOI(m,d))

class showPOI(ranaModule):
  """Show POI on the map and in the menu."""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.scroll = 0
    
  def update(self):
    # Get and set functions are used to access global data
    self.set('num_updates', self.get('num_updates', 0) + 1)
    #print "Updated %d times" % (self.get('num_updates'))
    pass
  
  def drawMenu(self, cr, menuName):
    if menuName == 'showPOI' or menuName == 'showPOIDetail' or menuName == 'showPOIRoute':
      store = self.m.get('storePOI', None)
      if store == None:
        print "showPOI: no POI storage module, quiting"
        return
      points = store.points

      menus = self.m.get('menu', None)
      if menus == None:
        return
      if menuName == 'showPOI':
        parent = 'poi'
        menus.drawListableMenuControls(cr, menuName, parent, menuName)
        menus.drawListableMenuItems(cr, points, self.scroll, self.describeItem)
      if menuName == 'showPOIDetail':
        parent = 'showPOI'
        button1 = ("map#show on", "generic", "set:menu:None")
        button2 = ("tools", "generic", "set:menu:showPOIDetail")
        activePOINr = int(self.get('activePOINr', 0))
        point = points[activePOINr]
        text = point.description + "|coordinates: %f, %f" % (point.lat, point.lon)
        box = (text , "set:menu:showPOIDetail")
        menus.drawThreePlusOneMenu(cr, menuName, parent, button1, button2, box)
      if menuName == 'showPOIRoute':
        parent = 'poi'
        scrollMenu = 'showPOI'
        menus.drawListableMenuControls(cr, menuName, parent, scrollMenu)
        menus.drawListableMenuItems(cr, points, self.scroll, self.describeItem4Routing)


  def describeItem(self, index, category, list):
    action = "set:activePOINr:%d|set:menu:showPOIDetail" % index
#    action += "|set:searchResultsItemNr:%d" % list[index][2] # here we use the ABSOLUTE index, not the relative one

    name = "%s" % list[index].name

#    units = self.m.get('units', None)
#    distanceString = units.km2CurrentUnitString(list[index][0]) # use correct units

    if list[index].category == 'gls':
      description = "Google Local Search result"
    else:
      description = ""

    return(
      name,
      description,
      action)

  def describeItem4Routing(self, index, category, list):
    """override the default action"""
    (name, description, action) = self.describeItem(index, category, list)

    lat = list[index].lat
    lon = list[index].lon
    action = "set:selectedPos:%f,%f|route:route|set:menu:None" % (lat,lon)

    return(
      name,
      description,
      action)

  def drawMapOverlay(self, cr):
    pass

  def handleMessage(self, message):
    if(message == "up"):
      if(self.scroll > 0):
        self.scroll -= 1
        self.set('needRedraw', True)
    if(message == "down"):
      print "down"
      self.scroll += 1
      self.set('needRedraw', True)
    if(message == "reset"):
      self.scroll = 0
      self.set("needRedraw", True)





if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
