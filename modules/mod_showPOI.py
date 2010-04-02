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
#    # Get and set functions are used to access global data
#    self.set('num_updates', self.get('num_updates', 0) + 1)
#    #print "Updated %d times" % (self.get('num_updates'))
    pass
  
  def drawMenu(self, cr, menuName):
    if menuName == 'showPOI' or menuName == 'showPOIDetail' :
      store = self.m.get('storePOI', None)
      if store == None:
        print "showPOI: no POI storage module, quiting"
        return
      points = store.points

      menus = self.m.get('menu', None)
      if menus == None:
        return
      if menuName == 'showPOI':
        parent = 'main'
        menus.drawListableMenuControls(cr, menuName, parent)
        menus.drawListableMenuItems(cr, points, self.scroll, self.describeItem)
      if menuName == 'showPOIDetail':
        parent = 'showPOI'
        button1 = ("map#show on", "generic", "set:menu:None")
        button2 = ("tools", "generic", "set:menu:showPOIDetail")
        activePOINr = int(self.get('activePOINr', 0))
        point = points[activePOINr]
        box = (point.description, "set:menu:showPOIDetail")
        menus.drawThreePlusOneMenu(cr, menuName, parent, button1, button2, box)

  def describeItem(self, index, category, list):
    action = "set:menu:showPOIDetail"
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

  def drawMapOverlay(self, cr):
    pass

  def handleMessage(self, message):
    if(message == "up"):
      if(self.scroll > 0):
        self.scroll -= 1
    if(message == "down"):
      print "down"
      self.scroll += 1
    if(message == "reset"):
      self.scroll = 0





if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
