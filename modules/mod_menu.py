#!/usr/bin/python
#----------------------------------------------------------------------------
# Handle menus
#----------------------------------------------------------------------------
# Copyright 2008, Oliver White
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
#---------------------------------------------------------------------------
from base_module import ranaModule
import cairo
import pango
import pangocairo
import gtk
import time
import math
import geo

def getModule(m,d):
  return(menus(m,d))

class menus(ranaModule):
  """Handle menus"""
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.menus = {}
    self.lists = {}
    self.listOffset = 0
    self.setupGeneralMenus()
    self.lastActivity = int(time.time())
    self.fullscreen = False
    self.mainScreenCoords = {}
    self.userConfig = {}
    self.notificationModule = None
    self.hideMapSreenButtons = False
    self.lastHideCheckTimestamp = time.time()

  def update(self):
    # check if buttons should be hidden, every second by default
    # TODO: implement this by using a timer ?
    timestamp = time.time()
    if (timestamp - self.lastHideCheckTimestamp) > 1:
      self.lastHideCheckTimestamp = timestamp
      hideDelay = self.get('hideDelay', 'never')
      if hideDelay != 'never': # is button hiding enabled ?
        if (timestamp - self.lastActivity) > int(hideDelay): # have we reached the timeout ?
          self.hideMapSreenButtons = True

  def buttonsHidingOn(self):
    """report whether button hiding is enabled"""
    return self.hideMapSreenButtons

  def drawScreenOverlay(self, cr):
    """Draw an overlay on top of the map, showing various information
    about position etc."""
    (x,y,w,h) = self.get('viewport')

    # Where is the map?
    proj = self.m.get('projection', None)

    dx = min(w,h) / 5.0
    dy = dx

    m = self.m.get('clickHandler', None)
    if(m != None):
      m.registerDraggable(x,y,x+w,y+h, "mapView") # handler for dragging the map
      m.registerXYWH(x,y,x+w,y+h, "menu:screenClicked")

    """check out if button hiding is on and behave accordingly"""
    if self.hideMapSreenButtons:
        (x1,y1) = proj.screenPos(0.6, -0.96)
        text = "tap screen to show menu"
        self.drawText(cr, text, x1, y1, w/3, h, 0) # draw a reminder
        cr.stroke()
    else:
      self.hideMapSreenButtons = False

      # default main button coordinates
      buttons = {}
      buttons['menu'] = (x,y) # main menu button coordinates
      buttons['zoom_in'] = (x,y+dx) # zoom in button coordinates
      buttons['zoom_out'] = (x+dx,y) # zoom out button coordinates
      buttons['fullscreen'] = (x, y+h-dy) # fullscreen button coordinates
      buttons['centre'] = (x+w-dx, y) # centre button coordinates
      buttons['scalebar'] = proj.screenPos(0.15, 0.97) # scalebar coordinates
      plusIcon = 'zoom_in'
      minusIcon = 'zoom_out'

      # possible main button coordinates override
      mode = self.get('mode', None)
      if mode in self.userConfig:
        if 'override_main_buttons' in self.userConfig[mode]:
          # we dont know the orientation, so we use generic icons
          plusIcon = 'plus'
          minusIcon = 'minus'
          item = self.userConfig[mode]['override_main_buttons']

          if 'icon_size' in item:
            size = float(item['icon_size'])
            dx = size * min(w,h)
            dy = dx



          for key in buttons:
            if key in item:
              (px,py,ndx,ndy) = [float(i) for i in item[key]]
              buttons[key] = (px*w+dx*ndx,py*h+dy*ndy)


      # main buttons



      menuIcon = self.get('mode', 'car')

      (x1,y1) = buttons['zoom_out']
      self.drawButton(cr, x1, y1, dx, dy, '', minusIcon, "mapView:zoomOut")
      (x1,y1) = buttons['menu']
      self.drawButton(cr, x1, y1, dx, dy, 'menu', menuIcon, "set:menu:main")
      (x1,y1) = buttons['zoom_in']
      self.drawButton(cr, x1, y1, dx, dy, '', plusIcon, "mapView:zoomIn")


      # draw the maximize icon
      if self.fullscreen:
        icon = 'minimize'
      else:
        icon = 'maximize'

      (x1,y1) = buttons['fullscreen']
      self.drawButton(cr, x1, y1, dx, dy, "", icon, "ms:display:fullscreen:toggle")

      (x1,y1) = buttons['centre']
      self.drawButton(cr, x1, y1, dx, dy, "", 'blue_border', "toggle:centred")

      cr.stroke()
      cr.save()
      (centreX,centreY) = (x1+dx/2.0,y1+dy/2.0)
      cr.translate(centreX,centreY)
      cr.set_line_width(6)
      cr.set_source_rgba(0, 0, 1, 0.45)
      cr.arc(0, 0, 15, 0, 2.0 * math.pi)
      cr.stroke()
      cr.fill()

      if not self.get('centred', False): # draw the position indicator indicator :)
        pos = self.get('pos', None)
        if pos != None:
          (lat1,lon1) = pos
          (lat, lon) = proj.xy2ll(centreX, centreY)
          angle = geo.bearing(lat1,lon1,lat,lon)
          cr.rotate(math.radians(angle))

          (pointX,pointY) = (0,y+dy/3.0)
        else:
          (pointX,pointY) = (0,0)
      else:
        (pointX,pointY) = (0,0)

      cr.set_source_rgb(0.0, 0.0, 0.0)
      cr.set_line_width(10)
      cr.arc(pointX, pointY, 3, 0, 2.0 * math.pi)
      cr.stroke()
      cr.set_source_rgb(1.0, 0.0, 0.0)
      cr.set_line_width(8)
      cr.arc(pointX, pointY, 2, 0, 2.0 * math.pi)
      cr.stroke()
      cr.fill()

      cr.restore()

      (x1,y1) = buttons['scalebar']
      self.drawScalebar(cr, proj,x1,y1,w)

    # master overlay hook - should be visible even when the mapscreen buttons are hidden
    if self.notificationModule:
      self.notificationModule.drawMasterOverlay(cr)

  def needRedraw(self):
    """conveninece function for asking for redraw"""
    self.set('needRedraw', True)

  def showText(self,cr,text,x,y,widthLimit=None,fontsize=40,colorString=None):
    pg = pangocairo.CairoContext(cr)
    # create a layout for your drawing area
    layout = pg.create_layout()
    layout.set_markup(text)
    layout.set_font_description(pango.FontDescription("Sans Serif %d" % fontsize))
    (lw,lh) = layout.get_size()
    if lw == 0 or lh == 0:
      return # no need to draw this + avoid a division by zero
    if colorString: #optinaly set text color
      cr.set_source_color(gtk.gdk.color_parse(colorString))
    if(widthLimit and lw > widthLimit):
      scale = float(pango.SCALE)
      factor = ((widthLimit/(lw/scale)))
      factor = min(factor, 1.0)
      cr.move_to(x,y)
      cr.save()
      cr.scale(factor,factor)
      pg.show_layout(layout)
      cr.restore()
    else:
      cr.move_to(x,y)
      pg.show_layout(layout)

## this ca be used when I can get it to behave like the old show_text based method
#  def drawText(self,cr,text,x,y,w,h,border=0):
#    """pango based text drawing method"""
#    if(not text):
#      return
#    # Put a border around the area
#    if(border != 0):
#      x += w * border
#      y += h * border
#      w *= (1-2*border)
#      h *= (1-2*border)
#    pg = pangocairo.CairoContext(cr)
#    # create a layout for your drawing area
#    layout = pg.create_layout()
#    layout.set_markup(text)
#    layout.set_font_description(pango.FontDescription("Sans Serif 60"))
#    (lw,lh) = layout.get_size()
#    if lw == 0 or lh == 0:
#      return # no need to draw this + avoid a division by zero
#    scale = float(pango.SCALE)
##    factor = min(((w)/(lw/scale)),((h)/(lh/scale)))
#    factorW = (w)/(lw/scale)
#    factorH = (h)/(lh/scale)
##    factor = min(factor, 1.0)
#    factor = min(factorW, factorH)
#    cr.move_to(x,y)
#    cr.save()
#    cr.scale(factor,factor)
#    ratio = max(lw / w, lh / h)
#    cr.set_font_size(60 / ratio)
#    pg.show_layout(layout)
#    cr.restore()

  def drawText(self,cr,text,x,y,w,h,border=0):
    if(not text):
      return
    # Put a border around the area
    if(border != 0):
      x += w * border
      y += h * border
      w *= (1-2*border)
      h *= (1-2*border)
    
    if(0): # optional choose a font
      self.cr.select_font_face(
        'Verdana',
        cairo.FONT_SLANT_NORMAL,
        cairo.FONT_WEIGHT_BOLD)

    # Pick a font size to fit
    test_fontsize = 60
    cr.set_font_size(test_fontsize)
    _s1, _s2, textwidth, textheight, _s3, _s4 = cr.text_extents(text)
    ratio = max(textwidth / w, textheight / h)

    # Draw text
    cr.set_font_size(test_fontsize / ratio)
    cr.move_to(x, y + h)
    cr.show_text(text)

  def drawToggleButtonOld(self, cr, x1, y1, w, h, textIconAction, index):
    """draw an automatic togglable icon
       textActionIcon -> a dictionary of text strings/actions/icons
    """
    self.drawButton(cr, x1, y1, w, h, textIconAction[index][0], textIconAction[index][1], textIconAction[index][2])
        
  def drawButton(self, cr, x1, y1, w, h, text='', icon='generic', action=''):
    """Draw a clickable button, with icon image and text"""
    """NOTE: # delimits the different captions: text_down#text_middle#text_up
       text_up is NOT YET IMPLEMENTED"""
    # Draw icon
    if(icon != None):
      m = self.m.get('icons', None)
      if(m != None):
          m.draw(cr,icon,x1,y1,w,h)

    # Draw text
    cr.set_source_rgb(0, 0, 0.3)
    if text != None:
      textList = text.split('#')
      if len(textList) == 1 and text != None:
        self.drawText(cr, textList[0], x1, y1+0.5*h, w, 0.4*h, 0.15)
      elif len(textList) >= 2:
        self.drawText(cr, textList[0], x1, y1+0.5*h, w, 0.4*h, 0.15)
        self.drawText(cr, textList[1], x1, y1+0.2*h, w, 0.4*h, 0.15)

    # Make clickable
    if(action != None):
      m = self.m.get('clickHandler', None)
      if(m != None):
        m.registerXYWH(x1,y1,w,h, action)

  def resetMenu(self, menu=None):
    print "Menu knows menu changed"
    self.listOffset = 0

  def dragEvent(self,startX,startY,dx,dy,x,y):
    menuName = self.get('menu', None)
    if(menuName == None):
      return
    list = self.lists.get(menuName, None)
    if(list != None):
      self.listOffset += dy
      print "Drag in menu + %f = %f" % (dy,self.listOffset)
    
  def drawMenu(self, cr, menuName):
    """Draw menus"""
#    print "current menu is:%s" % menuName
    # Find the screen
    if not self.d.has_key('viewport'):
      return
    (x1,y1,w,h) = self.get('viewport', None)

#    list = self.lists.get(menuName, None)
#    if(list != None):
#      m = self.m.get(list, None)
#      if(m != None):
#        listHelper = listable_menu(cr,x1,y1,w,h, self.m.get('clickHandler', None), self.listOffset)
#        m.drawList(cr, menuName, listHelper)
#      return

    # Is it a list ?
    if menuName in self.lists.keys(): # TODO: optimize this
      print "drawing list: %s" % menuName
      self.lists[menuName].draw(cr) # draw the list
      return
    
    # Find the menu
    menu = self.menus.get(menuName, None)
    if(menu == None):
      if(0):
        print "Menu %s doesn't exist, returning to main screen" % menuName
        self.set('menu', None)
        self.set('needRedraw', True)
      return



#    if(list != None):
#      m = self.m.get(list, None)
#      if(m != None):
#        listHelper = listable_menu(cr,x1,y1,w,h, self.m.get('clickHandler', None), self.listOffset)
#        m.drawList(cr, menuName, listHelper)
#      return

#    device = self.device
#    if device == 'neo':
#      cols = 3
#      rows = 4
#    elif device == 'n95':
#      cols = 3
#      rows = 4
#    elif device == 'n900':
#      cols = 4
#      rows = 3
#    elif device == 'eee':
#      cols = 4
#      rows = 3

    # Decide how to layout the menu
    if w > h:
      cols = 4
      rows = 3
    elif w < h:
      cols = 3
      rows = 4
    elif w == h:
      cols = 4
      rows = 4
    
    dx = w / cols
    dy = h / rows

    # for each item in the menu
    id = 0
    for y in range(rows):
      for x in range(cols):
        item = menu.get(id, None)
        if(item == None):
          # menu drawing is done, do the master overlay hook
          if self.notificationModule:
            self.notificationModule.drawMasterOverlay(cr)
          return

        # Draw it
        type = item[3]
        if type=='simple':
          (text, icon, action, type) = item
          self.drawButton(cr, x1+x*dx, y1+y*dy, dx, dy, text, icon, action)
        elif type=='toggle':
          index = item[1]
          toggleCount = len(item[0])
          nextIndex = (index + 1)%toggleCount
          # like this, text and corresponding actions can be written on a single line
          # eq: "save every 3 s", "nice icon", "set:saveInterval:3s"
          text = item[0][index][0]
          icon = item[0][nextIndex][1]
          action = item[0][nextIndex][2]

          action+='|menu:toggle#%s#%s|set:needRedraw:True' % (menuName,id)
          self.drawButton(cr, x1+x*dx, y1+y*dy, dx, dy, text, icon, action)
        id += 1

  def register(self, menu, type, module):
    """Register a menu as being handled by some other module"""
    if(type == 'list'):
      self.lists[menu] = module
    else:
      print "Can't register \"%s\" menu - unknown type" % type
    
  def clearMenu(self, menu, cancelButton='set:menu:main'):
    self.menus[menu] = {}
    if(cancelButton != None):
      self.addItem(menu,'','up', cancelButton, 0)

  def addItem(self, menu, text, icon=None, action=None, pos=None):
    i = 0
    while(pos == None):
      if(self.menus[menu].get(i, None) == None):
        pos = i
      i += 1
      if(i > 20):
        print "Menu full, can't add %s" % text
    type = "simple"
    self.menus[menu][pos] = (text, icon, action, type)


  def addToggleItem(self, menu, textIconAction, index=0, pos=None, uniqueName=None):
    """
    add a togglable item to the menu
    textIconAction is a list of texts icons and actions -> (text,icon,action)
    """
    i = 0
    while(pos == None):
      if(self.menus[menu].get(i, None) == None):
        pos = i
      i += 1
      if(i > 20):
        print "Menu full, can't add %s" % text
    type = 'toggle'
    if uniqueName:
      perzist = self.get('persistentToggleButtons', None)
      if perzist == None:
        self.set('persistentToggleButtons', {})
        perzist = {}

      if uniqueName in perzist:
        index = perzist[uniqueName]
      else:
        perzist[uniqueName] = index
        self.set('persistentToggleButtons', perzist)



    self.menus[menu][pos] = (textIconAction, index, uniqueName, type)


  def addListableMenu(self, name, items, parrentAction, descFunction=None, drawFunction=None):
    newListableMenu = self.listableMenu(name, self, items, parrentAction, descFunction, drawFunction,4)
    self.lists[name] = newListableMenu
    return newListableMenu
      

  class listableMenu:
    """a listable menu object"""
    def __init__(self, name, menus, items, parrentAction, descFunction=None, drawFunction=None, displayedItems=3):
      """use custom item and description drawing functions, or use the default ones"""
      self.descFunction = descFunction
      if descFunction==None:
        self.descFunction = self.describeListItem
      self.drawFunction = drawFunction
      if drawFunction==None:
        self.drawFunction=self.drawListItem
      self.index=0 #index of the first item in the current list view
      self.displayedItems = displayedItems
      self.items = items
      self.parrentAction = parrentAction
      self.menus = menus
      self.name = name

    def describeListItem(self, item, index, maxIndex):
      """default item description function
         -> get the needed strings for the default item drawing function"""
      (mainText, secText, action) = item
      indexString = "%d/%d" % (index+1,maxIndex)
      return(mainText, secText, indexString, action)

    def drawListItem(self, cr, item, x, y, w, h, index, descFunction=None):
      """default list item drawing function"""
      if descFunction==None:
        descFunction=self.describeListItem

      # * get the data for this button
      (mainText, secText, indexString, action) = descFunction(item, index, len(self.items))
      # * draw the background
      self.menus.drawButton(cr,x,y,w,h,'','generic', action)

      # * draw the text
      border = 20

      # 1st line: option name
      self.menus.drawText(cr, mainText, x+border, y+border, w-2*border,20)
      # 2nd line: current value
      self.menus.drawText(cr, secText, x + 0.15 * w, y + 0.6 * h, w * 0.85 - border, 20)
      # in corner: row number
      self.menus.drawText(cr, indexString, x+0.85*w, y+3*border, w * 0.15 - border, 20)

    def draw(self, cr):
      """draw the listable menu"""
      (e1,e2,e3,e4,alloc) = self.menus.threePlusOneMenuCoords()
      (x1,y1) = e1
      (x2,y2) = e2
      (x3,y3) = e3
      (x4,y4) = e4
      (w,h,dx,dy) = alloc

      # controls
      # * parent menu
      self.menus.drawButton(cr, x1, y1, dx, dy, "", "up", self.parrentAction)
      # * scroll up
      self.menus.drawButton(cr, x2, y2, dx, dy, "", "up_list", "ml:menu:listMenu:%s;up" % self.name)
      # * scroll down
      self.menus.drawButton(cr, x3, y3, dx, dy, "", "down_list", "ml:menu:listMenu:%s;down" % self.name)

      id = self.index

      # get the number of rows
      globalCount = self.menus.get('listableMenuRows', None) # try to get the global one
      if globalCount==None:
        nrItems = self.displayedItems # use the default value
      else:
        nrItems = int(globalCount) # use the global one
      visibleItems = self.items[id:(id+nrItems)]
      if len(visibleItems): # there must be a nonzero amount of items to avoid a division by zero
        # compute item sizes
        itemBoxW = w-x4
        itemBoxH = h-y4
        itemW = itemBoxW
#        itemH = itemBoxH/len(visibleItems)
        itemH = itemBoxH/nrItems
        for item in visibleItems:
          self.drawFunction(cr,item,x4,y4,itemW,itemH,id) #draw the item
          y4 = y4 + itemH # move the drawing window
          id = id + 1 # increment the current index

    def scrollUp(self):
      if self.index>=1:
        self.index = self.index -1
        self.menus.needRedraw()
    def scrollDown(self):
      if (self.index + 1) < len(self.items):
        self.index = self.index + 1
        self.menus.needRedraw()
    def reset(self):
      self.index = 0


  def setupProfile(self):
    self.clearMenu('data2', "set:menu:main")
    self.setupDataSubMenu()

  def setupMaplayerMenus(self):
    self.clearMenu('layers')
    m = self.m.get('mapTiles', None)
    if(m):
      layers = m.layers()
      for (name, layer) in layers.items():
        self.addItem(
          'layers',
          layer.get('label',name),
          name,
          'set:layer:'+name+'|set:menu:None')
    
  def setupTransportMenu(self):
    """Create menus for routing modes"""
    self.clearMenu('transport')
    for(label, mode) in { \
      'Bike':'cycle',
      'Walk':'foot',
#      'MTB':'cycle',
      'Car':'car',
#      'Hike':'foot',
#      'FastBike':'cycle',
      'Train':'train',
      'Bus':'bus',

#      'Train':'train',
#      'HGV':'hgv'
      }.items():
      self.addItem(
        'transport',                       # menu
        label,                             # label
        label.lower(),                     # icon
        'set:mode:'+mode+"|set:menu:None") # action

  def setupSearchWhereMenu(self):
    self.clearMenu('searchWhere')
    self.addItem('searchWhere', 'view#near', 'generic', 'ms:search:setWhere:view|set:menu:search')
    self.addItem('searchWhere', 'position#near', 'generic', 'ms:search:setWhere:position|set:menu:search')
    """
    TODO:
    * near tracklog
     * start
     * end
     * AROUND (is this doable ? maybe use points from perElevList...)
    * near address
    * near POI (when POI rework is finished)
    """

  def setupSearchMenus(self):
    """Create a load of menus that are just filters for OSM tags"""
    f = open("data/search_menu.txt", "r")
    self.clearMenu('search')
    sectionID = None
    for line in f:
      if(line[0:3] == '== '):
        section = line[3:].strip()
        sectionID = 'search_'+section.lower()
        self.addItem('search', section, section.lower(), 'set:menu:'+sectionID)
        self.clearMenu(sectionID)
      else:
        details = line.strip()
        if(details and sectionID):
          (name,filter) = details.split('|')
          self.addItem(sectionID, name, name.lower(), '')
    f.close()

    
  def setupPoiMenu(self):
    self.clearMenu('poi', "set:menu:main")
    self.addItem('poi', 'POI#list', 'generic', "showPOI:setupCategoryList|set:menu:POICategories")
    self.addItem('poi', 'POI#add new', 'generic', "set:menu:POIAddFromWhere")
    POISelectedAction1 = "showPOI:centerOnActivePOI"
    self.addItem('poi', 'POI#go to', 'generic', "ml:showPOI:setupCategoryList:%s|set:menu:POICategories" % POISelectedAction1)
    POISelectedAction2 = "showPOI:routeToActivePOI"
    self.addItem('poi', 'POI#route to', 'generic', "ml:showPOI:setupCategoryList:%s|set:menu:POICategories" % POISelectedAction2)
    self.addItem('poi', 'search#online', 'generic', "set:menu:searchWhere")

    self.addPOIPOIAddFromWhereMenu() # chain the "add from where menu"

  def addPOIPOIAddFromWhereMenu(self):
    self.clearMenu('POIAddFromWhere', "set:menu:poi")
    self.addItem('POIAddFromWhere', 'entry#manual', 'generic', "ms:showPOI:storePOI:manualEntry")
    self.addItem('POIAddFromWhere', 'map#from', 'generic', "ms:showPOI:storePOI:fromMap")
    self.addItem('POIAddFromWhere', 'position#current', 'generic', "ms:showPOI:storePOI:currentPosition")



  def setupEditBatchMenu(self):
    """this is a menu for editing settings of a batch before running the said batch"""
    self.clearMenu('editBatch', "mapData:refreshTilecount|set:menu:batchTileDl")
    # on exit from the editation menu refresh the tilecount

    # we show the values of the settings
    location = self.get("downloadArea", "here")
    z = self.get('z', 15)
    zoomUp = int(self.get('zoomUpSize', 0))
    zoomDown = int(self.get('zoomDownSize', 0))
    minZ = z - zoomUp
    if minZ < 0:
      minZ = 0
      zoomUp = z

    maxZ = z + zoomDown

    layer = self.get('layer', None)
    maplayers = self.get('maplayers', None)
    print maplayers[layer]['maxZoom']
    if maplayers == None:
      maxZoomLimit == 17
    else:
      maxZoomLimit = maplayers[layer]['maxZoom']

    if maxZ > maxZoomLimit:
      maxZ = 17
      zoomDown = maxZ - z
    radius = int(self.get("downloadSize", 4))*1.25 # to get km, we multiply with 1.25

    # add the buttons for the varius settings
    self.addItem('editBatch', 'where#now: %s' % location, 'generic', 'set:menu:data')
    self.addItem('editBatch', 'radius#now: %dkm' % radius, 'generic', 'set:menu:data2')
    self.addItem('editBatch', 'Zoom down#now: %d - %d = %d' % (z,zoomDown,maxZ), 'generic', 'set:menu:zoomDown')
    self.addItem('editBatch', 'Zoom up#now: %d - %d = %d' % (z,zoomUp,minZ), 'generic', 'set:menu:zoomUp')

    # on exit from submenu, we need to refresh the editBacht menu, so we also send setupEditBatchMenu
    self.setupDataMenu('editBatch|menu:setupEditBatchMenu', 'editBatch')
    self.setupDataSubMenu('editBatch|menu:setupEditBatchMenu', 'editBatch')
    self.setupZoomDownMenu('editBatch|menu:setupEditBatchMenu', 'editBatch')
    self.setupZoomUpMenu('editBatch|menu:setupEditBatchMenu', 'editBatch')

  def setupZoomUpMenu(self, nextMenu='batchTileDl', prevMenu='data'):
    """in this menu, we set the maximal zoom level UP from the current zoomlevel (eq less detail)"""
    self.clearMenu('zoomUp', "set:menu:%s" % prevMenu)
    if nextMenu == 'batchTileDl':
      """if the next menu is the batch tile download menu (eq we are not called from the edit menu)
      we also send a message to refresh the tilecount after pressing the button
      (the edit menu sends the refresh message on exit so it would be redundant)"""
      nextMenu = nextMenu + '|mapData:refreshTilecount'
    self.addItem('zoomUp', '+ 0 up', 'generic', 'set:zoomUpSize:0|set:menu:%s' % nextMenu)
    self.addItem('zoomUp', '+ 1 up', 'generic', 'set:zoomUpSize:1|set:menu:%s' % nextMenu)
    self.addItem('zoomUp', '+ 2 up', 'generic', 'set:zoomUpSize:2|set:menu:%s' % nextMenu)
    self.addItem('zoomUp', '+ 3 up', 'generic', 'set:zoomUpSize:3|set:menu:%s' % nextMenu)
    self.addItem('zoomUp', '+ 5 up', 'generic', 'set:zoomUpSize:5|set:menu:%s' % nextMenu)
    self.addItem('zoomUp', '+ 8 up', 'generic', 'set:zoomUpSize:8|set:menu:%s' % nextMenu)
    self.addItem('zoomUp', 'max up', 'generic', 'set:zoomUpSize:50|set:menu:%s' % nextMenu)

  def setupZoomDownMenu(self, nextMenu='zoomUp', prevMenu='data'):
    """in this menu, we set the maximal zoom level DOWN from the current zoomlevel (eq more detail)"""
    self.clearMenu('zoomDown', "set:menu:%s" % prevMenu)
    self.addItem('zoomDown', '+ 0 down', 'generic', 'set:zoomDownSize:0|set:menu:%s' % nextMenu)
    self.addItem('zoomDown', '+ 1 down', 'generic', 'set:zoomDownSize:1|set:menu:%s' % nextMenu)
    self.addItem('zoomDown', '+ 2 down', 'generic', 'set:zoomDownSize:2|set:menu:%s' % nextMenu)
    self.addItem('zoomDown', '+ 3 down', 'generic', 'set:zoomDownSize:3|set:menu:%s' % nextMenu)
    self.addItem('zoomDown', '+ 5 down', 'generic', 'set:zoomDownSize:5|set:menu:%s' % nextMenu)
    self.addItem('zoomDown', '+ 8 down', 'generic', 'set:zoomDownSize:8|set:menu:%s' % nextMenu)
    self.addItem('zoomDown', 'max down', 'generic', 'set:zoomDownSize:50|set:menu:%s' % nextMenu)
    self.setupZoomUpMenu()

  def setupDataSubMenu(self, nextMenu='zoomDown', prevMenu='data'):
    """here we set the radius for download"""
    self.clearMenu('data2', "set:menu:%s" % prevMenu)
#    self.addItem('data2', '5 km', 'generic', 'set:downloadSize:4|mapData:download|set:menu:editBatch')
    self.addItem('data2', '1 km', 'generic', 'set:downloadSize:1|set:menu:%s' % nextMenu)
    self.addItem('data2', '2 km', 'generic', 'set:downloadSize:2|set:menu:%s' % nextMenu)
    self.addItem('data2', '5 km', 'generic', 'set:downloadSize:4|set:menu:%s' % nextMenu)
    self.addItem('data2', '10 km', 'generic', 'set:downloadSize:8|set:menu:%s' % nextMenu)
    self.addItem('data2', '20 km', 'generic', 'set:downloadSize:16|set:menu:%s' % nextMenu)
    self.addItem('data2', '40 km', 'generic', 'set:downloadSize:32|set:menu:%s' % nextMenu)
    self.addItem('data2', '80 km', 'generic', 'set:downloadSize:64|set:menu:%s' % nextMenu)
    self.addItem('data2', '160 km', 'generic', 'set:downloadSize:128|set:menu:%s' % nextMenu)
    self.setupZoomDownMenu()
    
  def setupDataMenu(self, nextMenu='data2', prevMenu='main'):
    """we can download tiles around "here" (GPS cooridnates), route or the current view"""
    self.clearMenu('data', "set:menu:%s" % prevMenu)
    self.addItem('data', 'Around here', 'generic', 'set:downloadType:data|set:downloadArea:here|set:menu:%s' % nextMenu)
#    self.addItem('data', 'Around route', 'generic', 'set:downloadType:data|set:downloadArea:route|set:menu:%s' % nextMenu)
    self.addItem('data', 'Around route', 'generic', 'set:downloadType:data|set:downloadArea:route|set:menu:chooseRouteForDl')
    self.addItem('data', 'Around view', 'generic', 'set:downloadType:data|set:downloadArea:view|set:menu:%s' % nextMenu)
    self.setupDataSubMenu()
    if self.get("batchMenuEntered", None) == True:
      self.addItem('data', 'back to dl', 'generic', 'set:menu:batchTileDl')

  def setupRouteMenu(self):
     self.clearMenu('route')
     self.addItem('route', 'Point to Point', 'generic', 'set:menu:None|route:selectTwoPoints')
     self.addItem('route', 'Here to Point#Point to Here', 'generic', 'set:menu:None|route:selectOnePoint')
     POISelectedAction2 = "showPOI:routeToActivePOI"
     self.addItem('route', 'Here to POI', 'generic', "ml:showPOI:setupCategoryList:%s|set:menu:POICategories" % POISelectedAction2)
     self.addItem('route', 'to Address#Address', 'generic', 'set:menu:showAdressRoute')
     self.addItem('route', 'Clear', 'generic', 'route:clear|set:menu:None')
     self.addItem('route', 'route#Current', 'generic', 'set:menu:currentRoute')

  def setupGeneralMenus(self):
    self.clearMenu('main', "set:menu:None")
    #self.addItem('main', 'map', 'generic', 'set:menu:layers')
#    self.addItem('main', 'places', 'city', 'set:menu:placenames_categories')
#    self.addItem('main', 'waypoints', 'waypoints', 'set:menu:waypoints_categories')
    self.addItem('main', 'route', 'route', 'set:menu:route')
    self.addItem('main', 'POI', 'poi', 'set:menu:poi')
    self.addItem('main', 'search', 'business', 'set:menu:searchWhere')
    #self.addItem('main', 'view', 'view', 'set:menu:view')
    self.addItem('main', 'options', 'options', 'set:menu:options')
    self.addItem('main', 'download', 'download', 'set:menu:data')
    self.addItem('main', 'mode', 'transport', 'set:menu:transport')
#    self.addItem('main', 'centre', 'centre', 'toggle:centred|set:menu:None')
    self.addItem('main', 'tracklogs', 'tracklogs', 'set:menu:tracklogManagerCathegories')
    self.addItem('main', 'log a track', 'log', 'set:menu:tracklog')
    self.setupTransportMenu()
    self.setupSearchMenus()
    self.setupSearchWhereMenu()
    self.setupMaplayerMenus()
    self.setupPoiMenu()
    self.setupDataMenu()
    self.setupRouteMenu()
    self.clearMenu('options', "set:menu:main") # will be filled by mod_options
#    self.clearMenu('routeProfile', "set:menu:main") # will be filled by mod_routeProfile
    self.lists['places'] = 'placenames'

    self.set('editBatchMenuActive', False) # at startup, the edit batch menu is inactive


  def drawTextToSquare(self, cr, x, y, w, h, text):
    """draw lines of text to a square text box, \n is used as a delimiter"""
#    (x1,y1,w1,h1) = self.get('viewport', None)
#    dx = w / 3
#    dy = h / 4
    border = 30
    spacing = 20
    lines = text.split('\n')
    lineCount = len(lines)
    lineSpace = (h-2*spacing)/lineCount
    i = 0
    for line in lines:
      self.showText(cr, line, x+border, y+i*lineSpace+1*spacing, w-2*border)
      i = i + 1

  def drawThreeItemHorizontalMenu(self, cr, first, second, third):
    """draw a menu, that consists from three horizontal buttons
       this is mostly intended for asking YES/NO questions
       the three parameters are tupples, like this:
       (text,icon,action)"""
    (x1,y1,w,h) = self.get('viewport', None)
#    dx = w1
    dy = h/3

    # portrait and landscape are the same, in this case
    self.drawButton(cr, x1, y1, w, dy, '', first[1], first[2])
    self.drawTextToSquare(cr, x1, y1, w, dy, first[0])

    self.drawButton(cr, x1, y1+dy, w, dy, '', second[1], second[2])
    self.drawTextToSquare(cr, x1, y1+dy, w, dy, second[0])
    
    self.drawButton(cr, x1, y1+2*dy, w, dy, '', third[1], third[2])
    self.drawTextToSquare(cr, x1, y1+2*dy, w, dy, third[0])



  def threePlusOneMenuCoords(self):
    """
    get element coordinates for a menu,
    that combines three normal and one big button/area
    * becuse we want the big button/area to be cca square,
      we move the buttons to the upper part of the screen in portrait mode
      and to the left in landscape

    """
    (x1,y1,w1,h1) = self.get('viewport', None)

    if w1 > h1:
      cols = 4
      rows = 3
    elif w1 < h1:
      cols = 3
      rows = 4
    elif w1 == h1:
      cols = 4
      rows = 4

    dx = w1 / cols
    dy = h1 / rows

    if w1>h1: # landscape
      (elem1) = (x1, y1)
      (elem2) = (x1, y1+1*dy)
      (elem3) = (x1, y1+2*dy)
      (elem4) = (x1+dx, y1)


    elif w1<=h1: # portrait
      (elem1) = (x1, y1)
      (elem2) = (x1+dx, y1)
      (elem3) = (x1+2*dx, y1)
      (elem4) = (x1, y1+dy)

    alloc = (w1,h1,dx,dy)

    return(elem1,elem2,elem3,elem4,alloc)

  def listableMenuCoords(self):
    """listable menu is basicly the same as the three plus one menu,
    eq the listable entries are in the place of the square element"""
    return self.threePlusOneMenuCoords()

  def drawListableMenuControls(self, cr, menuName, parent, scrollMenu):
    """draw the controls for a listable menu"""
    (e1,e2,e3,e4,alloc) = self.threePlusOneMenuCoords()
    (x1,y1) = e1
    (x2,y2) = e2
    (x3,y3) = e3
#    (x4,y4) = e4
    (w1,h1,dx,dy) = alloc
    # * draw "escape" button
    self.drawButton(cr, x1, y1, dx, dy, "", "up", "%s:reset|set:menu:%s" % (parent,parent))
    # * scroll up
    self.drawButton(cr, x2, y2, dx, dy, "", "up_list", "%s:up" % scrollMenu)
    # * scroll down
    self.drawButton(cr, x3, y3, dx, dy, "", "down_list", "%s:down" % scrollMenu)

  def drawListableMenuItems(self, cr, list, scroll, describeItem):
    """draw the items for a listable menu"""
    (e1,e2,e3,e4,alloc) = self.listableMenuCoords()
    (x1,y1) = e1
#    (x2,y2) = e2
#    (x3,y3) = e3
    (x4,y4) = e4
    (w1,h1,dx,dy) = alloc

    category = ""

    for row in (0,1,2): # TODO: dynamic adjustment (how to guess the screensize vs dpi ?)
      index = scroll + row
      numItems = len(list)
      if(0 <= index < numItems):

        (text1,text2,onClick) = describeItem(index, category, list)

        y = y4 + (row) * dy
        w = w1 - (x4-x1)

        # Draw background and make clickable
        self.drawButton(cr,
          x4,
          y,
          w,
          dy,
          "",
          "generic", # background for a 3x1 icon
          onClick)

        border = 20

        self.showText(cr, text1, x4+border, y+border, w-2*border)

        # 2nd line: current value
        self.showText(cr, text2, x4 + 0.15 * w, y + 0.6 * dy, w * 0.85 - border)

        # in corner: row number
        self.showText(cr, "%d/%d" % (index+1, numItems), x4+0.85*w, y + 0.42 * dy, w * 0.15 - border, 20)

  def drawThreePlusOneMenu(self, cr, menuName, parentAction, button1, button2, box):
    """draw a three plus on menu"""
    (e1,e2,e3,e4,alloc) = self.threePlusOneMenuCoords()
    (x1,y1) = e1
    (x2,y2) = e2
    (x3,y3) = e3
    (x4,y4) = e4
    (w,h,dx,dy) = alloc

    (text1, icon1, action1) = button1
    (text2, icon2, action2) = button2
    (boxTextLines, boxAction) = box

    # * draw "escape" button
    self.drawButton(cr, x1, y1, dx, dy, "", "up", "%s:reset|%s" % (menuName, parentAction))
    # * draw the first button
    self.drawButton(cr, x2, y2, dx, dy, text1, icon1, action1)
    # * draw the second button
    self.drawButton(cr, x3, y3, dx, dy, text2, icon2, action2)
    # * draw info box
    w4 = w - x4
    h4 = h - y4
    self.drawButton(cr, x4, y4, w4, h4, "", "generic", boxAction)
    # * draw text to the box
    text = boxTextLines
    self.drawTextToSquare(cr, x4, y4, w4, h4, text) # display the text in the box

  def drawSixPlusOneMenu(self, cr, menuName, parent, fiveButtons, box):
    """draw a three plus on menu
    + support for toggle buttons"""
    (e1,e2,e3,e4,alloc) = self.threePlusOneMenuCoords()
    (x1,y1) = e1
    (x2,y2) = e2
    (x3,y3) = e3
    (x4,y4) = e4
    (w,h,dx,dy) = alloc



    """button: (index,[[text1,icon1,action1],..,[textN,iconN,actionN]])"""

    (boxTextLines, boxAction) = box

    # * draw "escape" button
    self.drawButton(cr, x1, y1, dx, dy, "", "up", "%s:reset|set:menu:%s" % (menuName, parent))
    # * draw the first button
    self.drawToggleButtonOld(cr, x2, y2, dx, dy, fiveButtons[0][0],fiveButtons[0][1])
    # * draw the second button
    self.drawToggleButtonOld(cr, x3, y3, dx, dy, fiveButtons[1][0],fiveButtons[1][1])
    # * draw the third button
    self.drawToggleButtonOld(cr, x4, y4, dx, dy, fiveButtons[2][0],fiveButtons[2][1])
    # * draw the fourth button
    self.drawToggleButtonOld(cr, x4+dx, y4, dx, dy, fiveButtons[3][0],fiveButtons[3][1])
    # * draw the fifth button
    self.drawToggleButtonOld(cr, x4+2*dx, y4, dx, dy, fiveButtons[4][0],fiveButtons[4][1])

    # * draw info box
    w4 = w - x4
    h4 = h - (y4+dy)
    self.drawButton(cr, x4, y4+dy, w4, h4, "", "generic", boxAction)
    # * draw text to the box
    text = boxTextLines
    self.drawTextToSquare(cr, x4, y4+dy, w4, h4, text) # display the text in the box


  def showTextOld(self,cr,text,x,y,widthLimit=None,fontsize=40):
    """DEPRECIATED shof text funtion"""
    if(text):
      cr.set_font_size(fontsize)
      stats = cr.text_extents(text)
      (textwidth, textheight) = stats[2:4]

      if(widthLimit and textwidth > widthLimit):
        cr.set_font_size(fontsize * widthLimit / textwidth)
        stats = cr.text_extents(text)
        (textwidth, textheight) = stats[2:4]

      cr.move_to(x, y+textheight)
      cr.show_text(text)

  def drawScalebar(self, cr, proj, x1, y1, w):

    (x2,y2) = (x1+0.2*w,y1)

#    (x1,y1) = proj.screenPos(0.05, 0.97)
#    (x2,y2) = proj.screenPos(0.25, 0.97)

    (lat1,lon1) = proj.xy2ll(x1,y1)
    (lat2,lon2) = proj.xy2ll(x2,y2)

    dist = geo.distance(lat1,lon1,lat2,lon2)
    # respect the current unit settings
    unit = "km"
    units = self.m.get('units', None)
    if units:
      unitString = units.km2CurrentUnitString(dist, 2, True)
      text = unitString
    else:
      text = "%1.1f km" % unit

    cr.set_source_rgb(0,0,0)
    cr.move_to(x1,y1)
    cr.line_to(x2,y2)
    cr.stroke()
    
# #   add zoomlevel
#    z = self.get('z', 15)
#    text = text + " (zl%d)" % z

    self.boxedText(cr, x1, y1-4, text, 12, 1)

  def boxedText(self, cr, x,y,text, size=12, align=1, border=2, fg=(0,0,0), bg=(1,1,1)):

    cr.set_font_size(12)
    extents = cr.text_extents(text)
    (w,h) = (extents[2], extents[3])

    x1 = x
    if(align in (9,6,3)):
      x1 -= w
    elif(align in (8,5,2)):
      x1 -= 0.5 * w

    y1 = y
    if(align in (7,8,9)):
      y1 += h
    elif(align in (4,5,6)):
      y1 += 0.5 * h

    cr.set_source_rgb(bg[0],bg[1],bg[2])
    cr.rectangle(x1 - border, y1 + border, w +2*border, -(h+2*border))
    cr.fill()

    cr.set_source_rgb(fg[0],fg[1],fg[2])
    cr.move_to(x1,y1)
    cr.show_text(text)
    cr.fill()

  def firstTime(self):
    self.set("menu",None)
    self.userConfig = self.m.get('config', None).userConfig
    # get the notification module (to implement the master overlay)
    self.notificationModule = self.m.get('notification', None)

  def handleMessage(self, message, type, args):
    messageList = message.split('#')
    message = messageList[0]
    if message=='listMenu':
      """manipulate a listable menu
         argument number one is name of the listable menu to manipulate"""
      listMenuName = args[0]
      if listMenuName in self.lists.keys(): # do we have this menu ?
        if args[1]=="up":
          self.lists[listMenuName].scrollUp()
        elif args[1]=="down":
          self.lists[listMenuName].scrollDown()

    elif (message == "rebootDataMenu"):
      self.setupDataMenu() # we are returning from the batch menu, data menu needs to be "rebooted"
      self.set('editBatchMenuActive', False)
    elif(message == "setupEditBatchMenu"):
      self.setupEditBatchMenu()
      self.set('editBatchMenuActive', True)
    elif(message == 'screenClicked'):
      self.lastActivity = int(time.time())
      self.hideMapSreenButtons = False # show the buttons at once
      self.set('needRedraw', True)
    elif(message == 'toggle' and len(messageList) >= 3):
      # toggle a button
      menu = messageList[1]
      pos = int(messageList[2])
      (textIconAction, currentIndex, uniqueName, type) = self.menus[menu][pos]
      maxIndex = len(textIconAction) # maxIndex => number of toggle values
      newIndex = (currentIndex + 1)%maxIndex # make the index ovelap
      # create a new tuple with updated index
      # TODO: maybe use a list instead of a tupple ?

      if uniqueName:
        perzist = self.get('persistentToggleButtons', None)
        if perzist and uniqueName in perzist:
          perzist[uniqueName] = newIndex
          self.set('persistentToggleButtons', perzist)

      self.set(uniqueName, newIndex)
      self.menus[menu][pos] = (textIconAction, newIndex, uniqueName, type)

    
if(__name__ == "__main__"):
  a = menus({},{'viewport':(0,0,600,800)})
  #a.drawMapOverlay(None)
  a.setupSearchMenus()
  