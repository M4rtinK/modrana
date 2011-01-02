#!/usr/bin/env python

import gtk
import rsvg
import cairo


WIDTH, HEIGHT  = 500, 600
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)

ctx = cairo.Context(surface)


window = gtk.Window()
window.set_title("Foo")
window.connect("destroy", gtk.main_quit)
window.show()

svg = rsvg.Handle(file='box.svg')
svg.render_cairo_sub(cr,id='#rect8666')
pixbuf = svg.get_pixbuf(id='#rect8666')

#rsvg.get_pixbuf(svg,cr,'#rect8666')

image = gtk.Image()
image.set_from_pixbuf(pixbuf)
image.show()

window.add(image)

gtk.main()
