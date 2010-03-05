# Copyright(c) 2007-2009 by Lorenzo Gil Sanchez <lorenzo.gil.sanchez@gmail.com>
#
# This file is part of PyCha.
#
# PyCha is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyCha is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with PyCha.  If not, see <http://www.gnu.org/licenses/>.

import math

import cairo

from pycha.chart import Chart, Option
from pycha.color import hex2rgb


class PieChart(Chart):

    def __init__(self, surface=None, options={}):
        super(PieChart, self).__init__(surface, options)
        self.slices = []
        self.centerx = 0
        self.centery = 0
        self.radius = 0

    def _updateChart(self):
        """Evaluates measures for pie charts"""
        self.centerx = self.area.x + self.area.w * 0.5
        self.centery = self.area.y + self.area.h * 0.5
        self.radius = min(self.area.w * self.options.pieRadius,
                          self.area.h * self.options.pieRadius)

        slices = [dict(name=key,
                       value=(i, value[0][1]))
                  for i, (key, value) in enumerate(self.datasets)]

        s = float(sum([slice['value'][1] for slice in slices]))

        fraction = angle = 0.0

        self.slices = []
        for slice in slices:
            angle += fraction
            if slice['value'][1] > 0:
                fraction = slice['value'][1] / s
                self.slices.append(Slice(slice['name'], fraction,
                                         slice['value'][0], slice['value'][1],
                                         angle))

    def _updateTicks(self):
        """Evaluates pie ticks"""
        self.xticks = []
        if self.options.axis.x.ticks:
            lookup = dict([(slice.xval, slice) for slice in self.slices])
            for tick in self.options.axis.x.ticks:
                if not isinstance(tick, Option):
                    tick = Option(tick)
                slice = lookup.get(tick.v, None)
                label = tick.label or str(tick.v)
                if slice is not None:
                    label += ' (%.1f%%)' % (slice.fraction * 100)
                    self.xticks.append((tick.v, label))
        else:
            for slice in self.slices:
                label = '%s (%.1f%%)' % (slice.name, slice.fraction * 100)
                self.xticks.append((slice.xval, label))

    def _renderBackground(self, cx):
        """Renders the background of the chart"""
        if self.options.background.hide:
            return

        cx.save()

        if self.options.background.baseColor:
            cx.set_source_rgb(*hex2rgb(self.options.background.baseColor))
            x, y, w, h = 0, 0, self.area.w, self.area.h
            w += self.options.padding.left + self.options.padding.right
            h += self.options.padding.top + self.options.padding.bottom
            cx.rectangle(x, y, w, h)
            cx.fill()

        cx.restore()

    def _renderChart(self, cx):
        """Renders a pie chart"""
        cx.set_line_join(cairo.LINE_JOIN_ROUND)

        if self.options.stroke.shadow:
            cx.save()
            cx.set_source_rgba(0, 0, 0, 0.15)

            cx.new_path()
            cx.move_to(self.centerx, self.centery)
            cx.arc(self.centerx + 1, self.centery + 2, self.radius + 1, 0,
                   math.pi * 2)
            cx.line_to(self.centerx, self.centery)
            cx.close_path()
            cx.fill()
            cx.restore()

        cx.save()
        for slice in self.slices:
            if slice.isBigEnough():
                cx.set_source_rgb(*self.colorScheme[slice.name])
                if self.options.shouldFill:
                    slice.draw(cx, self.centerx, self.centery, self.radius)
                    cx.fill()

                if not self.options.stroke.hide:
                    slice.draw(cx, self.centerx, self.centery, self.radius)
                    cx.set_line_width(self.options.stroke.width)
                    cx.set_source_rgb(*hex2rgb(self.options.stroke.color))
                    cx.stroke()

        cx.restore()

    def _renderAxis(self, cx):
        """Renders the axis for pie charts"""
        if self.options.axis.x.hide or not self.xticks:
            return

        self.xlabels = []
        lookup = dict([(slice.xval, slice) for slice in self.slices])


        cx.select_font_face(self.options.axis.tickFont,
                            cairo.FONT_SLANT_NORMAL,
                            cairo.FONT_WEIGHT_NORMAL)
        cx.set_font_size(self.options.axis.tickFontSize)

        cx.set_source_rgb(*hex2rgb(self.options.axis.labelColor))

        for tick in self.xticks:
            slice = lookup[tick[0]]

            normalisedAngle = slice.getNormalisedAngle()

            big_radius = self.radius + 10
            labelx = self.centerx + math.sin(normalisedAngle) * big_radius
            labely = self.centery - math.cos(normalisedAngle) * big_radius

            label = tick[1]
            extents = cx.text_extents(label)
            labelWidth = extents[2]
            labelHeight = extents[3]
            x = y = 0

            if normalisedAngle <= math.pi * 0.5:
                x = labelx
                y = labely - labelHeight
            elif math.pi * 0.5 < normalisedAngle <= math.pi:
                x = labelx
                y = labely
            elif math.pi < normalisedAngle <= math.pi * 1.5:
                x = labelx - labelWidth
                y = labely
            else:
                x = labelx - labelWidth
                y = labely - labelHeight

            # draw label with text tick[1]
            cx.move_to(x, y)
            cx.show_text(label)
            self.xlabels.append(label)


class Slice(object):

    def __init__(self, name, fraction, xval, yval, angle):
        self.name = name
        self.fraction = fraction
        self.xval = xval
        self.yval = yval
        self.startAngle = 2 * angle * math.pi
        self.endAngle = 2 * (angle + fraction) * math.pi

    def __str__(self):
        return ("<pycha.pie.Slice from %.2f to %.2f (%.2f%%)>" %
                (self.startAngle, self.endAngle, self.fraction))

    def isBigEnough(self):
        return abs(self.startAngle - self.endAngle) > 0.001

    def draw(self, cx, centerx, centery, radius):
        cx.new_path()
        cx.move_to(centerx, centery)
        cx.arc(centerx, centery, radius,
               self.startAngle - math.pi/2,
               self.endAngle - math.pi/2)
        cx.line_to(centerx, centery)
        cx.close_path()

    def getNormalisedAngle(self):
        normalisedAngle = (self.startAngle + self.endAngle) / 2

        if normalisedAngle > math.pi * 2:
            normalisedAngle -= math.pi * 2
        elif normalisedAngle < 0:
            normalisedAngle += math.pi * 2

        return normalisedAngle
