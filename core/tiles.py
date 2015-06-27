"""a modRana module with tile handling functionality"""
# -*- coding: utf-8 -*-
import string

def getOSMUrl(lzxy):
    return '%s%d/%d/%d.%s' % (lzxy[0].url, lzxy[1], lzxy[2], lzxy[3], lzxy[0].type)

def getWebMercatorSubstitutionUrl(lzxy):
    template = string.Template(lzxy[0].url)
    return str(template.substitute(z=lzxy[1], x=lzxy[2], y=lzxy[3]))

def getYahooUrl(lzxy):
    layer, z, x, y = lzxy
    y = ((2 ** (z - 1) - 1) - y)
    z += 1
    # I have no idea what the r parameter is, r=0 or no r => grey square
    # -> maybe revision ?
    return '%s&x=%d&y=%d&z=%d&r=1' % (layer.url, x, y, z)

def getGoogleUrl(lzxy):
    return '%s&x=%d&y=%d&z=%d' % (lzxy[0].url, lzxy[2], lzxy[3], lzxy[1])

# modified from:
# http://www.maptiler.org/google-maps-coordinates-tile-bounds-projection/globalmaptiles.py
# (GPL)
def quadTree(tx, ty, zoom):
    """Converts OSM type tile coordinates to Microsoft QuadTree

    :param int tx: x coordinate
    :param int ty: y coordinate
    :param int zoom: zoom level
    :returns str: quad key string
    """
    quadKey = ""
    #		ty = (2**zoom - 1) - ty
    for i in range(zoom, 0, -1):
        digit = 0
        mask = 1 << (i - 1)
        if (tx & mask) != 0:
            digit += 1
        if (ty & mask) != 0:
            digit += 2
        quadKey += str(digit)
    return quadKey

def getQuadtreeUrl(lzxy):
    quadKey = quadTree(lzxy[2], lzxy[3], lzxy[1])
    #  don't know what the g argument is, maybe revision ?
    #  looks like it isn't optional
    return '%s%s?g=452' % (lzxy[0].url, quadKey)

def getQuadtreeSubstitutionUrl(lzxy):
    quadKey = quadTree(lzxy[2], lzxy[3], lzxy[1])
    template = string.Template(lzxy[0].url)
    return str(template.substitute(quadindex=quadKey))

URL_FUNCTIONS = {
    'osm' : getOSMUrl,
    'web_mercator_substitution' : getWebMercatorSubstitutionUrl,
    'yahoo' : getYahooUrl,
    'google' : getGoogleUrl,
    'quadtree' : getQuadtreeUrl,
    'quadtree_substitution' : getQuadtreeSubstitutionUrl
}

def getTileUrl(lzxy):
    handler = URL_FUNCTIONS.get(lzxy[0].coordinates, getOSMUrl)
    return handler(lzxy)

