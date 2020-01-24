# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Projection code (lat/long to screen conversions)
#----------------------------------------------------------------------------
# Copyright 2007-2008, Oliver White
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
#----------------------------------------------------------------------------
from modules.base_module import RanaModule
from core.tilenames import *
from core import geo
from core.constants import DEFAULT_COORDINATES
from math import *
import math


def getModule(*args, **kwargs):
    return Projection(*args, **kwargs)


class Projection(RanaModule):
    """Projection code (lat/long to screen conversions)"""

    # HOW DOES IT WORK:
    # - there are basically two modes:
    # * current position tracking
    #  => set view + recentre + 2*find edges
    # * map dragging
    #  => nudge + 1*find edges

    # TODO:
    # - why is find edges called twice for position tracking ?
    # - don't redraw the whole map for a small nudge
    #  -> currently even for a 1 pixel nudge, the whole screen is redrawn
    # - use a mechanism similar to nudging for faster tracklog drawing
    #  -> show the trackpoints so no ll2xy would be needed

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)

        self.xyValid = False
        self.llValid = False
        self.needsEdgeFind = False

        # Scale is the number of display pixels per projected unit
        self.scale = tileSizePixels()

    #    self.initView()


    def firstTime(self):
        # make absolutely sure that centering is turned on on startup
        # otherwise we don't know what to show -> black screen => NOT GOOD :)

        pos = self.get("pos", None)
        if pos:
            (lat, lon) = pos # use position from last time
        else: # use default position
            self.set("pos", DEFAULT_COORDINATES) # Brno
            (lat, lon) = DEFAULT_COORDINATES

        self.recentre(lat, lon)

        z = int(self.get('z', 15))
        self.zoom = z

        viewport = self.get('viewport', None)
        if viewport is None:
        # initial size, we dont know the screen size
        # handleResize should trigger when the window is actually created
        # then the view would be set to the correct size
        # also, the viewport is stored, so after fist start, it should be available at startup
            (sx, sy, sw, sh) = (0, 0, 800, 480)
        else:
            (sx, sy, sw, sh) = viewport
        self.setView(sx, sy, sw, sh)

        self.findEdges()

        self.set('centred', True) # set centering to True at start to get setView to run

    #    px, py = latlon2xy(self.lat,self.lon,15)
    #    px1 = px - 0.5 * w / scale
    #    px2 = px + 0.5 * w / scale
    #    py1 = py - 0.5 * h / scale
    #    py2 = py + 0.5 * h / scale
    #    pdx = px2 - px1
    #    pdy = py2 - py1
    #
    #    self.z15px1 = px1
    #    self.z15pdx = pdx
    #    self.z15pdy = pdy


    def isValid(self):
        """Test if the module contains all the information needed to do conversions"""
        return self.xyValid and self.llValid

    def setView(self, x, y, w, h):
        """Setup the display"""
        #    self.log.debug("setting view xywh:%d,%d,%d,%d" % (x,y,w,h))
        self.w = w
        self.h = h
        self.xc = x + self.w
        self.yc = y + self.h
        self.xyValid = True
        if self.needsEdgeFind:
            self.findEdges()

    def recentre(self, lat, lon, zoom=None):
        """Move the projection to a particular geographic location
        (with optional zoom level)"""
        #    self.log.debug("recentering to: %f,%f" % (lat,lon))
        self.lat = lat
        self.lon = lon
        if zoom is not None:
            self.implementNewZoom(zoom)
            # note: implementNewZoom calls findEdges, hence the else: statement
        else:
            self.findEdges()
        self.llValid = True

    def setZoomXY(self, x, y, zoom):
        """Set a new zoom level while keeping the coordinates corresponding to
        x,y on the same place on the screen.
        This is used for example for double-click zoom so that you can repeatedly
        double-click a point on the map and the point will still stay in the
        same place on the screen.
        """

        # disable centering as this will almost always shift map center
        self.set("centred", False)
        # compute display unit position on the new zoom level
        lat, lon = self.xy2ll(x, y)
        newX, newY = self.llz2xy(lat, lon, zoom)
        # get the difference from map center
        dx = (x-newX)/2.0
        dy = (y-newY)/2.0
        # nudge the map center to compensate
        self.nudge(dx, dy)
        # implement the new zoom level
        self.implementNewZoom(zoom)

    def setZoom(self, value, isAdjustment=False):
        """Change the zoom level, keeping same map centre
        if isAdjustment is true, then value is relative to current zoom
        otherwise it's an absolute value"""
        if isAdjustment:
            # TODO: maybe we don't want all zoom levels?
            self.implementNewZoom(self.zoom + value)
        else:
            self.implementNewZoom(value)

    def limitZoom(self):
        """Check the zoom level, and move it if necessary to one of
        the 'allowed' zoom levels"""
        if self.zoom < 6:
            self.zoom = 6

    def implementNewZoom(self, zoom):
        """Change the zoom level"""
        self.zoom = int(zoom)
        #    self.limitZoom()
        self.findEdges()

    def findEdges(self):
        """Update the projection meta-info based on its fundamental parameters"""
        #    self.log.debug("find edges %f,%f" % (self.lat,self.lon))
        if not self.xyValid or not self.llValid:
            # If the display is not known yet, then we can't do anything, but we'll
            # mark it as something that needs doing as soon as the display
            # becomes valid
            self.needsEdgeFind = True
            return

        # Find the map centre in projection units
        self.px, self.py = ll2xy(self.lat, self.lon, self.zoom)
        # Find the map edges in projection units
        self.px1 = self.px - 0.5 * self.w / self.scale
        self.px2 = self.px + 0.5 * self.w / self.scale
        self.py1 = self.py - 0.5 * self.h / self.scale
        self.py2 = self.py + 0.5 * self.h / self.scale

        # Store width and height in projection units, just to save time later
        self.pdx = self.px2 - self.px1
        self.pdy = self.py2 - self.py1

        # Calculate the bounding box
        # ASSUMPTION: (that the projection is regular and north-up)
        self.N, self.W = pxpy2ll(self.px1, self.py1, self.zoom)
        self.S, self.E = pxpy2ll(self.px2, self.py2, self.zoom)

        # Mark the meta-info as valid
        self.needsEdgeFind = False

    def findEdgesForZl(self, zl, scale, side=256):
        """Get projection meta-info based on its fundamental parameters for a given zl"""
        tileSide = side * scale
        #    tileSide = 256
        # Find the map centre in projection units
        px, py = ll2xy(self.lat, self.lon, zl)
        # Find the map edges in projection units
        px1 = px - 0.5 * self.w / tileSide
        px2 = px + 0.5 * self.w / tileSide
        py1 = py - 0.5 * self.h / tileSide
        py2 = py + 0.5 * self.h / tileSide
        return px1, px2, py1, py2

    def handleResize(self, newW, newH):
        """When the window resizes, set the view accordingly."""
        self.setView(0, 0, newW, newH) # set the screen to new resolution
        self.findEdges() # find edges for this new resolution

    def screenPos(self, px, py):
        """Given a position on screen (where 0,0 is top-left and 1,1 is bottom right) get the coordinates"""
        x = self.xc + ((px - 1) * self.w)
        y = self.yc + ((py - 1) * self.h)
        return x, y

    def screenWidth(self, pw):
        """Proportional width to pixels(0=0, 1=full screen height)."""
        if pw > 1:
            pw = 1
        if pw < 0:
            pw = 0
        return pw * self.w

    def screenHeight(self, py):
        """Proportional height to pixels (0=0, 1=full screen height)."""
        if py > 1:
            py = 1
        if py < 0:
            py = 0
        return py * self.h

    #  def screenBBoxLL(self):
    #    """get lat,lon of upper left and lower right screen corners
    #       -> get the screen bounding box in geographical units"""
    #    (lat1,lon1) = self.xy2ll(0,0)
    #    (lat2,lon2) = self.xy2ll(self.w,self.h)
    #
    #    return (lat1,lon1,lat2,lon2)
    #
    #  def screenBBoxpxpy(self):
    #    """get lat,lon of upper left and lower right screen corners
    #       -> get the screen bounding box in geographical units"""
    #    (lat1,lon1) = self.xy2ll(0,0)
    #    (lat2,lon2) = self.xy2ll(self.w,self.h)
    #
    #    return (lat1,lon1,lat2,lon2)

    def getCurrentPospxpy(self):
        """returns px py coordinates of the current position, or None"""
        pos = self.get('pos', None)
        if pos:
            (lat, lon) = pos
            return self.ll2pxpy(lat, lon)
        else:
            return None

    def getCurrentPosXY(self):
        """returns x y coordinates of the current position, or None"""
        pos = self.get('pos', None)
        if pos:
            (lat, lon) = pos
            return self.ll2xy(lat, lon)
        else:
            return None

    def getScreenCentreLL(self):
        if self.lat and self.lon:
            return self.lat, self.lon
        else:
            return None

    def nudge(self, dx, dy):
    #    self.log.debug("nudging by: %d,%d" % (dx,dy))
        """Move the map by a number of pixels relative to its current position"""
        if dx == 0 and dy == 0:
            return
            # Calculate the lat/long of the pixel offset by dx,dy from the centre,
        # and centre the map on that

        newXC = self.px - dx / self.scale
        newYC = self.py - dy / self.scale
        self.lat, self.lon = pxpy2ll(newXC, newYC, self.zoom)
        self.findEdges()

    def ll2xy(self, lat, lon):
        """Convert geographic units to display units"""
        px, py = ll2xy(lat, lon, self.zoom)
        x = (px - self.px1) * self.scale
        y = (py - self.py1) * self.scale
        return x, y

    def llz2xy(self, lat, lon, zoom):
        """Convert geographic units to display units at given zoom level"""
        px, py = ll2xy(lat, lon, zoom)
        px1, px2, py1, py2 = self.findEdgesForZl(zoom, self.scale)
        x = (px - px1) * self.scale
        y = (py - py1) * self.scale
        return x + self.w/2.0, y+self.h/2.0

    def ll2pxpy(self, lat, lon):
        """Convert geographic units to projection units"""
        px, py = ll2xy(lat, lon, self.zoom)
        return px, py

    def ll2pxpyRel(self, lat, lon):
        """Convert geographic units to relative projection units"""
        px = (lon + 180) / 360
        py = (1 - log(tan(radians(lat)) + sec(radians(lat))) / pi) / 2
        return px, py

    def pxpyRel2xy(self, px, py):
        """Convert relative projection units
        to display units"""
        n = 2 ** self.zoom
        (px, py) = (px * n, py * n)
        x = self.w * (px - self.px1) / self.pdx
        y = self.h * (py - self.py1) / self.pdy
        return x, y

    def pxpy2xy(self, px, py):
        """Convert projection units to display units"""
        x = self.w * (px - self.px1) / self.pdx
        y = self.h * (py - self.py1) / self.pdy
        return x, y

    def xy2ll(self, x, y):
        """Convert display units to geographic units"""
        px = self.px1 + x / self.scale
        py = self.py1 + y / self.scale
        lat, lon = pxpy2ll(px, py, self.zoom)
        return lat, lon

    def pxpy2ll(self, px, py):
        """Convert projection units to geographic units"""
        return pxpy2ll(px, py, self.zoom)


    def onscreen(self, x, y):
        """Test if a position (in display units) is visible"""
        return 0 <= x < self.w and 0 <= y < self.h

    def relXY(self, x, y):
        return x / self.w, y / self.h

    def km2px(self, distanceInKm):
        """(experimental) km to screen pixel conversion"""
        pi = 3.1415926535897931 # we just use this as pi instead of importing math
        R = 6371.0 # km to the center of Earth
        C = 2 * pi * R # circumference of Earth
        degreesPerKm = 360 / C # how many degrees is a kilometre
        degreesPerPixel = ((self.N - self.S) / self.h) # how many degrees is a pixel (with current zoom)
        # we get degrees equivalent from kilometers and then convert it to pixels
        return (distanceInKm * degreesPerKm) / degreesPerPixel

    # doesnt seem to work correctly
    #  def px2km(self, distanceInPixel):
    #    """(experimental) screen pixel to km conversion"""
    #    pi = 3.1415926535897931 # we just use this as pi instead of importing math
    #    R = 6371.0 # km to the center of Earth
    #    C = 2*pi*R # circumference of Earth
    #    degreesPerKm = 360/C # how many degrees is a kilometre
    #    degreesPerPixel = ((self.N - self.S)/self.h) # how many degrees is a pixel (with current zoom)
    #    return (distanceInPixel * degreesPerPixel)/degreesPerKm

    def screenRadius(self):
        """Return the centerpoint and radius of a circle encompassing the screen."""
        (centreXpixel, centreYpixel) = self.screenPos(0.5, 0.5)
        (centreX, centreY) = self.xy2ll(centreXpixel, centreYpixel)
        #ASUMPTION: screen is rectangular
        (cornerXpixel, cornerYpixel) = self.screenPos(0, 0) # we take the coordinates of one corner of the screen
        (cornerX, cornerY) = self.xy2ll(cornerXpixel, cornerYpixel) # we convert them to projection coordinates
        (anotherCornerXpixel, anotherCornerYpixel) = self.screenPos(1,
                                                                    1) # we take the coordinates of another corner of the screen
        (anotherCornerX, anotherCornerY) = self.xy2ll(anotherCornerXpixel,
                                                      anotherCornerYpixel) # we convert them to projection coordinates
        # radius = diagonal/2
        radius = geo.distance(anotherCornerX, anotherCornerY, cornerX, cornerY) / 2.0
        return centreX, centreY, radius # we return the centre coordinates and the radius

    def radiusEdges(self, lat, lon, radiusInKm):
        """return edges of a box around the given point and radius
        (for downloading tiles for a given radius around a point)"""
        (x, y) = self.ll2xy(lat, lon)
        radiusInPixel = self.km2px(radiusInKm)
        side = radiusInPixel * 2
        #    px1 = x - 0.5 * side / self.scale
        #    px2 = x + 0.5 * side / self.scale
        #    py1 = y - 0.5 * side / self.scale
        #    py2 = y + 0.5 * side / self.scale
        px1 = x - 0.5 * side
        px2 = x + 0.5 * side
        py1 = y - 0.5 * side
        py2 = y + 0.5 * side
        return px1, py1, px2, py2

    def num2deg(self, xtile, ytile):
        """tile to degrees, implementation from OSM wiki"""
        zoom = 15 # for testing we use zl 15
        n = 2.0 ** zoom
        lon_deg = xtile / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
        lat_deg = math.degrees(lat_rad)
        return lat_deg, lon_deg

    def pixelBearing(self, x1, y1, x2, y2):
        """Bearing from one point to another in degrees (0-360) from pixel coordinates"""
        dX = x2 - y1
        dY = y2 - y1
        y = sin(radians(dY)) * cos(radians(x2))
        x = cos(radians(x1)) * sin(radians(x2)) - \
            sin(radians(x1)) * cos(radians(x2)) * cos(radians(dY))
        bearing = degrees(atan2(y, x))
        if bearing < 0.0:
            bearing += 360.0
        return bearing


#  def shiftllPoint(self, x, y, distanceInKm, where='west'):
#    """shift points coordinates by a given distance in km,
#    may not work very well in polar regions (or near Greenwich)"""
#    R = 6371.0
#    C = 2*math.pi*R
#    gradesPerKm = 360/C
#    shiftBy = gradesPerKm * distanceInKm
#    if where == 'west':
#      return(x-shiftBy)
#    elif where == 'east':
#      return(x+shiftBy)
#    elif where == 'north':
#      return(y+shiftBy)
#    elif where == 'south':
#      return(y-shiftBy)




