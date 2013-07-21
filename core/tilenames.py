# -*- coding: utf-8 -*-
#-------------------------------------------------------
# Translates between lat/long and the slippy-map tile
# numbering scheme
# 
# http://wiki.openstreetmap.org/index.php/Slippy_map_tilenames
# 
# Written by Oliver White, 2007
# This file is public-domain
#-------------------------------------------------------
from math import *


def numTiles(z):
    return pow(2, z)


def sec(x):
    return 1 / cos(x)


def ll2relativeXY(lat, lon):
    x = (lon + 180) / 360
    y = (1 - log(tan(radians(lat)) + sec(radians(lat))) / pi) / 2
    return x, y


def ll2xy(lat, lon, z):
    n = pow(2, z)
    x = (lon + 180) / 360
    y = (1 - log(tan(radians(lat)) + sec(radians(lat))) / pi) / 2
    return n * x, n * y


def tileXY(lat, lon, z):
    x, y = ll2xy(lat, lon, z)
    return int(x), int(y)


def pxpy2ll(x, y, z):
    n = numTiles(z)
    relY = y / n
    lat = mercatorToLat(pi * (1 - 2 * relY))
    lon = -180.0 + 360.0 * x / n
    return lat, lon


def latEdges(y, z):
    n = numTiles(z)
    unit = 1 / n
    relY1 = y * unit
    relY2 = relY1 + unit
    lat1 = mercatorToLat(pi * (1 - 2 * relY1))
    lat2 = mercatorToLat(pi * (1 - 2 * relY2))
    return lat1, lat2


def lonEdges(x, z):
    n = numTiles(z)
    unit = 360 / n
    lon1 = -180 + x * unit
    lon2 = lon1 + unit
    return lon1, lon2


def tileEdges(x, y, z):
    lat1, lat2 = latEdges(y, z)
    lon1, lon2 = lonEdges(x, z)
    return lat2, lon1, lat1, lon2 # S,W,N,E


def mercatorToLat(mercatorY):
    return degrees(atan(sinh(mercatorY)))


def tileSizePixels():
    return 256
