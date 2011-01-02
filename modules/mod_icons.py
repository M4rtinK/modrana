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
from configobj import ConfigObj

def getModule(m,d):
  return(icons(m,d))

class icons(ranaModule):
  """Draw icons"""
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.images = {}
    self.cantLoad = []
    self.themesFolderPath = 'themes/'
    self.defaultTheme = 'default'
    self.currentTheme = self.get('currentTheme', self.defaultTheme)
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

    self.load('blank')
    self.updateThemeList()

#    self.load('generic')
    
  def load(self,name,w=None,h=None):
    """load icon image to cache or draw the icon with cairo
    TODO: draw all cions through this function ?"""
#    if name=='start':
#      print (w, h)
#      pixbuf = gtk.gdk.pixbuf_new_from_file_at_size('icons/bitmap/start.svg',w,h)
#      image = cairo.ImageSurface(0,w,h)
#      ct = cairo.Context(image)
#      ct2 = gtk.gdk.CairoContext(ct)
#      ct2.set_source_pixbuf(pixbuf,0,0)
#      ct2.paint()
#    else:
#    filename = "icons/bitmap/%s.png" % name
    iconPath = None
    iconPathThemed = self.getCurrentThemePath() + '%s.png' % name
    iconPathDefault = self.themesFolderPath + '/' + self.defaultTheme + '/%s.png' % name
    if(os.path.exists(iconPathThemed)):
      iconPath = iconPathThemed
    elif(os.path.exists(iconPathDefault)):
      iconPath = iconPathDefault
    else:
      print "icons: %s not found" % name
      return(0)

    image = None
    try:
      image = cairo.ImageSurface.create_from_png(iconPath) #TODO: improve this by the pixbuff method ?
    except Exception, e:
      print '** the icon "%s" is possibly corrupted' % name
      print "** filename: %s" % filename
      print "** exception: %s" % e

    if(not image):
      return(0)
    w = float(image.get_width())
    h = float(image.get_height())
    self.images[name] = {'image':image,'w':w,'h':h}
    return(1)

  def firstTime(self):
    self.subscribeColorInfo(self, self.colorsChangedCallback)

  def updateThemeList(self):
    rawFolderContent = os.listdir(self.themesFolderPath)
    self.availableThemes = filter(lambda x: not os.path.isdir(x),rawFolderContent)

  def getThemeList(self):
    """returna a list of currently available themes (list of folders in the themes folder)"""
    return self.availableThemes

  def getCurrentThemePath(self):
    """returns path to currently active theme"""
    return self.themesFolderPath + '/' + self.currentTheme + '/'

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

  def flushIconCache(self):
    """flush the icon cache"""
    self.images = {}

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
      
    def setCairoColor(self,r,g,b,a):
      self.cairoColor = (r,g,b,a)

    def setAlpha(self, alpha):
      self.alpha = alpha

    def getAlpha(self):
      return alpha

    def getGtkColor(self):
      return self.gtkColor

    def getCairoColor(self):
      return self.cairoColor

    def getColorStringAlphaTupple(self):
      return self.colorStringAlphaTupple

  def draw(self,cr,name,x,y,w,h):
    if name == 'generic':
      self.roundedRectangle(cr, x, y, w, h, self.buttonFillColor, self.buttonOutlineColor)
      return
    elif not name in self.images.keys():
      if(name in self.cantLoad):
        self.roundedRectangle(cr, x, y, w, h, self.buttonFillColor, self.buttonOutlineColor)
        return
      elif(not self.load(name,w,h)):
        self.cantLoad.append(name)
        self.roundedRectangle(cr, x, y, w, h, self.buttonFillColor, self.buttonOutlineColor)
        return
#    if not name in self.images.keys():
#      if(name in self.cantLoad):
#        name = 'generic'
#      elif(not self.load(name,w,h)):
#        self.cantLoad.append(name)
#        name='generic'
        
    icon = self.images[name]
    cr.save()
    cr.translate(x,y)
    cr.scale(w / icon['w'], h / icon['h'])
    cr.set_source_surface(icon['image'],0,0)
    cr.paint()
    cr.restore()

  def handleMessage(self, message, type, args):
    if message == "themeChanged":
      """handle theme switching"""
      currentTheme = self.get('currentTheme', self.defaultTheme)
      self.switchTheme(currentTheme)
      
  # ported from
  #http://www.cairographics.org/samples/rounded_rectangle/
  def roundedRectangle(self, cr, x, y, width, height, fill, outline):
    """draw a rounded rectangle, fill and outline set the fill and outline rgba color
       r,g,b from 0 to 255, a from 0 to 1"""
    pi = 3.1415926535897931
    aspect        = 1.0     #/* aspect ratio */
#    corner_radius = height / 10.0   #/* and corner curvature radius */
    corner_radius = height / 7   #/* and corner curvature radius */

    radius = corner_radius / aspect
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
    cr.set_source_rgba(*fill)
    cr.fill_preserve ()
    cr.set_source_rgba(*outline)
    cr.set_line_width(8.0)
    cr.stroke()
  