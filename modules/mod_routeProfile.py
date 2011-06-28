#!/usr/bin/python
#----------------------------------------------------------------------------
# Creates a route profile (an elevation chart)
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
import pycha.line
import cairo
import geo

def getModule(m,d,i):
  return(routeProfile(m,d,i))

class routeProfile(ranaModule):
  """Creates a route profile (an elevation chart)"""
  
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)

  def drawMenu(self, cr, menuName):
    #print menuName
    # is this menu the correct menu ?
    if menuName != 'routeProfile':
      return # we arent the active menu so we dont do anything
    (x1,y1,w,h) = self.get('viewport', None)
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

    dx = min(w,h) / 5.0
    dy = dx

    menus = self.m.get("menu",None)
    loadTl = self.m.get('loadTracklogs', None) # get the tracklog module
    tracklog = loadTl.getActiveTracklog()
    if tracklog.elevation == True:
      self.lineChart(cr, tracklog, 0, 0, w, h)
      
    # * draw "escape" button
    menus.drawButton(cr, x1, y1, dx, dy, "", "up_transp_gama", "set:menu:tracklogInfo")


    if tracklog.trackpointsList == []:
      # there are no points to graph, so we quit
      return

    # * draw current elevation/position indicator
    pos = self.get('pos', None)
    if pos != None:
      (pLat,pLon) = pos
      l = [geo.distance(pLat,pLon,i[2],i[3]) for i in tracklog.perElevList]
      totalLength = len(tracklog.perElevList)
      nearestIndex = l.index(min(l)) # get index of the shortest distance
      step = (w-60-35)/totalLength # width minus padding divided by number of points

      currentPositionX = 60+nearestIndex*step

#      cr.set_source_rgba(1,1,1,1)
#      cr.set_line_width(5)
      cr.move_to(currentPositionX,0+30)
      cr.line_to(currentPositionX,h-40)
#      cr.stroke_preserve()
      cr.set_source_rgba(1.0, 0.5,0,1)
      cr.set_line_width(3)
      cr.stroke()
      cr.fill()

#      nearestPoint = tracklog.perElevList[nearestIndex] # get the nearest point
#      proj = self.m.get('projection', None)
#      (nLat,nLon) = (nearestPoint[2],nearestPoint[3])
    return

  def lineChart(self, cr, tracklog, x, y, w, h):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)

    title = tracklog.tracklogName

    list = tracklog.perElevList

    minimum = min(map(lambda x: x[1], list))
    maximum = max(map(lambda x: x[1], list))
#
#    list = map(lambda x: (x[0],(x[1]-minimum)), list)

    lines = tuple(map(lambda x: (x[0], x[1]), list))

    units = self.m.get('units', None)
    length = int(len(list))

    if w <= 610:
      yTick = 7
      labelTick = 20
      fontSize = 11
    else:
      yTick = 10
      labelTick = 20
      fontSize = 15

    if units == None:
      xTicks = [dict(v=r, label=list[r][0]) for r in range(0,length,labelTick)]
    else:
      xTicks = [dict(v=r, label=units.km2CurrentUnitString(round(list[r][0], 1))) for r in range(0,length,labelTick)]

#    list = tracklog.trackpointsList[0]
#    lines = tuple(map(lambda x: ("", float(x.elevation)), list))

    dataSet = (
        ('lines', [(i, l[1]) for i, l in enumerate(lines)]),
        )

    options = {
        'axis': {
        
            'tickFontSize' : fontSize,
            'labelFontSize': 12,

            'x': {
                  'ticks': xTicks,
                  'label' : "distance",
#                  'tickCount': 10, #number of data points on the X axis
#                 'ticks':[dict(v=i, label=l[1]) for i, l in enumerate(lines)],
            },
            'y': {
#                'interval' : 200,
                'range' : (minimum-15,maximum+30),
                'tickCount': yTick, #number of data points on the Y axis
#                'rotate' : 35,
                'label' : "elevation",
            }
        },
        'background': {
            'color': '#eeeeff',
            'lineColor': '#444444'
        },
        'colorScheme': {
            'name': 'gradient',
            'args': {
                'initialColor': 'blue',
            },
        },
        'legend': {
            'hide': True,
        },
        'padding': {
            'left': 60,
            'right': 35,
            'bottom': 40,
        },
        'title' : title,
        'titleFontSize': 16,
    }
    chart = pycha.line.LineChart(surface, options)
    chart.addDataset(dataSet)
    chart.render()
    cr.set_source_surface(surface, x, y)
    cr.paint()

if(__name__ == "__main__"):
  a = routeProfile({}, {})
  a.update()
  a.update()
  a.update()
