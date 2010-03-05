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
#from lines import lines
import sys
import cairo

def getModule(m,d):
  return(routeProfile(m,d))

class routeProfile(ranaModule):
  """Creates a route profile (an elevation chart)"""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    
  def update(self):
    # Get and set functions are used to access global data
    self.set('num_updates', self.get('num_updates', 0) + 1)
    #print "Updated %d times" % (self.get('num_updates'))

  def drawMenu(self, cr, menuName):
    #print menuName
    # is this menu the correct menu ?
    if menuName != 'routeProfile':
      return # we arent the active menu so we dont do anything
    (x1,y1,w,h) = self.get('viewport', None)
    if w > h:
      cols = 4
      rows = 3
    elif w < h:
      cols = 3
      rows = 4
    elif w == h:
      cols = 4
      rows = 4

    dx = w / cols
    dy = h / rows

    menus = self.m.get("menu",None)
    loadTl = self.m.get('loadTracklog', None) # get the tracklog module
    loadedTracklogs = loadTl.tracklogs # get list of all tracklogs
    #tracklistsWithElevation = filter(lambda x: x.elevation == True, loadedTracklogs)
    activeTracklogIndex = int(self.get('activeTracklog', 0))
    print activeTracklogIndex
    tracklog = loadedTracklogs[activeTracklogIndex]
    if tracklog.elevation == True:
      self.lineChart(cr, tracklog, w, h)
    # * draw "escape" button
    menus.drawButton(cr, x1, y1, dx, dy, "", "up_transp_gama", "set:menu:main")
    return

  def lineChart(self, cr, tracklog, w, h):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)

    list = tracklog.trackpointsList[0]
    lines = tuple(map(lambda x: ("", float(x.elevation)), list))
    
    dataSet = (
        ('lines', [(i, l[1]) for i, l in enumerate(lines)]),
        )

    options = {
        'axis': {
            'x': {
                #'ticks': [dict(v=i, label=l[0]) for i, l in enumerate(lines)],
                #'ticks' : [1:3,2,3,],
            },
            'y': {
                'tickCount': 10, #number of data points on the Y axis
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
            'left': 55,
            'bottom': 40,
        }
    }
    chart = pycha.line.LineChart(surface, options)
    chart.addDataset(dataSet)
    chart.render()
    cr.set_source_surface(surface, 0, 0)
    cr.paint()
#    cr.move_to(0, 680)
#    cr.line_to(480,680)
#    cr.stroke()
#    cr.fill()

if(__name__ == "__main__"):
  a = routeProfile({}, {})
  a.update()
  a.update()
  a.update()
