class Color:
  """an object representing a color
     provides:
     * hex color string
     * cairo compatible rgba tupple
     * a gtk.gdkColor object
     """

  #TODO: use colormath ?


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
      import gtk
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
      print("** color string parsing failed **")
      print("** input that caused this:", colorStringAlphaTupple)
      print("** exception: %s" % e)
      # fallback
      self.gtkColor = "ff0000"

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
#    return self.gtkColor.to_string()
    return str(self.gtkColor)