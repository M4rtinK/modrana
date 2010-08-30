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

def getModule(m,d):
  return(icons(m,d))

class icons(ranaModule):
  """Draw icons"""
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.images = {}
    self.cantLoad = []
    self.load('blank')
#    self.load('generic')
    
  def load(self,name,w=None,h=None):
#    if name=='start':
#      print (w, h)
#      pixbuf = gtk.gdk.pixbuf_new_from_file_at_size('icons/bitmap/start.svg',w,h)
#      image = cairo.ImageSurface(0,w,h)
#      ct = cairo.Context(image)
#      ct2 = gtk.gdk.CairoContext(ct)
#      ct2.set_source_pixbuf(pixbuf,0,0)
#      ct2.paint()
#    else:
    filename = "icons/bitmap/%s.png" % name
    if(not os.path.exists(filename)):
      print "Can't load %s" % filename
      return(0)

    image = None
    try:
      image = cairo.ImageSurface.create_from_png(filename) #TODO: improve this by the pixbuff method ?
    except Exception, e:
      print '** the icon "%s" is possibly corrupted' % name
      print "** filename: %s" % filename

    if(not image):
      return(0)
    w = float(image.get_width())
    h = float(image.get_height())
    self.images[name] = {'image':image,'w':w,'h':h}
    return(1)
  
  def draw(self,cr,name,x,y,w,h):
    if name == 'generic':
      self.roundedRectangle(cr, x, y, w, h)
      return
    elif not name in self.images.keys():
      if(name in self.cantLoad):
        self.roundedRectangle(cr, x, y, w, h)
        return
      elif(not self.load(name,w,h)):
        self.cantLoad.append(name)
        self.roundedRectangle(cr, x, y, w, h)
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

  # ported from
  #http://www.cairographics.org/samples/rounded_rectangle/
  def roundedRectangle(self, cr, x, y, width, height, fill=(146,170,243,1), outline=(60,96,250,1)):
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
    (r1, g1, b1, a1) = (fill[0]/256.0,fill[1]/256.0,fill[2]/256.0,fill[3])
    (r2, g2, b2, a2) = (outline[0]/256.0,outline[1]/256.0,outline[2]/256.0,outline[3])
    cr.set_source_rgba(r1, g1, b1, a1)
    cr.fill_preserve ()
    cr.set_source_rgba(r2, g2, b2, a2)
    cr.set_line_width(8.0)
    cr.stroke()
  