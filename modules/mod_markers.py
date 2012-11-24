# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# A module handling markers on the map.
#----------------------------------------------------------------------------
# Copyright 2011, Martin Kolman
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
from modules.base_module import RanaModule
import math
from core import geo
from core.color import Color

def getModule(m,d,i):
  return Markers(m,d,i)

class Markers(RanaModule):
  """A module handling markers on the map."""
  
  def __init__(self, m, d, i):
    RanaModule.__init__(self, m, d, i)
    self.groups = {} # marker groups

  def addGroup(self, name, points, menu=False):
    """the name must be unique,
    if it isn't the previous similarly named group is overwritten
    points is a list of point objects"""
    g = PointGroup(points)
    if menu:
      g.setMenuEnabled(menu)
      menus = self.m.get('menu', None)
      if menus:
        menu = menus.addPointListMenu(name, "set:menu:None", points, goto="map")
        g.setMenuInstance(menu)
    self.groups[name] = g
    return g

  def removeGroup(self,name):
    """remove a group by name
    return True if a group was removed and False if it wasn't due to
    not being found"""
    if name in self.groups.keys():
      del self.groups[name]
      return True
    else:
      return False

  def getGroup(self,name):
    if name in self.groups.keys():
      return self.groups[name]
    else:
      return None

  def groupExists(self, name):
    """return if a group with a given name exists"""
    return name in self.groups.keys()

  def clearAll(self):
    self.groups = {}

  def drawMapOverlay(self, cr):
    if self.groups:
      pos = self.get('pos', None)
      units = self.m.get('units', None)
      proj = self.m.get('projection', None)
      crPosUnitsProj = (cr, pos, units, proj)
      for key in self.groups.keys(): # draw all groups
        group = self.groups[key]
        menu = group.getMenuEnabled()
        colors = group.getColors()

        index = 0
        for point, highlight in group.getPoints(): # draw all points in group
          if menu:
            """key contains the point group name, it should be the same
            as the corresponding listable menu name"""
            action="set:menu:menu#listDetail#%s#%d" % (key, index)
          else:
            action=""
          if highlight:
            self._drawPoint(crPosUnitsProj, point, colors, action=action, highlight=True)
          else:
            self._drawPoint(crPosUnitsProj, point, colors, action=action)
          index+=1

  def _drawPoint(self, crPosUnitsProj, point, colors, distance=True, action="", highlight=False):
    (cr, pos, units, proj) = crPosUnitsProj
    (lat,lon) = point.getLL() #TODO use getLLE for 3D distance
    (lat1,lon1) = pos # current position coordinates
    kiloMetricDistance = geo.distance(lat,lon,lat1,lon1)
    unitString = units.km2CurrentUnitString(kiloMetricDistance, 0, True)
    if distance and pos and units:
      distanceString = " (%s)" % unitString
    else:
      distanceString=""

    text = "%s%s" % (point.getName(), distanceString)

    (x,y) = proj.ll2xy(lat, lon)
    # get colors
    (bgColor,textColor) = colors

    if highlight:
      # draw the highlighting circle
      cr.set_line_width(8)
      cr.set_source_rgba(*bgColor.getCairoColor()) # highlight circle color
      cr.arc(x, y, 15, 0, 2.0 * math.pi)
      cr.stroke()
      cr.fill()

    # draw the point
    cr.set_source_rgb(0.0, 0.0, 0.0)
    cr.set_line_width(10)
    cr.arc(x, y, 3, 0, 2.0 * math.pi)
    cr.stroke()
    cr.set_source_rgb(0.0, 0.0, 1.0)
    cr.set_line_width(8)
    cr.arc(x, y, 2, 0, 2.0 * math.pi)
    cr.stroke()

    # draw a caption with transparent background
    cr.set_font_size(25)
    extents = cr.text_extents(text) # get the text extents
    (w,h) = (extents[2], extents[3])
    border = 2
    cr.set_line_width(2)

    cr.set_source_rgba(*bgColor.getCairoColor()) # trasparent blue
    (rx,ry,rw,rh) = (x - border+12, y + border+h*0.2 + 6, w + 4*border, -(h*1.4))
    cr.rectangle(rx,ry,rw,rh) # create the transparent background rectangle
    cr.fill()

    # register clickable area
    click = self.m.get('clickHandler', None)
    if click:
      """ make the POI caption clickable"""
      click.registerXYWH(rx,ry-(-rh),rw,-rh, action)
    cr.fill()

    # draw the actual text
    cr.set_source_rgba(*textColor.getCairoColor()) # slightly transparent white
    cr.move_to(x+15,y+7)
    cr.show_text(text) # show the transparent result caption
    cr.stroke()

class PointGroup():
  def __init__(self, points=None, bgColor=Color("bg", ("blue", 0.45)), textColor=Color("bg", ("white", 0.95))):
    if not points: points = []
    self.points = []
    for point in points:
      self.points.append((point,False))
    self.bgColor = bgColor
    self.textColor = textColor
    self.menu=False
    self.menuInstance = None

  def getBBox(self):
    """report a bounding box for all points"""
    pass

  def getPoints(self):
    """return a list of included points"""
    return self.points

  def getColors(self):
    return self.bgColor, self.textColor

  def highlightPoint(self, id):
    try:
      self.points[id][1] = True
    except Exception, e:
      print("markers: highlight index out of range: %r" % id)
      print e

  def unhighlightAll(self):
    for tuple in self.points:
      tuple[1] = False

  def setMenuEnabled(self, value):
    self.menu = value

  def getMenuEnabled(self):
    """is menu for this point group enabled or disabled"""
    return self.menu

  def setMenuInstance(self, menu):
    self.menuInstance = menu

  def getMenuInstance(self):
    return self.menuInstance

  def setInitialBackAction(self, action):
        """this action will be used if the corresponding marker group menu is
    entered for the first time without selecting any items,
    once an item is selected, the back action reverts to "set:menu:None",
    eq. returning to the map screen
    USE CASE: quick returning from search results back to the search menu
              to start another search
    """




