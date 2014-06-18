# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Draw OSD (On Screen Display).
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
    import gtk
    import pycha


def getModule(m, d, i):
    return ShowOSD(m, d, i)


class ShowOSD(RanaModule):
    """Draw OSD (On Screen Display)."""

    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)
        self.items = None
        self.routeProfileData = None
        self.nearestPoint = None
        self.nearestIndex = None
        self.distanceList = None # sorted distances from current position

        # colors
        self.widgetBackgroundColor = (0, 0, 1, 0.45) # transparent blue
        self.widgetTextColor = (1, 1, 1, 0.95) # slightly transparent white

    #    self.avail = set(
    #                      'speed'
    #                      )

    def firstTime(self):
        icons = self.m.get('icons', None)
        if icons:
            icons.subscribeColorInfo(self, self.colorsChangedCallback)

    def colorsChangedCallback(self, colors):
        self.widgetBackgroundColor = colors['widget_background'].getCairoColor()
        self.widgetTextColor = colors['widget_text'].getCairoColor()


    def drawScreenOverlay(self, cr):
        """ draw currently active information widgets TODO: just draw object from list"""
        if self.m.get('config', {}):
            config = self.modrana.configs.getUserConfig()

            mode = self.get('mode', None)
            if mode is None:
                return

            if mode not in config:
                return
            if 'OSD' in config[mode]:
                items = config[mode]['OSD']
                # we don't know the nearest point when refreshing the screen
                # TODO: don't search for nearest point on every refresh ?
                self.nearestPoint = None
                self.nearestIndex = None
                self.distanceList = None
                for item in items:
                    self.drawWidget(cr, items[item], item)


    def drawWidget(self, cr, item, type):
        if type == 'speed':
            speed = self.get('speed', 0)
            units = self.m.get('units', None)
            if speed is None:
                speedString = "? %s" % units.currentUnitString()
            else:
                speedString = units.km2CurrentUnitPerHourString(speed)
            self.drawMultilineTextWidget(cr, item, speedString)
        elif type == 'time':
            units = self.m.get('units', None)
            if units:
                timeString = units.getCurrentTimeString()
                self.drawMultilineTextWidget(cr, item, timeString)
        elif type == 'coordinates':
            pos = self.get('pos', None)
            if pos is None:
                return
            posString = "%f(lat)|%f(lon)" % pos
            self.drawMultilineTextWidget(cr, item, posString)
        elif type == 'statistics':
            units = self.m.get('units', None)
            maxSpeed = self.get('maxSpeed', 0)
            avg = self.get('avgSpeed', 0)
            statString = "max:%s|" % units.km2CurrentUnitPerHourStringTwoDP(maxSpeed)
            statString += "avg:%s" % units.km2CurrentUnitPerHourStringTwoDP(avg)
            self.drawMultilineTextWidget(cr, item, statString)
        elif type == 'route_profile':
            self.drawRouteProfile(cr, item)
        elif type == 'time_to_start':
            if self.routeProfileData is None:
                text = "activate a track | to show time to start"
                self.drawMultilineTextWidget(cr, item, text)
                return
            else:
                if self.distanceList is None: # was the nearest point already determined ?
                    if self.findNearestPoint() == False: # False is returned if the nearest point can not be computed
                        return
            avgSpeed = self.get('avgSpeed', 0)
            units = self.m.get('units', None) # get the unit conversion module
            avgSpeedMPS = units.currentSpeedUnitToMS(avgSpeed)
            currentLength = (self.routeProfileData[self.nearestIndex][0]) * 1000.0 # rem. length in meters
            if avgSpeedMPS == 0 or avgSpeedMPS == 0.0:
                timeString = "start moving"
            else:
                timeString = self.timeString(currentLength / avgSpeedMPS)
            text = 'to start:|%s h:m' % timeString
            self.drawMultilineTextWidget(cr, item, text)
        elif type == 'time_to_destination':
            if self.routeProfileData is None:
                text = "activate a track | to show time to dest."
                self.drawMultilineTextWidget(cr, item, text)
                return
            else:
                if self.distanceList is None: # was the nearest point already determined ?
                    if self.findNearestPoint() == False: # False is returned if the nearest point can not be computed
                        return
            avgSpeed = self.get('avgSpeed', 0)
            units = self.m.get('units', None) # get the unit conversion module
            avgSpeedMPS = units.currentSpeedUnitToMS(avgSpeed)
            currentLength = self.routeProfileData[self.nearestIndex][0]
            remainingLength = (self.routeProfileData[-1][0] - currentLength) * 1000 # rem. length in meters
            if avgSpeedMPS == 0 or avgSpeedMPS == 0.0:
                timeString = "start moving"
            else:
                timeString = self.timeString(remainingLength / avgSpeedMPS)
            text = 'to destination|%s h:m' % timeString
            self.drawMultilineTextWidget(cr, item, text)
        elif type == 'route_remaining_length':
            if self.routeProfileData is None:
                text = "activate a track | to show rem. length"
                self.drawMultilineTextWidget(cr, item, text)
                return
            else:
                if self.distanceList is None: # was the nearest point already determined ?
                    if self.findNearestPoint() == False: # False is returned if the nearest point can not be computed
                        return
                currentLength = self.routeProfileData[self.nearestIndex][0]
                remainingLength = self.routeProfileData[-1][0] - currentLength #TODO: from actual current position
            units = self.m.get('units', None) # get the unit conversion module
            text = "%s from start|" % units.km2CurrentUnitPerHourStringTwoDP(currentLength)
            text += "%s to destination" % units.km2CurrentUnitPerHourStringTwoDP(remainingLength)
            self.drawMultilineTextWidget(cr, item, text)

    def timeString(self, seconds):
        """convert seconds to h:m:s string"""
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return '%02d:%02d' % (hours, minutes)

    def drawMultilineTextWidget(self, cr, item, text=""):
        if 'px' and 'py' in item:
            proj = self.m.get('projection', None)
            (px, py) = float(item['px']), float(item['py'])
            (x, y) = proj.screenPos(px, py)

            if 'font_size' in item:
                fontSize = int(item['font_size'])
            else:
                fontSize = 30
            cr.set_font_size(fontSize)

            #      if 'pw' and 'ph' in item: # are the width and height set ?
            #        w = proj.screenWidth(float(item['pw']))
            #        h = proj.screenHeight(float(item['ph']))
            #      else: # width and height are not set, we ge them from the text size
            #        extents = cr.text_extents(text)
            #        (w,h) = (extents[2], extents[3])

            lines = text.split('|')
            border = 10
            (w, h) = (0, 0)
            yOffset = []
            for line in lines:
                extents = cr.text_extents(line)
                (w, h) = (max(w, extents[2]), h + extents[3] + border)
                yOffset.append(y + h)

            if 'align' in item:
                if item['align'] == 'right':
                    x -= w

            self.drawBackground(cr, x, y, w, h)

            i = 0
            for line in lines:
                self.drawText(cr, x, yOffset[i], line)
                i += 1

    def drawBackground(self, cr, x, y, w, h, source=None):
        cr.set_line_width(2)
        cr.set_source_rgba(*self.widgetBackgroundColor) # transparent blue
        #    (rx,ry,rw,rh) = (x, y-h*1.4, w*1.2, (h*2))
        (rx, ry, rw, rh) = (x, y, w * 1.2, h * 1.2)
        cr.rectangle(rx, ry, rw, rh) # create the transparent background rectangle
        cr.fill()

    def drawBackgroundExact(self, cr, x, y, w, h, source=None):
        cr.set_line_width(2)
        cr.set_source_rgba(*self.widgetBackgroundColor) # transparent blue
        (rx, ry, rw, rh) = (x, y, w, h)
        cr.rectangle(rx, ry, rw, rh) # create the transparent background rectangle
        cr.fill()

    def drawText(self, cr, x, y, text, source=None):
        cr.set_source_rgba(*self.widgetTextColor) # slightly transparent white
        cr.move_to(x + 10, y)
        cr.show_text(text) # show the transparent notification text
        cr.stroke()
        cr.fill()

    # from PyCha.color module

    def findNearestPoint(self):
        """find the nearest point of the active tracklog(nearest to our position)"""
        pos = self.get('pos', None)
        if pos is None:
            return False
        #    print(profile)

        #    (sx,sy) = proj.screenPos(0.5, 0.5)
        #    (sLat,sLon) = proj.xy2ll(sx, sy)

        (pLat, pLon) = pos

        # list order: distance from pos/screen center, lat, lon, distance from start, elevation
        distList = [(geo.distance(pLat, pLon, i[2], i[3]), i[2], i[3], i[0], i[1]) for i in self.routeProfileData]
        #    distList.sort()

        l = [k[0] for k in distList] # make a list with only distances to our position

        self.nearestIndex = l.index(min(l)) # get index of the shortest distance
        self.nearestPoint = distList[self.nearestIndex] # get the nearest point
        self.distanceList = distList
        return True


    def drawRouteProfile(self, cr, item):
        """draw a dynamic route profile as a part of the osd"""
        if self.routeProfileData is None:
            text = "activate a tracklog|to show route profile"
            item['font_size'] = 20
            self.drawMultilineTextWidget(cr, item, text)
            return

        #    profile = self.routeProfileData
        #    print(item)

        proj = self.m.get('projection', None)
        (px, py) = float(item['px']), float(item['py'])
        (x, y) = proj.screenPos(px, py)

        if 'pw' and 'ph' in item:
            (pw, ph) = float(item['pw']), float(item['ph'])
        else:
            (pw, ph) = (0.2, 0.15)
        (w, h) = proj.screenPos(pw, ph)

        segmentLength = 5
        if 'segment_length' in item:
            segmentLength = float(item['segment_length'])

        if self.distanceList is None: # was the nearest point already determined ?
            if self.findNearestPoint() == False: # False is returned if the nearest point can not be computed
                return

        distList = self.distanceList
        nearestIndex = self.nearestIndex # get index of the shortest distance
        #    nearestPoint = self.nearestPoint # get the nearest point

        # * build the dataset *

        # prepare

        step = distList[1][3] # distance between the periodic points
        totalLength = len(distList)

        nrPoints = int(segmentLength / step) # how many points re in the range ?

        leftAdd = 0
        rightAdd = 0

        leftIndex = nearestIndex - nrPoints / 2
        rightIndex = nearestIndex + nrPoints / 2
        #    print(leftAdd, leftIndex, nearestIndex, rightIndex, rightAdd)
        if leftIndex < 0:
            leftAdd = abs(leftIndex)
            leftIndex = 0
        if rightIndex > totalLength - 1:
            rightAdd = rightIndex - (totalLength - 1)
            rightIndex = totalLength - 1


        #    print(totalLength)
        #    print(leftAdd, leftIndex, nearestIndex, rightIndex, rightAdd)

        # build

        zeroes = [(0, 0, 0, 0, 0)] # simulates no data areas

        profile = []

        profile.extend(zeroes * leftAdd) # possible front padding
        profile.extend(distList[leftIndex:rightIndex]) # add the current segment
        profile.extend(zeroes * rightAdd) # possible end padding

        #    mostDistantPoint = distList[-1]

        #    (nx,ny) = proj.ll2xy(nearestPoint[1],nearestPoint[2])
        #    cr.set_source_rgb(1,1,0)
        #    cr.rectangle(nx,ny,20,20)
        #    cr.stroke()
        #    cr.fill()

        minimum = min(map(lambda x: x[4], profile))
        maximum = max(map(lambda x: x[4], profile))

        self.drawBackgroundExact(cr, x, y, w, h)
        self.drawLinechart(cr, x, y, w, 0.8 * h, maximum, minimum, profile)


        # draw current elevation indicator
        cr.set_source_rgb(1, 1, 0)
        cr.set_line_width(3)
        cr.move_to(x + w / 2.0, y)
        cr.line_to(x + w / 2.0, y + h)
        cr.stroke()
        cr.fill()

        cr.set_source_rgb(1, 1, 1)
        lengthString = '%1.2f km' % segmentLength
        maxString = "max: %1.0f m" % maximum
        minString = "min: %1.0f m" % minimum
        current = "%1.0f m" % self.nearestPoint[4]

        menu = self.m.get('menu', None) # we use a function from this module to draw text
        menu.drawText(cr, maxString, x, y, w * 0.35, 0.15 * h)
        menu.drawText(cr, minString, x + 0.63 * w, y, w * 0.35, 0.15 * h)
        menu.drawText(cr, lengthString, x, y + 0.8 * h, w * 0.45, 0.15 * h)
        cr.set_source_rgb(1, 1, 0)
        menu.drawText(cr, current, x + w / 1.9, y + 0.8 * h, w * 0.3, 0.15 * h)


    def drawLinechart(self, cr, x, y, w, h, maximum, minimum, profile):
        """draw a linechart, showing a segment of the route"""

        w = int(w)
        h = int(h)

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        profileList = profile

        #    minimum = min(map(lambda x: x[4], list))
        #    maximum = max(map(lambda x: x[4], list))

        lines = tuple(map(lambda x: (x[3], x[4]), profileList))

        dataSet = (
            ('lines', [(i, l[1]) for i, l in enumerate(lines)]),
        )

        options = {
            'axis': {

                'lineWidth': 1,
                'lineColor': '#0000ff',
                'labelFontSize': 12,

                'x': {
                },
                'y': {
                    'range': (minimum - h / 20, maximum + h / 20),
                    #                'range' : (minimum,maximum),
                }
            },
            'background': {
                'hide': True,
                'color': '#eeeeff',
                #            'lineColor': '#444444'
                'lineColor': '#eeeeff',
                'lineWidth': 10
            },
            'colorScheme': {
                'name': 'gradient',
                'args': {
                    #                'initialColor': 'blue',
                    'initialColor': '#eeeeff',
                },
            },
            'legend': {
                'hide': True,
            },
            'stroke': {
                'hide': False,
                'color': '#eeeeff',
                'width': 3
            },
            'yvals': {
                'hide': True,
                'color': '#eeeeff',
            },
            'xvals': {
                'hide': True,
                'color': '#eeeeff',
            },
            'padding': {
                'left': 0,
                'right': 0,
                'bottom': 0,
            },
            'shouldFill': False,
            'lineWidth': 10,
        }
        chart = pycha.line.LineChart(surface, options)
        chart.addDataset(dataSet)
        chart.render()
        cr.set_source_surface(surface, x, y)
        cr.paint()


def parseColour(inputString):
    color = gtk.gdk.color_parse(inputString)
    return color


def hex2rgb(hexstring, digits=2):
    """Converts a hexstring color to a rgb tuple.

    Example: #ff0000 -> (1.0, 0.0, 0.0)

    digits is an integer number telling how many characters should be
    interpreted for each component in the hexstring.
    """
    if isinstance(hexstring, (tuple, list)):
        return hexstring

    top = float(int(digits * 'f', 16))
    r = int(hexstring[1:digits + 1], 16)
    g = int(hexstring[digits + 1:digits * 2 + 1], 16)
    b = int(hexstring[digits * 2 + 1:digits * 3 + 1], 16)
    return r / top, g / top, b / top
