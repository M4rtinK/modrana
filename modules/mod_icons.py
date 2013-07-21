# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Draw icons
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
import os
import glob
import fnmatch
# for some reason one import method works
# on Fremantle and other everywhere (?) else"""
try:
    from modules.configobj.configobj import ConfigObj # everywhere
except Exception:
    import sys

    e = sys.exc_info()[1]
    print(e)
    print("icons: trying alternative configobj import method")
    from configobj import ConfigObj # Fremantle


# only import GKT libs if GTK GUI is used
from core import gs

if gs.GUIString == "GTK":
    import gtk
    import cairo
    from core.color import Color
from core import constants


def getModule(m, d, i):
    return Icons(m, d, i)


class Icons(RanaModule):
    """Draw icons"""

    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)

        self.defaultTheme = constants.DEFAULT_THEME_ID
        self.cantLoad = []
        self.imageOrderList = [] # for cache trimming
        self.maxImages = 200 # default 200
        self.images = {}

        self.currentTheme = self.defaultTheme
        self.themeList = []

        # structure -> color_key:color_object
        self.defaultColors = {} # default color set
        self.colors = {} # main combined color set
        defaultThemeConfig = os.path.join(
            self.modrana.paths.getThemesFolderPath(),
            self.defaultTheme,
            'theme.conf'
        )
        # TODO: make themes GUI toolkit independent
        if gs.GUIString == "GTK":
            # load the default set of colors
            defaultColors = self.loadColorsFromFile(defaultThemeConfig)
            self.defaultColors = defaultColors
            self.colors = defaultColors.copy()
            self.colorInfoSubscribers = {}

            #color shortcuts
            self.buttonOutlineColor = (0, 0, 0, 1)
            self.buttonFillColor = (1, 1, 1, 1)


    def firstTime(self):
        # TODO: make themes GUI toolkit independent
        if gs.GUIString == "GTK":
            self.subscribeColorInfo(self, self.colorsChangedCallback)
            # check if there was some theme used last time
            lastUsedTheme = self.get('currentTheme', self.defaultTheme)
            self.switchTheme(lastUsedTheme)

    def getIconByName(self, name, returnPixbuf=False):
        """"get icon from current theme by exact name match
            return None if no icon is found"""
        # first check in the current theme folder
        iconPathThemed = self.getCurrentThemePath()
        # and then check the default folder if the theme folder
        # doesnt contain this icon
        iconPathDefault = self.getDefaultThemePath()
        simplePaths = None
        for path in (iconPathThemed, iconPathDefault):
            simplePaths = glob.glob(os.path.join(path, "%s.*" % name))
            if simplePaths:
                break
        if simplePaths:
            iconPath = simplePaths[0] # just take the first one
            # check if it is loadable
            if gtk.gdk.pixbuf_get_file_info(iconPath):
                pixbuf = gtk.gdk.pixbuf_new_from_file(iconPath)
                if returnPixbuf:
                    return pixbuf
                else:
                    w = pixbuf.get_width()
                    h = pixbuf.get_height()
                    # paint the pixbuf on an image surface
                    icon = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
                    ct = cairo.Context(icon)
                    ct2 = gtk.gdk.CairoContext(ct)
                    ct2.set_source_pixbuf(pixbuf, 0, 0)
                    ct2.paint()
                    # return the image surface
                    return icon
            else:
                # image is probably not loadable
                print("icon: icon not loadable (by pixbuf loader): %s" % name)
                return None
        else:
            print("icons: no icon found with name: %s" % name)
            return None


    def loadFromFile(self, name, w=None, h=None, scale=True, noBackground=False):
        """load icon image to cache or draw the icon with cairo
        TODO: draw all icons through this function ?"""

        # we convert the width and height to int to get rid of some GTK warnings
        w = int(w)
        h = int(h)

        iconPathThemed = self.getCurrentThemePath()
        iconPathDefault = self.getDefaultThemePath()

        (simplePaths, parameterPaths) = self.findUsableIcon(name, [iconPathThemed, iconPathDefault])

        parameterPaths.extend(simplePaths)

        image = None
        # is there a filename with positional parameters ?
        if parameterPaths:
            result = None
            aboveTextIconPath = fnmatch.filter(parameterPaths, "*%s.*" % name).pop()
            pixbufInfo = gtk.gdk.pixbuf_get_file_info(aboveTextIconPath)
            # it we get some info about the file, it means that the image is probably pixbufable
            if pixbufInfo:
                (iconInfo, iconW, iconH) = pixbufInfo
                if iconH == 0:
                    iconH = 1
                hwRatio = iconW / float(iconH)
                border = min(w, h) * 0.1
                targetH = (h * 0.55)
                targetW = w - 2 * border
                # try to fit the icon image above the text inside the icon outline,
                # with some space between, while respecting original aspect ratio"""
                scaledW = targetW
                scaledH = targetW / float(hwRatio)
                if scaledH > targetH:
                    scaledH = targetH
                    scaledW = targetH * hwRatio
                targetX = border + (targetW - scaledW) / 2.0
                targetY = border * 0.9 + ((targetH - scaledH) / 2.0)
                pixbuf = None
                try:
                    # try to load the icon to pixbuf and get its original width and height
                    pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(aboveTextIconPath, int(scaledW), int(scaledH))
                except Exception:
                    import sys

                    e = sys.exc_info()[1]
                    print("icons: icon probably corrupted: %s" % aboveTextIconPath)
                    print("%s" % e)
                if pixbuf:
                    compositeIcon = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
                    ct = cairo.Context(compositeIcon)
                    ct2 = gtk.gdk.CairoContext(ct)
                    ct2.set_source_pixbuf(pixbuf, targetX, targetY)
                    ct2.paint()
                    return compositeIcon, True # this signalizes that a background might be needed
                else:
                    return self.roundedRectangle(w, h, self.buttonFillColor, self.buttonOutlineColor), False
            if result is None:
                return self.roundedRectangle(w, h, self.buttonFillColor, self.buttonOutlineColor), False
        # just use the classic icon
        elif simplePaths:
            iconPath = simplePaths.pop()
            if scale:
                image = self.getImageSurface(iconPath, w, h)
            else:
                image = self.getImageSurface(iconPath)

        # no icon found
        else:
            print("icons: %s not found" % name)
            # we use the default button background if the tile is missing
            return self.roundedRectangle(w, h, self.buttonFillColor, self.buttonOutlineColor), False

        if not image: # loading the image probably failed
            return False
        #    w = float(image.get_width())
        #    h = float(image.get_height())
        return image, False

    def getImageSurface(self, path, w=None, h=None):
        """load a image given by path to pixbuf and paint it to an image surface,
           then return the image surface"""
        try:
            pixbuf = gtk.gdk.pixbuf_new_from_file(path)
            #if width or height are not set, we take them from the pixbuf
            #if both are not set, we disable scaling

            (w, h, scale) = self._getValidParams(w, h, pixbuf)

            # create a new cairo surface to place the image on
            image = cairo.ImageSurface(0, w, h)
            # create a context to the new surface
            ct = cairo.Context(image)
            # create a GDK formatted Cairo context to the new Cairo native context
            ct2 = gtk.gdk.CairoContext(ct)
            # draw from the pixbuf to the new surface
            if scale:
                pixbuf = pixbuf.scale_simple(w, h, gtk.gdk.INTERP_HYPER)
            ct2.set_source_pixbuf(pixbuf, 0, 0)
            ct2.paint()
            # surface now contains the image in a Cairo surface
        except Exception:
            import sys

            e = sys.exc_info()[1]
            print("** loading image to pixbuf failed")
            print("** filename: %s" % path)
            print("** exception: %s" % e)
            return None
        return image

    def _getValidParams(self, w, h, pixbuf):
        """return width and height
           just return w or h if they are set,
           if they are None, use values from the given pixbuf"""
        if w is None:
            w = pixbuf.get_width()
        if h is None:
            h = pixbuf.get_height()
        if w is None and h is None:
            scale = False
        else:
            scale = True
        return w, h, scale

    def getCustomIcon(self, parameterList, w, h):
        """
        there are six positional parameters:
        fill color,fill opacity, outline color, outline opacity,
        outline width (default 8) and corner radius (default 22)
        to use default value, just don't fill in the positional parameter
        ( len(parameter) == 0 )
        USAGE:
        corner radius: default=22, 0 does right angle corners


        EXAMPLE: generic:green;1.0;blue;0.5;10;15
        """
        # check if the list has proper length
        if len(parameterList) != 6:
            return None
        semicolonSepList = parameterList
        # process the positional parameters
        if len(semicolonSepList[0]):
            fillColorString = semicolonSepList[0]
        else:
            fillColorString = None

        if len(semicolonSepList[1]):
            fillAlpha = float(semicolonSepList[1])
        else:
            fillAlpha = 1.0

        if len(semicolonSepList[2]):
            outlineColorString = semicolonSepList[2]
        else:
            outlineColorString = None

        if len(semicolonSepList[3]):
            outlineAlpha = float(semicolonSepList[3])
        else:
            outlineAlpha = 1.0

        if len(semicolonSepList[4]):
            outlineWidth = int(semicolonSepList[4])
        else:
            outlineWidth = 4

        if len(semicolonSepList[5]):
            cornerRadius = int(semicolonSepList[5])
        else:
            cornerRadius = 22

        # parse the colors (if defined)

        if fillColorString:
            fillColor = Color("fill", (fillColorString, fillAlpha))
            fillColorRGBATuple = fillColor.getCairoColor()
        else:
            fillColorRGBATuple = self.buttonFillColor

        if outlineColorString:
            outlineColor = Color("outline", (outlineColorString, outlineAlpha))
            outlineColorRGBATuple = outlineColor.getCairoColor()
        else:
            outlineColorRGBATuple = self.buttonOutlineColor

        # apply the alpha values
        try:
            (r, g, b, a) = fillColorRGBATuple
            fillColorRGBATuple = (r, g, b, fillAlpha)
        except Exception:
            import sys

            e = sys.exc_info()[1]
            print("** wrong fill color code or name: %s" % fillColorString)
            print("** exception: %s" % e)
            fillColorRGBATuple = self.buttonFillColor

        try:
            (r, g, b, a) = outlineColorRGBATuple
            outlineColorRGBATuple = (r, g, b, outlineAlpha)
        except Exception:
            import sys

            e = sys.exc_info()[1]
            print("** wrong outline color code or name: %s" % fillColorString)
            print("** exception: %s" % e)
            outlineColorRGBATuple = self.buttonOutlineColor

        # create the icon
        icon = self.roundedRectangle(w, h, fillColorRGBATuple, outlineColorRGBATuple, outlineWidth, cornerRadius)
        return icon


    def findUsableIcon(self, name, themePathList):
        """due to compatibility reasons, there might be more icon
        file versions for an icon in a theme
        -> this function select one of them based on a given set of priorities
        priorities:
        * SVG icons are preferred over PNG
        * PNG is preferred over JPEG
        * icons with centering info are preferred over "plain" icons
        """
        simplePaths = None
        parameterPaths = None
        # list the theme directory
        for path in themePathList:
            simplePaths = glob.glob(os.path.join(path, "%s.*") % name)
            parameterPaths = glob.glob(os.path.join(path, "%s-*.*" % name))
            if parameterPaths or simplePaths:
                break
        return simplePaths, parameterPaths

    def flushIconCache(self):
        """flush the icon cache"""
        self.images = {}
        self.cantLoad = []
        self.imageOrderList = []

    def draw(self, cr, name, x, y, w, h):
        # is the icon already cached ?
        cacheName = "%fx%f#%s" % (w, h, name)

        if cacheName in self.images.keys():
            self.drawIcon(cr, self.images[cacheName], x, y, w, h)
        else:
            # run through possible "layers", which are separated by >
            compositedIcon = None
            needBackground = False
            # icon specifications are separated by >,
            # which should be seen as a pointing arrow in this context
            # we composite top -> down,
            # for example: "icon1>icon2"
            # icon1 will be drawn over icon2
            for currentName in reversed(name.split('>')): # we draw top down

                if currentName.split(':')[0] == 'generic':
                    if currentName == "generic":
                        # just the default cairo drawn icon
                        needBackground = False
                        genericIcon = self.roundedRectangle(w, h, self.buttonFillColor, self.buttonOutlineColor)
                        compositedIcon = self.combineTwoIcons(compositedIcon, genericIcon)
                    else:
                        # the icon name contains custom positional parameters
                        semicolonSepList = currentName.split(':', 1)[1].split(';')
                        # there are five positional parameters:
                        # fill color,fill opacity, outline color, outline opacity,
                        # outline width (default 8) and corner radius (default 22)
                        # to use default value, just don't fill in the positional parameter
                        # ( len(parameter) == 0
                        needBackground = False
                        parametricIcon = self.getCustomIcon(semicolonSepList, w, h)
                        compositedIcon = self.combineTwoIcons(compositedIcon, parametricIcon)
                elif currentName.split(':')[0] == 'above':
                    # "above" means that we have an icon that we want to position above any text that
                    # can be on the button
                    loadingResult = self.loadFromFile(currentName.split(':')[1], w, h)
                    if loadingResult == False:
                        self.cantLoad.append(currentName)
                    else:
                        (loadingResult, needBackground) = loadingResult
                        needBackground = False
                        compositedIcon = self.combineTwoIcons(compositedIcon, loadingResult)

                elif currentName.split(':')[0] == 'center':
                    # "center" means that we have an icon which we want to center inside the button
                    # there re two parameters - icon name and border width
                    # EXAMPLE: center:more;0.1;0.5
                    # -> icon name: more
                    # -> border width: 10% of shortest icon side
                    # -> 50% opacity

                    # parse the parameters
                    semicolonSepList = currentName.split(':', 1)[1].split(';')
                    iconName = semicolonSepList[0]

                    # try to get the icon
                    icon = self.getIconByName(iconName, returnPixbuf=True)
                    if icon is None:
                        self.cantLoad.append(iconName)
                        # get a generic icon
                        genericIcon = self.roundedRectangle(w, h, self.buttonFillColor, self.buttonOutlineColor)
                        # submit it instead of the icon that failed to load
                        compositedIcon = self.combineTwoIcons(compositedIcon, genericIcon)
                    else:
                        w = int(w)
                        h = int(h)

                        needBackground = False
                        background = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
                        # scale to fit and properly place inside the button size

                        iw = icon.get_width()
                        ih = icon.get_height()
                        # get usable width and height
                        if len(semicolonSepList) >= 2:
                            borderWidth = float(semicolonSepList[1])
                        else:
                            borderWidth = 0
                            # get opacity
                        if len(semicolonSepList) >= 3:
                            opacity = float(semicolonSepList[2])
                        else:
                            opacity = 1.0
                        if borderWidth >= 1 or borderWidth <= 0:
                            border = 0
                        else:
                            border = min(w, h) * borderWidth
                        uw = float(w - border * 2)
                        uh = float(h - border * 2)

                        # division by zero defence
                        if not (iw == 0 or iw == 0 or uw == 0 or uh == 0):

                            if iw >= ih: # "landscape" icon
                                newH = uh
                                newW = iw * (uh / ih)
                                if newW > uw:
                                    newW = uw
                                    newH = ih * (newW / iw)

                            else: # "portrait" icon
                                newW = uw
                                newH = ih * (newW / iw)
                                if newH > uh:
                                    newH = uh
                                    newW = iw * (newH / ih)

                            # shift to center
                            dx = border + (uw - newW) / 2.0
                            dy = border + (uh - newH) / 2.0

                            # crete contexts
                            ct = cairo.Context(background)
                            ctBack = gtk.gdk.CairoContext(ct)
                            icon = icon.scale_simple(int(newW), int(newH), gtk.gdk.INTERP_HYPER)
                            ctBack.set_source_pixbuf(icon, dx, dy)

                            # paint the icon on image surface
                            ctBack.paint_with_alpha(opacity)

                            # composite the result with other layers
                            compositedIcon = self.combineTwoIcons(compositedIcon, background)

                else: # not a generic or parametric icon, try to load from file
                    loadingResult = self.loadFromFile(currentName, w, h)
                    if loadingResult == False:
                        self.cantLoad.append(currentName)
                    else:
                        (loadingResult, needBackground) = loadingResult
                        compositedIcon = self.combineTwoIcons(compositedIcon, loadingResult)

            # cache and draw the finished icon
            if compositedIcon:
                if needBackground:
                    # add a generic icon as a background
                    genericIcon = self.roundedRectangle(w, h, self.buttonFillColor, self.buttonOutlineColor)
                    compositedIcon = self.combineTwoIcons(genericIcon, compositedIcon)
                cachedIcon = self.storeInCache(cacheName, compositedIcon, w, h)
                self.drawIcon(cr, cachedIcon, x, y, w, h)

    def drawIcon(self, cr, icon, x, y, w, h):
        cr.save()
        cr.translate(x, y)
        cr.set_source_surface(icon['image'], 0, 0)
        cr.paint()
        cr.restore()

    def combineTwoIcons(self, backIcon, overIcon):
        """ composite two same-size icons """
        if backIcon and overIcon:
            ct = cairo.Context(backIcon)
            ct2 = gtk.gdk.CairoContext(ct)
            ct2.set_source_surface(overIcon, 0, 0)
            ct2.paint()
            return backIcon
        elif not backIcon and not overIcon:
            return None
        elif backIcon:
            return backIcon
        else:
            return overIcon

    def storeInCache(self, name, image, w, h):
        """store an item in cache and return the cache representation"""
        # check if the cache is full
        if len(self.images) >= self.maxImages:
            # get the oldest image + remove it from the queue
            oldestImageName = self.imageOrderList.pop(0) # TODO: this might be slow
            #      print("trimming cache, %s, %d" % (oldestImageName, len(self.images)))
            # remove it from the cache
            del self.images[oldestImageName]
        cacheRepresentation = {'image': image, 'w': w, 'h': h, 'name': name}
        self.images[name] = cacheRepresentation
        self.imageOrderList.append(name)
        return cacheRepresentation

    def handleMessage(self, message, messageType, args):
        if message == "themeChanged":
            # handle theme switching
            currentTheme = self.get('currentTheme', self.defaultTheme)
            self.switchTheme(currentTheme)

    # ported from
    #http://www.cairographics.org/samples/rounded_rectangle/
    def roundedRectangle(self, width, height, fillColor, outlineColor, outlineWidth=None, radius=22):
        """draw a rounded rectangle, fill and outline set the fill and outline rgba color
           r,g,b from 0 to 255, a from 0 to 1"""
        # make the outline proportional to the size of the button
        if outlineWidth is None:
            outlineWidth = min(width, height) * 0.05
        elif outlineWidth < 1.0: # add support for proportional outlines
            outlineWidth *= min(width, height)

        x = 0
        y = 0

        image = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(width), int(height))
        cr = cairo.Context(image)
        pi = 3.1415926535897931

        degrees = pi / 180.0

        # correcting for the line width
        # we also leave a line about one pixel wide free on all sides

        x += 5
        y += 5
        width -= 9
        height -= 9

        cr.new_sub_path()
        if radius <= 0: # no round corners, just draw a box
            cr.move_to(x, y)
            cr.line_to(x + width, y)
            cr.line_to(x + width, y + height)
            cr.line_to(x, y + height)
        else:
            cr.arc(x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
            cr.arc(x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees)
            cr.arc(x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees)
            cr.arc(x + radius, y + radius, radius, 180 * degrees, 270 * degrees)
        cr.close_path()

        cr.set_source_rgba(*fillColor)
        cr.fill_preserve()
        cr.set_source_rgba(*outlineColor)
        cr.set_line_width(outlineWidth)
        cr.stroke()
        return image

    def getCurrentThemePath(self):
        """returns path to currently active theme"""
        return os.path.join(self.modrana.paths.getThemesFolderPath(), self.currentTheme)

    def getDefaultThemePath(self):
        """returns path to currently active theme"""
        return os.path.join(self.modrana.paths.getThemesFolderPath(), self.defaultTheme)

    def switchTheme(self, newTheme):
        """switch the current theme to another one"""

        # handle bitmap icons
        self.currentTheme = newTheme
        self.flushIconCache()

        # handle colors
        self.colors = self.defaultColors.copy() # revert to default colors first
        themeColors = self.loadColorsFromFile(os.path.join(self.getCurrentThemePath(), 'theme.conf'))
        self.colors.update(themeColors) # then overwrite theme specific colors
        self.notifyColorSubscribers() # notify color info subscribers
        print("icons: switched theme to: %s" % newTheme)

    def loadColorsFromFile(self, path):
        """load color definitions from file"""
        config = ConfigObj(path)
        if 'colors' in config:
            colors = config['colors']
            colorObjects = {}
            for key in colors.keys():
                content = colors[key]
                if len(content) == 2: # hex color/color name and alpha as float 0-1
                    colorString = content[0]
                    alpha = float(content[1])
                    # create a new modRana color instance
                    newColor = Color(key, colorStringAlphaTupple=(colorString, alpha))
                    colorObjects[key] = newColor
            return colorObjects
        else:
            return {}

    def getColors(self):
        """return list of currently available color objects"""
        return self.colors

    def subscribeColorInfo(self, module, callback, firstCall=True):
        """subscribe to notifications about color map changes"""
        # TODO: make themes GUI toolkit independent
        if gs.GUIString == "GTK":
            self.colorInfoSubscribers[module] = callback
            if firstCall: # should we call tha callback function right after subscribing ?
                callback(self.getColors())

    def unSubscribeColorInfo(self, module):
        """un-subscribe from notifications about colormap changes"""
        del self.colorInfoSubscribers[module]

    def notifyColorSubscribers(self):
        """notify subscribers that colormap changed"""
        colors = self.getColors()
        for callback in self.colorInfoSubscribers.values():
            callback(colors)

    def colorsChangedCallback(self, colors):
        self.buttonOutlineColor = colors['main_outline'].getCairoColor()
        self.buttonFillColor = colors['main_fill'].getCairoColor()