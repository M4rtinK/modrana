#!/usr/bin/python
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
from base_module import ranaModule
import cairo
import gtk
import os
import glob
import fnmatch
from configobj import ConfigObj

def getModule(m,d):
  return(icons(m,d))

class icons(ranaModule):
  """Draw icons"""
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.images = {}
    self.cantLoad = []
    self.imageOrderList = [] # for cache trimming
    self.maxImages = 200 # default 200
    self.themesFolderPath = 'themes/'
    self.defaultTheme = 'default'
    self.currentTheme = self.defaultTheme
    self.themeList = []

    # structure -> color_key:color_object
    self.defaultColors = {} # default color set
    self.colors = {} # main combined color set
    defaultThemeConfig = self.themesFolderPath + '/' + self.defaultTheme + '/theme.conf'
    # load the default set of colors
    defaultColors = self.loadColorsFromFile(defaultThemeConfig)
    self.defaultColors = defaultColors
    self.colors = defaultColors.copy()
    self.colorInfoSubscribers = {}

    #color shortcuts
    self.buttonOutlineColor = (0,0,0,1)
    self.buttonFillColor = (1,1,1,1)

    self.updateThemeList()
    
  def loadFromFile(self,name,w=None,h=None):
    """load icon image to cache or draw the icon with cairo
    TODO: draw all icons through this function ?"""

    # we convert the width and height to int to get rid of some GTK warnings
    w = int(w)
    h = int(h)

    iconPathThemed = self.getCurrentThemePath()
    iconPathDefault = self.getDefaultThemePath()

    (simplePaths,parameterPaths) = self.findUsableIcon(name, [iconPathThemed,iconPathDefault])
    image = None
    # ist there a filename with positional parameters ?
    if parameterPaths:
      result = None
      if fnmatch.filter(parameterPaths, "*%s-above_text.*" % name):
        aboveTextIconPath = fnmatch.filter(parameterPaths, "*%s-above_text.*" % name).pop()
        pixbufInfo = gtk.gdk.pixbuf_get_file_info(aboveTextIconPath)
        # it we get some info about the file, it means that the image is probably pixbufable
        if pixbufInfo:
          (iconInfo,iconW,iconH) = pixbufInfo
          if iconH == 0:
            iconH = 1
          hwRatio = iconW/float(iconH)
          border = min(w,h)*0.1
          targetH = (h*0.55)
          targetW = w - 2*border
          """ try to fit the icon image above the text inside the icon outline,
              with some space between, while respecting appect original aspect ratio"""
          scaledW = targetW
          scaledH = targetW/float(hwRatio)
          if scaledH > targetH:
            scaledH = targetH
            scaledW = targetH * hwRatio
          targetX = border + (targetW-scaledW)/2.0
          targetY = border*(0.9) + ((targetH-scaledH)/2.0)
          try:
            # try to load the icon to pixbuf and get ist original width and height
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(aboveTextIconPath,int(scaledW),int(scaledH))
          except Exception, e:
            print "icons: icon probably corrupted: %s" % aboveTextIconPath
            print "%s" % e
          # get the background icon
#          compositeIcon = self.roundedRectangle(w, h, self.buttonFillColor, self.buttonOutlineColor)
          compositeIcon = cairo.ImageSurface(cairo.FORMAT_ARGB32,w,h)
          ct = cairo.Context(compositeIcon)
          ct2 = gtk.gdk.CairoContext(ct)
          ct2.set_source_pixbuf(pixbuf,targetX,targetY)
          ct2.paint()
          return (compositeIcon,True) # this signalizes that a background might be needed

      if result == None:
        return(self.roundedRectangle(w, h, self.buttonFillColor, self.buttonOutlineColor))
    # just use the classic icon
    elif simplePaths:
      iconPath = simplePaths.pop()
      image = self.getImageSurface(iconPath, w, h)
    # no icon found
    else:
      print "icons: %s not found" % name
      # we use the default button background if the tile is missing
      return(self.roundedRectangle(w, h, self.buttonFillColor, self.buttonOutlineColor),False)

    if(not image): # loading the image probably failed
      return(False)
    w = float(image.get_width())
    h = float(image.get_height())
    return (image,False)

  def getImageSurface(self,path, w, h):
    """load a image given by path to pixbuf and paint ti to image surface,
       then return the image surface"""
    image = None
    try:
      pixbuf = gtk.gdk.pixbuf_new_from_file(path)

      ''' create a new cairo surface to place the image on '''
      image = cairo.ImageSurface(0,w,h)
      ''' create a context to the new surface '''
      ct = cairo.Context(image)
      ''' create a GDK formatted Cairo context to the new Cairo native context '''
      ct2 = gtk.gdk.CairoContext(ct)
      ''' draw from the pixbuf to the new surface '''
      ct2.set_source_pixbuf(pixbuf.scale_simple(w,h,gtk.gdk.INTERP_HYPER),0,0)
      ct2.paint()
      ''' surface now contains the image in a Cairo surface '''
    except Exception, e:
      print "** filename: %s" % path
      print "** exception: %s" % e
    return image

  def getCustomIcon(self,parameterList,w,h):
    """
    there are five positional parameters:
    fill collor,fill opacity, outline color, outline opacity,
    outline width (default 8) and corner radius (default 22)
    to use default value, just don't fill in the positional parameter
    ( len(parameter) == 0 )
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
      outlineWidth = 8

    if len(semicolonSepList[5]):
      cornerRadius = int(semicolonSepList[5])
    else:
      cornerRadius = 22

    # parse the colors (if defined)

    if fillColorString:
      fillColor = self.color("fill", (fillColorString,fillAlpha))
      fillColorRGBATupple = fillColor.getCairoColor()
    else:
      fillColorRGBATupple = self.buttonFillColor


    if outlineColorString:
      outlineColor = self.color("outline", (outlineColorString,outlineAlpha))
      outlineColorRGBATupple = outlineColor.getCairoColor()
    else:
      outlineColorRGBATupple = self.buttonOutlineColor

    # apply the alfa values
    try:
      (r,g,b,a) = fillColorRGBATupple
      fillColorRGBATupple = (r,g,b,fillAlpha)
    except Exception, e:
      print "** wrong fill color code or name: %s" % fillColorString
      print "** exception: %s" % e
      fillColorRGBATupple = self.buttonFillColor

    try:
      (r,g,b,a) = outlineColorRGBATupple
      outlineColorRGBATupple = (r,g,b,outlineAlpha)
    except Exception, e:
      print "** wrong outline color code or name: %s" % fillColorString
      print "** exception: %s" % e
      outlineColorRGBATupple = self.buttonOutlineColor

    # create the icon
    icon = self.roundedRectangle(w, h, fillColorRGBATupple, outlineColorRGBATupple, outlineWidth=outlineWidth, radius=cornerRadius)
    return icon


  def findUsableIcon(self, name, themePathList):
    """due to compatibility reasons, there might be more icon
    file versions for an icon in a them
    -> this function select one of them based on a given set of priorities
    priorities:
    * SVG icons are prefered over PNG
    * PNG is prefered over JPEG
    * icons with centering info are prefered over "plain" icons
    """
    simplePaths = None
    parameterPaths = None
    # list the theme directory
    for path in themePathList:
      simplePaths = glob.glob(path+"%s.*" % name)
      parameterPaths = glob.glob(path+"%s-*.*" % name)
      if parameterPaths or simplePaths:
        break
    return (simplePaths,parameterPaths)

#      possibleTargets = os.listdir(self.getCurrentThemePath())
#      # first try to find a filename with positional parameters
#      if fnmatch.filter(possibleTargets, "%s-*.*" % name):
#        positionalFilenames = fnmatch.filter(possibleTargets, "%s-*.*" % name)
#        print positionalFilenames
#        if fnmatch.filter(positionalFilenames, "%s-above_text.*" % name):
#          print "above text"
#      elif fnmatch.filter(possibleTargets, "%s.*" % name):
#        clasicIconFilename = fnmatch.filter(possibleTargets, "%s.*" % name)[0]
#        print clasicIconFilename

#    matchingExtension = None
#    matchList = []
#    # first, filter out only the prefered-format files
#    for extension in extensionPriority:
#      extensionMatchList = []
#      extensionMatchList.extend(fnmatch.filter(possibleTargets, "*.%s" % extension))
#      extensionMatchList.extend(fnmatch.filter(possibleTargets, "*.%s" % extension.upper()))
#      if extensionMatchList:
#        matchingExtension = extension
#        break
#
#    # second - look if we can find any files with in the targets
#    if matchingExtension:
#      if ("%s-above_text." % namelower) in


#    # second, are there any icons with in-filename position in the list ?
#    iconsWithPosData = filter(lambda x: len(x.split('-')), matchList)
#    if iconsWithPosData:
#      pass
#    else:
#      return

  def firstTime(self):
    self.subscribeColorInfo(self, self.colorsChangedCallback)
    # check if there was some theme used last time
    lastUsedTheme = self.get('currentTheme', self.defaultTheme)
    self.switchTheme(lastUsedTheme)

  def flushIconCache(self):
    """flush the icon cache"""
    self.images = {}
    self.cantLoad = []
    self.imageOrderList = []

  def draw(self,cr,name,x,y,w,h):
    # is the icon already cached ?
    cacheName  = "%fx%f#%s" % (w,h,name)

    if cacheName in self.images.keys():
      self.drawIcon(cr, self.images[cacheName], x, y, w, h)

    # is it in the cant load list ?
#    elif name in self.cantLoad:
#      """the cant load list stores names of icons which errored out during
#         loading from file -> like this we wont load corrupted or
#         nonexisting icons over and over again"""
#      return

    else:
      # run through possible "layers", which are separated by >
      compositedIcon = None
      needBackground = False
      """icon secifications are separated by >,
      which should be seen as a pointing arrow in this context
      we composite from top -> down,
      for example: "icon1>icon2"
      icon1 will be drawn over icon2
      """
      for currentName in reversed(name.split('>')): # we draw top down
        if currentName.split(':')[0] == 'generic':
          if len(currentName.split(':',1)) == 1:
            # just the default cairo drawn icon
            needBackground = False
            genericIcon = self.roundedRectangle(w, h, self.buttonFillColor, self.buttonOutlineColor)
            compositedIcon = self.combineTwoIcons(compositedIcon, genericIcon)
          else:
            # the icon name contains custom positional parameters
            semicolonSepList = currentName.split(':',1)[1].split(';')
            """
            there are five positional parameters:
            fill collor,fill opacity, outline color, outline opacity,
            outline width (default 8) and corner radius (default 22)
            to use default value, just dont fill in the positional parameter
            ( len(parameter) == 0
            """
            needBackground = False
            parametricIcon = self.getCustomIcon(semicolonSepList,w,h)
            compositedIcon = self.combineTwoIcons(compositedIcon, parametricIcon)
        else: # not a generic or parametric icon, try to load from file
          loadingResult = self.loadFromFile(currentName, w, h)
          if (loadingResult == False):
            self.cantLoad.append(currentName)
          else:
            (loadingResult,needBackground) = loadingResult
            compositedIcon = self.combineTwoIcons(compositedIcon, loadingResult)

      # cache and draw the finished icon
      if compositedIcon:
        if needBackground:
          # add a generic icon as a background
          genericIcon = self.roundedRectangle(w, h, self.buttonFillColor, self.buttonOutlineColor)
          compositedIcon = self.combineTwoIcons(genericIcon, compositedIcon)
        cachedIcon = self.storeInCache(cacheName, compositedIcon, w, h)
        self.drawIcon(cr, cachedIcon, x, y, w, h)
        
  def drawIcon(self,cr,icon,x,y,w,h):        
    cr.save()
    cr.translate(x,y)
#    cr.scale(w / icon['w'], h / icon['h'])
    cr.set_source_surface(icon['image'],0,0)
    cr.paint()
    cr.restore()

  def combineTwoIcons(self, backIcon,overIcon):
    """ composite two same-size icons """
    if backIcon and overIcon:
      ct = cairo.Context(backIcon)
      ct2 = gtk.gdk.CairoContext(ct)
      ct2.set_source_surface(overIcon,0,0)
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
      # get the oldest image + remove it ofrem the queue
      oldestImageName = self.imageOrderList.pop(0) # TODO: this might be slow
#      print "trimming cache, %s, %d" % (oldestImageName, len(self.images))
      # remove it from the cache
      del self.images[oldestImageName]
    cacheRepresentation = {'image':image,'w':w,'h':h, 'name':name}
    self.images[name] = cacheRepresentation
    self.imageOrderList.append(name)
    return cacheRepresentation

  def handleMessage(self, message, type, args):
    if message == "themeChanged":
      """handle theme switching"""
      currentTheme = self.get('currentTheme', self.defaultTheme)
      self.switchTheme(currentTheme)
      
  # ported from
  #http://www.cairographics.org/samples/rounded_rectangle/
  def roundedRectangle(self, width, height, fillColor, outlineColor, outlineWidth=None, radius=22):
    """draw a rounded rectangle, fill and outline set the fill and outline rgba color
       r,g,b from 0 to 255, a from 0 to 1"""
    # make the outline propertional to the size of the button
    if outlineWidth == None:
      outlineWidth = min(width,height)*0.05

    x = 0
    y = 0
    image = cairo.ImageSurface(0,int(width),int(height))
    cr = cairo.Context(image)
    pi = 3.1415926535897931
#    aspect        = 1.0     #/* aspect ratio */
##    corner_radius = height / 10.0   #/* and corner curvature radius */
#    corner_radius = height / 7   #/* and corner curvature radius */
##    corner_radius = height / 100   #/* and corner curvature radius */
#
##    radius = corner_radius / aspect

    degrees = pi / 180.0

    # correcting for the line width
    # we also leave a line about one pixel wide free on all sides

    x         = x+5
    y         = y+5
    width         = width-9
    height        = height-9

    cr.new_sub_path()
    cr.arc (x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
    cr.arc (x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees)
    cr.arc (x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees)
    cr.arc (x + radius, y + radius, radius, 180 * degrees, 270 * degrees)
    cr.close_path()

    # inscape to cairo conversion :)
#    (r1, g1, b1, a1) = (fill[0]/256.0,fill[1]/256.0,fill[2]/256.0,fill[3])
#    (r2, g2, b2, a2) = (outline[0]/256.0,outline[1]/256.0,outline[2]/256.0,outline[3])
#
#    (r1, g1, b1, a1) = (fill[0]/256.0,fill[1]/256.0,fill[2]/256.0,fill[3])
#    (r2, g2, b2, a2) = (outline[0]/256.0,outline[1]/256.0,outline[2]/256.0,outline[3])
    cr.set_source_rgba(*fillColor)
    cr.fill_preserve ()
    cr.set_source_rgba(*outlineColor)
    cr.set_line_width(outlineWidth)
    cr.stroke()
    return (image)

  def updateThemeList(self):
    rawFolderContent = os.listdir(self.themesFolderPath)
    self.availableThemes = filter(lambda x: os.path.isdir(self.themesFolderPath + '/' +x) and not x=='.svn',rawFolderContent)

  def getThemeList(self):
    """returna a list of currently available themes (list of folders in the themes folder)"""
    return self.availableThemes

  def getCurrentThemePath(self):
    """returns path to currently active theme"""
    return self.themesFolderPath + '/' + self.currentTheme + '/'

  def getDefaultThemePath(self):
    """returns path to currently active theme"""
    return self.themesFolderPath + '/' + self.defaultTheme + '/'

  def switchTheme(self, newTheme):
    """switch the current theme to another one"""

    # handle bitmap icons
    self.currentTheme = newTheme
    self.flushIconCache()

    # handle colors
    self.colors = self.defaultColors.copy() # revert to default colors first
    themeColors = self.loadColorsFromFile(self.getCurrentThemePath()+'theme.conf')
    self.colors.update(themeColors) # then overwrite theme specific colors
    self.notifyColorSubscribers() # notify color info subscribers
    print "icons: switched theme to: %s" % newTheme
  
  def loadColorsFromFile(self,path):
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
          newColor = self.color(key,colorStringAlphaTupple=(colorString,alpha))
          colorObjects[key] = newColor
      return colorObjects
    else:
      return {}

  def getColors(self):
    """return list of currently available color objects"""
    return self.colors
  
  def subscribeColorInfo(self,module,callback,firstCall=True):
    """subscribe to notifictaions about color map changes"""
    self.colorInfoSubscribers[module] = callback
    if firstCall: # should we call tha callback function right after subscribing ?
      callback(self.getColors())

  def unSubscribeColorInfo(self,module):
    """unsubscribe from notifications about colormap changes"""
    del self.colorInfoSubscribers[module]

  def notifyColorSubscribers(self):
    """notify subscribers that colormap changed"""
    colors = self.getColors()
    for callback in self.colorInfoSubscribers.values():
      callback(colors)

  def colorsChangedCallback(self,colors):
    self.buttonOutlineColor = colors['main_outline'].getCairoColor()
    self.buttonFillColor = colors['main_fill'].getCairoColor()

  class color:
    """an object representing a color
       provides:
       * hex color string
       * cairo compatible rgba tupple
       * a gtk.gdkColor object
       """
    def __init__(self,name,colorStringAlphaTupple=None,cairoColor=None):
      self.name = name
      self.valid = False
      self.gtkColor = None
      self.cairoColor=None
      self.colorStringAlphaTupple = None
      self.alpha = None
      if colorStringAlphaTupple:
        self.setColorFromColorStringAlphaTupple(colorStringAlphaTupple)

    def __str__(self):
      print "color name: %s" % self.name
      print self.valid
      print self.gtkColor
      print self.cairoColor
      print self.colorStringAlphaTupple
      print self.alpha

    def isValid(self):
      return valid

    def setColorFromColorStringAlphaTupple(self, colorStringAlphaTupple):
      try:
        (colorString,alpha) = colorStringAlphaTupple
        gtkColor = gtk.gdk.color_parse(colorString)
        gtkcolorRange = float(2**16)
        cairoR = gtkColor.red/gtkcolorRange
        cairoG = gtkColor.green/gtkcolorRange
        cairoB = gtkColor.blue/gtkcolorRange
        self.setAlpha(alpha)
        self.setCairoColor(cairoR,cairoG,cairoB,alpha)
        self.gtkColor = gtkColor
        self.valid = True
      except Exception, e:
        print "** color string parsing failed **"
        print "** input that coused this: %s" % colorStringAlphaTupple
        print "** exception: %s" % e


    def setCairoColor(self,r,g,b,a):
      self.cairoColor = (r,g,b,a)

    def setAlpha(self, alpha):
      self.alpha = alpha

    def getAlpha(self):
      return self.alpha

    def getGtkColor(self):
      return self.gtkColor

    def getCairoColor(self):
      return self.cairoColor

    def getColorStringAlphaTupple(self):
      return self.colorStringAlphaTupple

    def getColorString(self):
      return self.gtkColor.to_string()