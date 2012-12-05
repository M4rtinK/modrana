# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Draw position marker.
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
import math
from math import radians


def getModule(m, d, i):
  return PositionMarker(m, d, i)


class PositionMarker(RanaModule):
  """A sample pyroute module"""

  def __init__(self, m, d, i):
    RanaModule.__init__(self, m, d, i)

  def drawMapOverlay(self, cr):
    """Draw an "own position" marker"""

    # Where are we?
    pos = self.get('pos', None)
    if pos is None:
      return
    (lat, lon) = pos

    # Where is the map?
    proj = self.m.get('projection', None)
    if proj is None:
      return
    if not proj.isValid():
      return

    # Where are we on the map?
    x1, y1 = proj.ll2xy(lat, lon)

    # What are we?
    angle = self.get('bearing', 0)

    speed = self.get('speed', 0)
    if speed is None:
      self.drawStandingCircle(cr, x1, y1)
    elif speed < 1: # do we look like we are moving ?
      self.drawStandingCircle(cr, x1, y1) # draw TangoGPS style marker without bearing
    else:
      self.drawMovingCircle(cr, x1, y1, angle) # draw TangoGPS style marker with bearing
      #     Draw yellow/black triangle showing us
      #      self.drawArrow(cr, x1, y1, angle)


  def drawMovingCircle(self, cr, x1, y1, angle):
    cr.save()

    # rotate the marker according to our bearing
    cr.translate(x1, y1) # we move the coordinates center to where we want the center of the marker
    cr.rotate(radians(angle))

    # circle

    # background (black) circle
    cr.set_source_rgb(0.0, 0.0, 0.0)
    cr.set_line_width(11)
    cr.arc(0, 0, 16, 0, 2.0 * math.pi)
    cr.stroke()

    # foreground orange circle
    cr.set_source_rgb(1.0, 0.5, 0.0)
    cr.set_line_width(5)
    cr.arc(0, 0, 16, 0, 2.0 * math.pi)
    cr.stroke()

    # line
    lineLength = 27
    # background black line
    cr.set_source_rgb(0.0, 0.0, 0.0)
    cr.set_line_width(6)
    cr.arc(0, 0, 6, 0, 2.0 * math.pi) # we want round ends :)
    cr.arc(0, 0 - lineLength, 6, 0, 2.0 * math.pi)
    cr.fill()
    cr.set_line_width(12)
    cr.move_to(0, 0)
    cr.line_to(0, 0 - lineLength)
    cr.stroke()

    cr.fill()

    # foreground yellow line
    cr.set_source_rgb(1.0, 1.0, 0.0)
    cr.set_line_width(3)
    cr.arc(0, 0, 3, 0, 2.0 * math.pi)
    cr.arc(0, 0 - lineLength, 3, 0, 2.0 * math.pi)
    cr.fill()
    cr.set_line_width(6)
    cr.move_to(0, 0)
    cr.line_to(0, 0 - lineLength)
    cr.stroke()
    cr.fill()

    cr.restore()

  def drawStandingCircle(self, cr, x1, y1):
    cr.save()

    # rotate the marker according to our bearing
    cr.translate(x1, y1) # we move the coordinates center to where we want the center of the marker

    # circle

    # background (black) circle
    cr.set_source_rgb(0.0, 0.0, 0.0)
    cr.set_line_width(11)
    cr.arc(0, 0, 16, 0, 2.0 * math.pi)
    cr.stroke()

    # foreground orange circle
    cr.set_source_rgb(1.0, 0.5, 0.0)
    cr.set_line_width(5)
    cr.arc(0, 0, 16, 0, 2.0 * math.pi)
    cr.stroke()

    # centerpoint
    cr.set_source_rgb(0.0, 0.0, 0.0)
    cr.set_line_width(6)
    cr.arc(0, 0, 6, 0, 2.0 * math.pi) # we want round ends :)
    cr.fill()
    cr.set_source_rgb(1.0, 1.0, 0.0)
    cr.set_line_width(4)
    cr.arc(0, 0, 4, 0, 2.0 * math.pi) # we want round ends :)
    cr.fill()
    cr.stroke()

    cr.fill()

    cr.restore()

  def drawArrow(self, cr, x1, y1, angle):
    cr.set_source_rgb(1.0, 1.0, 0.0)
    cr.save()
    cr.translate(x1, y1)
    cr.rotate(radians(angle))
    cr.move_to(-10, 15)
    cr.line_to(10, 15)
    cr.line_to(0, -15)
    cr.fill()
    cr.set_source_rgb(0.0, 0.0, 0.0)
    cr.set_line_width(3)
    cr.move_to(-10, 15)
    cr.line_to(10, 15)
    cr.line_to(0, -15)
    cr.close_path()
    cr.stroke()
    cr.restore()
