# -*- coding: utf-8 -*-
# modRana color handling

import logging
log = logging.getLogger("core.color")

# only import GKT libs if GTK GUI is used
from core import gs

if gs.GUIString == "GTK":
    import gtk


class Color(object):
    """an object representing a color
       provides:
       * hex color string
       * cairo compatible rgba tuple
       * a gtk.gdkColor object
       """

    #TODO: use palette ?


    def __init__(self, name, colorStringAlphaTupple=None, cairoColor=None):
        self.name = name
        self.valid = False
        self.gtkColor = None
        self.cairoColor = None
        self.colorStringAlphaTupple = None
        self.alpha = None
        if colorStringAlphaTupple:
            self.setColorFromColorStringAlphaTuple(colorStringAlphaTupple)

    def __str__(self):
        print("color name: %s" % self.name)
        print(self.valid)
        print(self.gtkColor)
        print(self.cairoColor)
        print(self.colorStringAlphaTupple)
        print(self.alpha)

    def isValid(self):
        return self.valid

    def setColorFromColorStringAlphaTuple(self, colorStringAlphaTupple):
        if gs.GUIString == "GTK":
            try:
                import gtk
                (colorString, alpha) = colorStringAlphaTupple
                if colorString == "transparent":
                    colorString = "black"
                    alpha = 0.0
                try:
                    gtkColor = gtk.gdk.color_parse(colorString)
                except ValueError:
                    log.error("** initial color parsing of %s failed" % colorString)
                    # might be a hex color string with alpha at the end
                    if colorString > 6:
                        alphaString = colorString[7:]
                        colorString = colorString[:7]
                        try:
                            alpha = int(alphaString, 16)/255.0
                        except Exception:
                            log.exception("** alpha string parsing failed **")
                            log.error("** alpha string: %s **" % alphaString)
                            log.error("** from color string: %s **" % colorString)
                            log.error("** using numeric alpha or default: %d **" % alpha)

                        log.info("** retrying parsing of trimmed string: %s **" % colorString)
                        gtkColor = gtk.gdk.color_parse(colorString)
                    else:
                        raise

                gtkColorRange = float(2 ** 16)
                cairoR = gtkColor.red / gtkColorRange
                cairoG = gtkColor.green / gtkColorRange
                cairoB = gtkColor.blue / gtkColorRange
                self.setAlpha(float(alpha))
                self.setCairoColor(cairoR, cairoG, cairoB, alpha)
                self.gtkColor = gtkColor
                self.valid = True
            except Exception:
                log.exception("** color string parsing failed **")
                log.error("** input that caused this:", colorStringAlphaTupple)
                # fallback
                self.setAlpha(float(1.0))
                self.setCairoColor(1.0, 0.0, 0.0, float(1.0))
                self.gtkColor = "ff0000"

    def setCairoColor(self, r, g, b, a):
        self.cairoColor = (r, g, b, a)

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