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

import copy
import inspect
import math

import cairo

from pycha.color import ColorScheme, hex2rgb, DEFAULT_COLOR


class Chart(object):

    def __init__(self, surface, options={}):
        # this flag is useful to reuse this chart for drawing different data
        # or use different options
        self.resetFlag = False

        # initialize storage
        self.datasets = []

        # computed values used in several methods
        self.area = None # chart area without padding or text labels
        self.minxval = None
        self.maxxval = None
        self.minyval = None
        self.maxyval = None
        self.xscale = 1.0
        self.yscale = 1.0
        self.xrange = None
        self.yrange = None

        self.xticks = []
        self.yticks = []

        # set the default options
        self.options = copy.deepcopy(DEFAULT_OPTIONS)
        if options:
            self.options.merge(options)

        # initialize the surface
        self._initSurface(surface)

        self.colorScheme = None

    def addDataset(self, dataset):
        """Adds an object containing chart data to the storage hash"""
        self.datasets += dataset

    def _getDatasetsKeys(self):
        """Return the name of each data set"""
        return [d[0] for d in self.datasets]

    def _getDatasetsValues(self):
        """Return the data (value) of each data set"""
        return [d[1] for d in self.datasets]

    def setOptions(self, options={}):
        """Sets options of this chart"""
        self.options.merge(options)

    def getSurfaceSize(self):
        cx = cairo.Context(self.surface)
        x, y, w, h = cx.clip_extents()
        return w, h

    def reset(self):
        """Resets options and datasets.

        In the next render the surface will be cleaned before any drawing.
        """
        self.resetFlag = True
        self.options = copy.deepcopy(DEFAULT_OPTIONS)
        self.datasets = []

    def render(self, surface=None, options={}):
        """Renders the chart with the specified options.

        The optional parameters can be used to render a chart in a different
        surface with new options.
        """
        self._update(options)
        if surface:
            self._initSurface(surface)

        cx = cairo.Context(self.surface)
        self._renderBackground(cx)
        self._renderChart(cx)
        self._renderAxis(cx)
        self._renderTitle(cx)
        self._renderLegend(cx)

    def clean(self):
        """Clears the surface with a white background."""
        cx = cairo.Context(self.surface)
        cx.save()
        cx.set_source_rgb(1, 1, 1)
        cx.paint()
        cx.restore()

    def _setColorscheme(self):
        """Sets the colorScheme used for the chart using the
        options.colorScheme option
        """
        name = self.options.colorScheme.name
        keys = self._getDatasetsKeys()
        colorSchemeClass = ColorScheme.getColorScheme(name, None)
        if colorSchemeClass is None:
            raise ValueError('Color scheme "%s" is invalid!' % name)

        # Remove invalid args before calling the constructor
        kwargs = dict(self.options.colorScheme.args)
        validArgs = inspect.getargspec(colorSchemeClass.__init__)[0]
        kwargs = dict([(k, v) for k, v in kwargs.items() if k in validArgs])
        self.colorScheme = colorSchemeClass(keys, **kwargs)

    def _initSurface(self, surface):
        self.surface = surface

        if self.resetFlag:
            self.resetFlag = False
            self.clean()

    def _update(self, options={}):
        """Update all the information needed to render the chart"""
        self.setOptions(options)
        self._setColorscheme()
        self._updateXY()
        self._updateChart()
        self._updateTicks()

    def _updateXY(self):
        """Calculates all kinds of metrics for the x and y axis"""
        x_range_is_defined = self.options.axis.x.range is not None
        y_range_is_defined = self.options.axis.y.range is not None

        if not x_range_is_defined or not y_range_is_defined:
            stores = self._getDatasetsValues()

        # gather data for the x axis
        if x_range_is_defined:
            self.minxval, self.maxxval = self.options.axis.x.range
        else:
            xdata = [pair[0] for pair in reduce(lambda a, b: a+b, stores)]
            self.minxval = float(min(xdata))
            self.maxxval = float(max(xdata))
            if self.minxval * self.maxxval > 0 and self.minxval > 0:
                self.minxval = 0.0

        self.xrange = self.maxxval - self.minxval
        if self.xrange == 0:
            self.xscale = 1.0
        else:
            self.xscale = 1.0 / self.xrange

        # gather data for the y axis
        if y_range_is_defined:
            self.minyval, self.maxyval = self.options.axis.y.range
        else:
            ydata = [pair[1] for pair in reduce(lambda a, b: a+b, stores)]
            self.minyval = float(min(ydata))
            self.maxyval = float(max(ydata))
            if self.minyval * self.maxyval > 0 and self.minyval > 0:
                self.minyval = 0.0

        self.yrange = self.maxyval - self.minyval
        if self.yrange == 0:
            self.yscale = 1.0
        else:
            self.yscale = 1.0 / self.yrange

        # calculate area data
        surface_width, surface_height = self.getSurfaceSize()
        width = (surface_width
                 - self.options.padding.left - self.options.padding.right)
        height = (surface_height
                  - self.options.padding.top - self.options.padding.bottom)

        if self.minyval * self.maxyval < 0: # different signs
            origin = abs(self.minyval) * self.yscale
        else:
            origin = 0

        self.area = Area(self.options.padding.left,
                         self.options.padding.top,
                         width, height, origin)

    def _updateChart(self):
        raise NotImplementedError

    def _updateTicks(self):
        """Evaluates ticks for x and y axis.

        You should call _updateXY before because that method computes the
        values of xscale, minxval, yscale, and other attributes needed for
        this method.
        """
        stores = self._getDatasetsValues()

        # evaluate xTicks
        self.xticks = []
        if self.options.axis.x.ticks:
            for tick in self.options.axis.x.ticks:
                if not isinstance(tick, Option):
                    tick = Option(tick)
                if tick.label is None:
                    label = str(tick.v)
                else:
                    label = tick.label
                pos = self.xscale * (tick.v - self.minxval)
                if 0.0 <= pos <= 1.0:
                    self.xticks.append((pos, label))

        elif self.options.axis.x.interval > 0:
            interval = self.options.axis.x.interval
            label = (divmod(self.minxval, interval)[0] + 1) * interval
            pos = self.xscale * (label - self.minxval)
            while 0.0 <= pos <= 1.0:
                self.xticks.append((pos, label))
                label += interval
                pos = self.xscale * (label - self.minxval)

        elif self.options.axis.x.tickCount > 0:
            uniqx = range(len(uniqueIndices(stores)) + 1)
            roughSeparation = self.xrange / self.options.axis.x.tickCount
            i = j = 0
            while i < len(uniqx) and j < self.options.axis.x.tickCount:
                if (uniqx[i] - self.minxval) >= (j * roughSeparation):
                    pos = self.xscale * (uniqx[i] - self.minxval)
                    if 0.0 <= pos <= 1.0:
                        self.xticks.append((pos, uniqx[i]))
                        j += 1
                i += 1

        # evaluate yTicks
        self.yticks = []
        if self.options.axis.y.ticks:
            for tick in self.options.axis.y.ticks:
                if not isinstance(tick, Option):
                    tick = Option(tick)
                if tick.label is None:
                    label = str(tick.v)
                else:
                    label = tick.label
                pos = 1.0 - (self.yscale * (tick.v - self.minyval))
                if 0.0 <= pos <= 1.0:
                    self.yticks.append((pos, label))

        elif self.options.axis.y.interval > 0:
            interval = self.options.axis.y.interval
            label = (divmod(self.minyval, interval)[0] + 1) * interval
            pos = 1.0 - (self.yscale * (label - self.minyval))
            while 0.0 <= pos <= 1.0:
                self.yticks.append((pos, label))
                label += interval
                pos = 1.0 - (self.yscale * (label - self.minyval))

        elif self.options.axis.y.tickCount > 0:
            prec = self.options.axis.y.tickPrecision
            num = self.yrange / self.options.axis.y.tickCount
            if (num < 1 and prec == 0):
                roughSeparation = 1
            else:
                roughSeparation = round(num, prec)

            for i in range(self.options.axis.y.tickCount + 1):
                yval = self.minyval + (i * roughSeparation)
                pos = 1.0 - ((yval - self.minyval) * self.yscale)
                if 0.0 <= pos <= 1.0:
                    self.yticks.append((pos, round(yval, prec)))

    def _renderBackground(self, cx):
        """Renders the background area of the chart"""
        if self.options.background.hide:
            return

        cx.save()

        if self.options.background.baseColor:
            cx.set_source_rgb(*hex2rgb(self.options.background.baseColor))
            cx.paint()

        if self.options.background.chartColor:
            cx.set_source_rgb(*hex2rgb(self.options.background.chartColor))
            cx.rectangle(self.area.x, self.area.y, self.area.w, self.area.h)
            cx.fill()

        if self.options.background.lineColor:
            cx.set_source_rgb(*hex2rgb(self.options.background.lineColor))
            cx.set_line_width(self.options.axis.lineWidth)
            self._renderLines(cx)

        cx.restore()

    def _renderLines(self, cx):
        """Aux function for _renderBackground"""
        ticks = self.yticks
        for tick in ticks:
            self._renderLine(cx, tick, False)

    def _renderLine(self, cx, tick, horiz):
        """Aux function for _renderLines"""
        x1, x2, y1, y2 = (0, 0, 0, 0)
        if horiz:
            x1 = x2 = tick[0] * self.area.w + self.area.x
            y1 = self.area.y
            y2 = y1 + self.area.h
        else:
            x1 = self.area.x
            x2 = x1 + self.area.w
            y1 = y2 = tick[0] * self.area.h + self.area.y

        cx.new_path()
        cx.move_to(x1, y1)
        cx.line_to(x2, y2)
        cx.close_path()
        cx.stroke()

    def _renderChart(self, cx):
        raise NotImplementedError

    def _renderYTick(self, cx, tick):
        """Aux method for _renderAxis"""

        if callable(tick):
            return

        x = self.area.x
        y = self.area.y + tick[0] * self.area.h

        cx.new_path()
        cx.move_to(x, y)
        cx.line_to(x - self.options.axis.tickSize, y)
        cx.close_path()
        cx.stroke()

        cx.select_font_face(self.options.axis.tickFont,
                            cairo.FONT_SLANT_NORMAL,
                            cairo.FONT_WEIGHT_NORMAL)
        cx.set_font_size(self.options.axis.tickFontSize)

        label = unicode(tick[1])
        extents = cx.text_extents(label)
        labelWidth = extents[2]
        labelHeight = extents[3]

        if self.options.axis.y.rotate:
            radians = math.radians(self.options.axis.y.rotate)
            cx.move_to(x - self.options.axis.tickSize
                       - (labelWidth * math.cos(radians))
                       - 4,
                       y + (labelWidth * math.sin(radians))
                       + labelHeight / (2.0 / math.cos(radians)))
            cx.rotate(-radians)
            cx.show_text(label)
            cx.rotate(radians) # this is probably faster than a save/restore
        else:
            cx.move_to(x - self.options.axis.tickSize - labelWidth - 4,
                       y + labelHeight / 2.0)
            cx.show_text(label)

        return label

    def _renderXTick(self, cx, tick, fontAscent):
        if callable(tick):
            return

        x = self.area.x + tick[0] * self.area.w
        y = self.area.y + self.area.h

        cx.new_path()
        cx.move_to(x, y)
        cx.line_to(x, y + self.options.axis.tickSize)
        cx.close_path()
        cx.stroke()

        cx.select_font_face(self.options.axis.tickFont,
                            cairo.FONT_SLANT_NORMAL,
                            cairo.FONT_WEIGHT_NORMAL)
        cx.set_font_size(self.options.axis.tickFontSize)

        label = unicode(tick[1])
        extents = cx.text_extents(label)
        labelWidth = extents[2]
        labelHeight = extents[3]

        if self.options.axis.x.rotate:
            radians = math.radians(self.options.axis.x.rotate)
            cx.move_to(x - (labelHeight * math.cos(radians)),
                       y + self.options.axis.tickSize
                       + (labelHeight * math.cos(radians))
                       + 4.0)
            cx.rotate(radians)
            cx.show_text(label)
            cx.rotate(-radians)
        else:
            cx.move_to(x - labelWidth / 2.0,
                       y + self.options.axis.tickSize
                       + fontAscent + 4.0)
            cx.show_text(label)
        return label

    def _getTickSize(self, cx, ticks, rotate):
        tickExtents = [cx.text_extents(unicode(tick[1]))[2:4]
                       for tick in ticks]
        tickWidth = tickHeight = 0.0
        if tickExtents:
            tickHeight = self.options.axis.tickSize + 4.0
            tickWidth = self.options.axis.tickSize + 4.0
            widths, heights = zip(*tickExtents)
            maxWidth, maxHeight = max(widths), max(heights)
            if rotate:
                radians = math.radians(rotate)
                sinRadians = math.sin(radians)
                cosRadians = math.cos(radians)
                maxHeight = maxWidth * sinRadians + maxHeight * cosRadians
                maxWidth = maxWidth * cosRadians + maxHeight * sinRadians
            tickWidth += maxWidth
            tickHeight += maxHeight
        return tickWidth, tickHeight

    def _renderAxisLabel(self, cx, tickWidth, tickHeight, label, x, y,
                         vertical=False):
        cx.new_path()
        cx.select_font_face(self.options.axis.labelFont,
                            cairo.FONT_SLANT_NORMAL,
                            cairo.FONT_WEIGHT_BOLD)
        cx.set_font_size(self.options.axis.labelFontSize)
        labelWidth = cx.text_extents(label)[2]
        fontAscent = cx.font_extents()[0]
        if vertical:
            cx.move_to(x, y + labelWidth / 2)
            radians = math.radians(90)
            cx.rotate(-radians)
        else:
            cx.move_to(x - labelWidth / 2.0, y + fontAscent)

        cx.show_text(label)

    def _renderYAxis(self, cx):
        """Draws the vertical line represeting the Y axis"""
        cx.new_path()
        cx.move_to(self.area.x, self.area.y)
        cx.line_to(self.area.x, self.area.y + self.area.h)
        cx.close_path()
        cx.stroke()

    def _renderXAxis(self, cx):
        """Draws the horizontal line representing the X axis"""
        cx.new_path()
        cx.move_to(self.area.x,
                   self.area.y + self.area.h * (1.0 - self.area.origin))
        cx.line_to(self.area.x + self.area.w,
                   self.area.y + self.area.h * (1.0 - self.area.origin))
        cx.close_path()
        cx.stroke()

    def _renderAxis(self, cx):
        """Renders axis"""
        if self.options.axis.x.hide and self.options.axis.y.hide:
            return

        cx.save()
        cx.set_source_rgb(*hex2rgb(self.options.axis.lineColor))
        cx.set_line_width(self.options.axis.lineWidth)

        if not self.options.axis.y.hide:
            if self.yticks:
                for tick in self.yticks:
                    self._renderYTick(cx, tick)

            if self.options.axis.y.label:
                cx.save()
                rotate = self.options.axis.y.rotate
                tickWidth, tickHeight = self._getTickSize(cx, self.yticks,
                                                          rotate)
                label = unicode(self.options.axis.y.label)
                x = self.area.x - tickWidth - 4.0
                y = self.area.y + 0.5 * self.area.h
                self._renderAxisLabel(cx, tickWidth, tickHeight, label, x, y,
                                      True)
                cx.restore()

            self._renderYAxis(cx)

        if not self.options.axis.x.hide:
            fontAscent = cx.font_extents()[0]
            if self.xticks:
                for tick in self.xticks:
                    self._renderXTick(cx, tick, fontAscent)

            if self.options.axis.x.label:
                cx.save()
                rotate = self.options.axis.x.rotate
                tickWidth, tickHeight = self._getTickSize(cx, self.xticks,
                                                          rotate)
                label = unicode(self.options.axis.x.label)
                x = self.area.x + self.area.w / 2.0
                y = self.area.y + self.area.h + tickHeight + 4.0
                self._renderAxisLabel(cx, tickWidth, tickHeight, label, x, y,
                                      False)
                cx.restore()

            self._renderXAxis(cx)

        cx.restore()

    def _renderTitle(self, cx):
        if self.options.title:
            cx.save()
            cx.select_font_face(self.options.titleFont,
                                cairo.FONT_SLANT_NORMAL,
                                cairo.FONT_WEIGHT_BOLD)
            cx.set_font_size(self.options.titleFontSize)

            title = unicode(self.options.title)
            extents = cx.text_extents(title)
            titleWidth = extents[2]

            x = self.area.x + self.area.w / 2.0 - titleWidth / 2.0
            y = cx.font_extents()[0] # font ascent

            cx.move_to(x, y)
            cx.show_text(title)

            cx.restore()

    def _renderLegend(self, cx):
        """This function adds a legend to the chart"""
        if self.options.legend.hide:
            return

        surface_width, surface_height = self.getSurfaceSize()

        # Compute legend dimensions
        padding = 4
        bullet = 15
        width = 0
        height = padding
        keys = self._getDatasetsKeys()
        for key in keys:
            extents = cx.text_extents(key)
            width = max(extents[2], width)
            height += max(extents[3], bullet) + padding
        width = padding + bullet + padding + width + padding

        # Compute legend position
        legend = self.options.legend
        if legend.position.right is not None:
            legend.position.left = (surface_width
                                    - legend.position.right
                                    - width)
        if legend.position.bottom is not None:
            legend.position.top = (surface_height
                                   - legend.position.bottom
                                   - height)

        # Draw the legend
        cx.save()
        cx.rectangle(self.options.legend.position.left,
                     self.options.legend.position.top,
                     width, height)
        cx.set_source_rgba(1, 1, 1, self.options.legend.opacity)
        cx.fill_preserve()
        cx.set_line_width(self.options.stroke.width)
        cx.set_source_rgb(*hex2rgb(self.options.legend.borderColor))
        cx.stroke()

        def drawKey(key, x, y, text_height):
            cx.rectangle(x, y, bullet, bullet)
            cx.set_source_rgb(*self.colorScheme[key])
            cx.fill_preserve()
            cx.set_source_rgb(0, 0, 0)
            cx.stroke()
            cx.move_to(x + bullet + padding,
                       y + bullet / 2.0 + text_height / 2.0)
            cx.show_text(key)

        cx.set_line_width(1)
        x = self.options.legend.position.left + padding
        y = self.options.legend.position.top + padding
        for key in keys:
            extents = cx.text_extents(key)
            drawKey(key, x, y, extents[3])
            y += max(extents[3], bullet) + padding

        cx.restore()


def uniqueIndices(arr):
    """Return a list with the indexes of the biggest element of arr"""
    return range(max([len(a) for a in arr]))


class Area(object):
    """Simple rectangle to hold an area coordinates and dimensions"""

    def __init__(self, x, y, w, h, origin=0.0):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.origin = origin

    def __str__(self):
        msg = "<pycha.chart.Area@(%.2f, %.2f) %.2f x %.2f Origin: %.2f>"
        return  msg % (self.x, self.y, self.w, self.h, self.origin)


class Option(dict):
    """Useful dict that allow attribute-like access to its keys"""

    def __getattr__(self, name):
        if name in self.keys():
            return self[name]
        else:
            raise AttributeError(name)

    def merge(self, other):
        """Recursive merge with other Option or dict object"""
        for key, value in other.items():
            if key in self:
                if isinstance(self[key], Option):
                    self[key].merge(other[key])
                else:
                    self[key] = other[key]


DEFAULT_OPTIONS = Option(
    axis=Option(
        lineWidth=1.0,
        lineColor='#0f0000',
        tickSize=3.0,
        labelColor='#666666',
        labelFont='Tahoma',
        labelFontSize=9,
        labelWidth=50.0,
        tickFont='Tahoma',
        tickFontSize=9,
        x=Option(
            hide=False,
            ticks=None,
            tickCount=10,
            tickPrecision=1,
            range=None,
            rotate=None,
            label=None,
            interval=0,
        ),
        y=Option(
            hide=False,
            ticks=None,
            tickCount=10,
            tickPrecision=1,
            range=None,
            rotate=None,
            label=None,
            interval=0,
        ),
    ),
    background=Option(
        hide=False,
        baseColor=None,
        chartColor='#f5f5f5',
        lineColor='#ffffff',
        lineWidth=1.5,
    ),
    legend=Option(
        opacity=0.8,
        borderColor='#000000',
        hide=False,
        position=Option(top=20, left=40, bottom=None, right=None),
    ),
    padding=Option(
        left=30,
        right=30,
        top=30,
        bottom=30,
    ),
    stroke=Option(
        color='#ffffff',
        hide=False,
        shadow=True,
        width=2
    ),
    yvals=Option(
        show=False,
        inside=False,
        fontSize=11,
        fontColor='#000000',
    ),
    fillOpacity=1.0,
    shouldFill=True,
    barWidthFillFraction=0.75,
    pieRadius=0.4,
    colorScheme=Option(
        name='gradient',
        args=Option(
            initialColor=DEFAULT_COLOR,
            colors=None,
            ),
    ),
    title=None,
    titleFont='Tahoma',
    titleFontSize=12,
)
