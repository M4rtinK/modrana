# -*- coding: utf-8 -*-
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
from modules.base_module import RanaModule
from core import geo
# only import GKT libs if GTK GUI is used
from core import gs

if gs.GUIString == "GTK":
    import cairo
    from core.bundle import pycha
    # from core.bundle.pycha import line as pycha_color
    # from core.bundle.pycha import color as pycha_line

def getModule(m, d, i):
    return RouteProfile(m, d, i)


class RouteProfile(RanaModule):
    """Creates a route profile (an elevation chart)"""

    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)

    def drawMenu(self, cr, menuName, args=None):
        # is this menu the correct menu ?
        if menuName != 'routeProfile':
            return # we aren't the active menu so we don't do anything
        (x1, y1, w, h) = self.get('viewport', None)
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

        dx = min(w, h) / 5.0
        dy = dx

        # draw a solid color background
        cr.rectangle(x1, y1, w, h)
        cr.set_source_rgb(*pycha.color.hex2rgb("#eeeeff"))
        cr.fill()

        menus = self.m.get("menu", None)
        loadTl = self.m.get('loadTracklogs', None) # get the tracklog module
        tracklog = loadTl.getActiveTracklog()
        if tracklog.elevation == True:
            self.lineChart(cr, tracklog, 0, 0, w, h)

        # * draw "escape" button
        menus.drawButton(cr, x1, y1, dx, dy, "", "center:back;0.2;0.3>generic:;0.5;;0.5;;",
                         "set:menu:tracklogManager#tracklogInfo")

        if tracklog.trackpointsList == []:
            # there are no points to graph, so we quit
            return

        # * draw current elevation/position indicator
        pos = self.get('pos', None)
        if pos is not None:
            (pLat, pLon) = pos
            l = [geo.distance(pLat, pLon, i[2], i[3]) for i in tracklog.perElevList]
            totalLength = len(tracklog.perElevList)
            nearestIndex = l.index(min(l)) # get index of the shortest distance
            step = (w - 60 - 35) / totalLength # width minus padding divided by number of points

            currentPositionX = 60 + nearestIndex * step

            #      cr.set_source_rgba(1,1,1,1)
            #      cr.set_line_width(5)
            cr.move_to(currentPositionX, 0 + 30)
            cr.line_to(currentPositionX, h - 40)
            #      cr.stroke_preserve()
            cr.set_source_rgba(1.0, 0.5, 0, 1)
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

        elevList = tracklog.perElevList

        units = self.m.get('units', None)
        if units is None:
            print("routeProfile, lineChart: Units module missing")
            return

        length = int(len(elevList))
        lines = tuple(map(lambda x: (x[0], x[1]), elevList))

        if w <= 610:
            yTick = 7
            labelTick = 20
            fontSize = 11
        else:
            yTick = 10
            labelTick = 20
            fontSize = 15

        xTicks = [dict(v=r, label=units.km2CurrentUnitString(elevList[r][0], 1)) for r in range(0, length, labelTick)]
        minimum = min(map(lambda x: x[1], elevList))
        maximum = max(map(lambda x: x[1], elevList))

        #    elevList = map(lambda x: (x[0],(x[1]-minimum)), elevList)


        unitType = self.get('unitType', 'km')
        if unitType == 'km':
            yAxis = {
                #                  'interval' : 200,
                'range': (minimum - 15, maximum + 30),
                'tickCount': yTick, #number of data points on the Y axis
                'label': "elevation (m)",

            }
        else: # non metric
            cuMinimum = units.m2CurrentUnitString(minimum, 3, short=True)
            cuMaximum = units.m2CurrentUnitString(maximum, 3, short=True)
            middle = minimum + (maximum - minimum) / 2.0
            #      print(minimum)
            #      print(middle)
            #      print(maximum)
            cuMiddle = units.m2CurrentUnitString(middle, 3, short=True)
            yTicks = [{'label': cuMinimum, 'v': minimum - 15},
                      {'label': cuMiddle, 'v': middle + 15 / 2.0},
                      {'label': cuMaximum, 'v': maximum + 30}]
            yAxis = {
                #                  'interval' : 200,
                'range': (minimum - 15, maximum + 30),
                'ticks': yTicks,
                #                  'tickCount': yTick, #number of data points on the Y axis
                #                   'label' : "elevation (%s)" % units.currentSmallUnitString(short=True),
                'label': "elevation",
            }

        dataSet = (
            ('lines', [(i, l[1]) for i, l in enumerate(lines)]),
        )

        options = {
            'axis': {

                'tickFontSize': fontSize,
                'labelFontSize': 12,

                'x': {
                    'ticks': xTicks,
                    'label': "distance",
                    #                  'tickCount': 10, #number of data points on the X axis
                },
                'y': yAxis
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
            'title': title,
            'titleFontSize': 16,
        }
        chart = pycha.line.LineChart(surface, options)
        chart.addDataset(dataSet)
        chart.render()
        cr.set_source_surface(surface, x, y)
        cr.paint()
