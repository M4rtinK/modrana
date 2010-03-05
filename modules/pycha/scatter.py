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

from pycha.line import LineChart


class ScatterplotChart(LineChart):

    def _renderChart(self, cx):
        """Renders a scatterplot"""

        def drawSymbol(point, size=2):
            ox = point.x * self.area.w + self.area.x
            oy = point.y * self.area.h + self.area.y
            cx.move_to(ox-size, oy)
            cx.line_to(ox+size, oy)
            cx.move_to(ox, oy-size)
            cx.line_to(ox, oy+size)

        def preparePath(storeName, size=2):
            cx.new_path()
            for point in self.points:
                if point.name == storeName:
                    drawSymbol(point, size)
            cx.close_path()

        cx.save()

        cx.set_line_width(self.options.stroke.width)
        # TODO: self.options.stroke.shadow
        for key in self._getDatasetsKeys():
            cx.set_source_rgb(*self.colorScheme[key])
            preparePath(key)
            cx.stroke()

        cx.restore()

    def _renderLines(self, cx):
        # We don't need lines in the background
        pass
