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

from pycha.chart import Chart, uniqueIndices
from pycha.color import hex2rgb


class BarChart(Chart):

    def __init__(self, surface=None, options={}):
        super(BarChart, self).__init__(surface, options)
        self.bars = []
        self.minxdelta = 0.0
        self.barWidthForSet = 0.0
        self.barMargin = 0.0

    def _updateXY(self):
        super(BarChart, self)._updateXY()
        # each dataset is centered around a line segment. that's why we
        # need n + 1 divisions on the x axis
        self.xscale = 1 / (self.xrange + 1.0)

    def _updateChart(self):
        """Evaluates measures for vertical bars"""
        stores = self._getDatasetsValues()
        uniqx = uniqueIndices(stores)

        if len(uniqx) == 1:
            self.minxdelta = 1.0
        else:
            self.minxdelta = min([abs(uniqx[j] - uniqx[j-1])
                                  for j in range(1, len(uniqx))])

        k = self.minxdelta * self.xscale
        barWidth = k * self.options.barWidthFillFraction
        self.barWidthForSet = barWidth / len(stores)
        self.barMargin = k * (1.0 - self.options.barWidthFillFraction) / 2

        self.bars = []

    def _renderChart(self, cx):
        """Renders a horizontal/vertical bar chart"""

        def drawBar(bar):
            stroke_width = self.options.stroke.width
            ux, uy = cx.device_to_user_distance(stroke_width, stroke_width)
            if ux < uy:
                ux = uy
            cx.set_line_width(ux)

            # gather bar proportions
            x = self.area.x + self.area.w * bar.x
            y = self.area.y + self.area.h * bar.y
            w = self.area.w * bar.w
            h = self.area.h * bar.h

            if w < 1 or h < 1:
                return # don't draw when the bar is too small

            if self.options.stroke.shadow:
                cx.set_source_rgba(0, 0, 0, 0.15)
                rectangle = self._getShadowRectangle(x, y, w, h)
                cx.rectangle(*rectangle)
                cx.fill()

            if self.options.shouldFill or (not self.options.stroke.hide):

                if self.options.shouldFill:
                    cx.set_source_rgb(*self.colorScheme[bar.name])
                    cx.rectangle(x, y, w, h)
                    cx.fill()

                if not self.options.stroke.hide:
                    cx.set_source_rgb(*hex2rgb(self.options.stroke.color))
                    cx.rectangle(x, y, w, h)
                    cx.stroke()

            # render yvals above/beside bars
            if self.options.yvals.show:
                cx.save()
                cx.set_font_size(self.options.yvals.fontSize)
                cx.set_source_rgb(*hex2rgb(self.options.yvals.fontColor))

                label = unicode(bar.yval)
                extents = cx.text_extents(label)
                labelW = extents[2]
                labelH = extents[3]

                self._renderYVal(cx, label, labelW, labelH, x, y, w, h)

                cx.restore()

        cx.save()
        for bar in self.bars:
            drawBar(bar)
        cx.restore()

    def _renderYVal(self, cx, label, width, height, x, y, w, h):
        raise NotImplementedError


class VerticalBarChart(BarChart):

    def _updateChart(self):
        """Evaluates measures for vertical bars"""
        super(VerticalBarChart, self)._updateChart()
        for i, (name, store) in enumerate(self.datasets):
            for item in store:
                xval, yval = item
                x = (((xval - self.minxval) * self.xscale)
                    + self.barMargin + (i * self.barWidthForSet))
                w = self.barWidthForSet
                h = abs(yval) * self.yscale
                if yval > 0:
                    y = (1.0 - h) - self.area.origin
                else:
                    y = 1 - self.area.origin
                rect = Rect(x, y, w, h, xval, yval, name)

                if (0.0 <= rect.x <= 1.0) and (0.0 <= rect.y <= 1.0):
                    self.bars.append(rect)

    def _updateTicks(self):
        """Evaluates bar ticks"""
        super(BarChart, self)._updateTicks()
        offset = (self.minxdelta * self.xscale) / 2
        self.xticks = [(tick[0] + offset, tick[1]) for tick in self.xticks]

    def _getShadowRectangle(self, x, y, w, h):
        return (x-2, y-2, w+4, h+2)

    def _renderYVal(self, cx, label, labelW, labelH, barX, barY, barW, barH):
        x = barX + (barW / 2.0) - (labelW / 2.0)
        if self.options.yvals.inside:
            y = barY + (1.5 * labelH)
        else:
            y = barY - 0.5 * labelH

        # if the label doesn't fit below the bar, put it above the bar
        if y > (barY + barH):
            y = barY - 0.5 * labelH

        cx.move_to(x, y)
        cx.show_text(label)


class HorizontalBarChart(BarChart):

    def _updateChart(self):
        """Evaluates measures for horizontal bars"""
        super(HorizontalBarChart, self)._updateChart()

        for i, (name, store) in enumerate(self.datasets):
            for item in store:
                xval, yval = item
                y = (((xval - self.minxval) * self.xscale)
                     + self.barMargin + (i * self.barWidthForSet))
                h = self.barWidthForSet
                w = abs(yval) * self.yscale
                if yval > 0:
                    x = self.area.origin
                else:
                    x = self.area.origin - w
                rect = Rect(x, y, w, h, xval, yval, name)

                if (0.0 <= rect.x <= 1.0) and (0.0 <= rect.y <= 1.0):
                    self.bars.append(rect)

    def _updateTicks(self):
        """Evaluates bar ticks"""
        super(BarChart, self)._updateTicks()
        offset = (self.minxdelta * self.xscale) / 2
        tmp = self.xticks
        self.xticks = [(1.0 - tick[0], tick[1]) for tick in self.yticks]
        self.yticks = [(tick[0] + offset, tick[1]) for tick in tmp]

    def _renderLines(self, cx):
        """Aux function for _renderBackground"""
        ticks = self.xticks
        for tick in ticks:
            self._renderLine(cx, tick, True)

    def _getShadowRectangle(self, x, y, w, h):
        return (x, y-2, w+2, h+4)

    def _renderXAxis(self, cx):
        """Draws the horizontal line representing the X axis"""
        cx.new_path()
        cx.move_to(self.area.x, self.area.y + self.area.h)
        cx.line_to(self.area.x + self.area.w, self.area.y + self.area.h)
        cx.close_path()
        cx.stroke()

    def _renderYAxis(self, cx):
        # draws the vertical line representing the Y axis
        cx.new_path()
        cx.move_to(self.area.x + self.area.origin * self.area.w,
                   self.area.y)
        cx.line_to(self.area.x + self.area.origin * self.area.w,
                   self.area.y + self.area.h)
        cx.close_path()
        cx.stroke()

    def _renderYVal(self, cx, label, labelW, labelH, barX, barY, barW, barH):
        y = barY + (barH / 2.0) + (labelH / 2.0)
        if self.options.yvals.inside:
            x = barX + barW - (1.2 * labelW)
        else:
            x = barX + barW + 0.2 * labelW

        # if the label doesn't fit to the left of the bar, put it to the right
        if x < barX:
            x = barX + barW + 0.2 * labelW

        cx.move_to(x, y)
        cx.show_text(label)


class Rect(object):

    def __init__(self, x, y, w, h, xval, yval, name):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.xval, self.yval = xval, yval
        self.name = name

    def __str__(self):
        return ("<pycha.bar.Rect@(%.2f, %.2f) %.2fx%.2f (%.2f, %.2f) %s>"
                % (self.x, self.y, self.w, self.h, self.xval, self.yval,
                   self.name))
