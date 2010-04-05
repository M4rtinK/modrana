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
import time
from listable_menu import listable_menu

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

  def drawMapOverlay(self, cr):
    """Draw an overlay on top of the map, showing various information
    about position etc."""
    hideDelay = self.get('hideDelay', 'never')
    (x,y,w,h) = self.get('viewport')

    # Where is the map?
    proj = self.m.get('projection', None)

    dx = min(w,h) / 5.0
    dy = dx

    m = self.m.get('clickHandler', None)
    if(m != None):
      m.registerDraggable(x,y,x+w,y+h, "mapView") # handler for dragging the map
      m.registerXYWH(x,y,x+w,y+h, "menu:screenClicked")

    if hideDelay != 'never': # is button hiding on ?
      currentTimestamp = int(time.time())
      lastActivity = self.lastActivity
      if (currentTimestamp - lastActivity) > int(hideDelay): # have we reached the timeout ?
        (x1,y1) = proj.screenPos(0.6, -0.96)
        text = "tap screen to show menu"
        self.drawText(cr, text, x1, y1, w/3, h, 0) # draw a reminder
        return



    self.drawButton(cr, x+dx, y, dx, dy, '', "zoom_out", "mapView:zoomOut")
    self.drawButton(cr, x, y, dx, dy, '', "hint", "set:menu:main")
    self.drawButton(cr, x, y+dy, dx, dy, '', "zoom_in", "mapView:zoomIn")




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

    list = self.lists.get(menuName, None)
    if(list != None):
      m = self.m.get(list, None)
      if(m != None):
        listHelper = listable_menu(cr,x1,y1,w,h, self.m.get('clickHandler', None), self.listOffset)
        m.drawList(cr, menuName, listHelper)
      return
    
    # Find the menu
    menu = self.menus.get(menuName, None)
    if(menu == None):
      if(0):
        print "Menu %s doesn't exist, returning to main screen" % menuName
        self.set('menu', None)
        self.set('needRedraw', True)
      return


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
          return
        
        # Draw it
        (text, icon, action) = item
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
    self.menus[menu][pos] = (text, icon, action)

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
      'MTB':'cycle',
      'Car':'car',
      'Hike':'foot',
      'FastBike':'cycle',
      'Train':'train',
      'HGV':'hgv'}.items():
      self.addItem(
        'transport',                       # menu
        label,                             # label
        label.lower(),                     # icon
        'set:mode:'+mode+"|set:menu:None") # action

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
        print sectionID
        self.clearMenu(sectionID)
      else:
        details = line.strip()
        if(details and sectionID):
          (name,filter) = details.split('|')
          self.addItem(sectionID, name, name.lower(), '')
    f.close()

    
  def setupPoiMenu(self):
    self.clearMenu('poi', "set:menu:None")
    for i in("Show map", "Go to", "Delete"):
      self.addItem('poi', i, i, 'set:menu:showPOI')
      
    self.addItem('poi', 'Route to', 'generic', "set:menu:showPOIRoute")
    self.addItem('poi', 'route#clear', 'generic', "route:clear|set:menu:main")

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
    self.addItem('zoomUp', '+ 1 up', 'generic', 'set:zoomUpSize:1|set:menu:%s' % nextMenu)
    self.addItem('zoomUp', '+ 2 up', 'generic', 'set:zoomUpSize:2|set:menu:%s' % nextMenu)
    self.addItem('zoomUp', '+ 3 up', 'generic', 'set:zoomUpSize:3|set:menu:%s' % nextMenu)
    self.addItem('zoomUp', '+ 5 up', 'generic', 'set:zoomUpSize:5|set:menu:%s' % nextMenu)
    self.addItem('zoomUp', '+ 8 up', 'generic', 'set:zoomUpSize:8|set:menu:%s' % nextMenu)
    self.addItem('zoomUp', 'max up', 'generic', 'set:zoomUpSize:50|set:menu:%s' % nextMenu)

  def setupZoomDownMenu(self, nextMenu='zoomUp', prevMenu='data'):
    """in this menu, we set the maximal zoom level DOWN from the current zoomlevel (eq more detail)"""
    self.clearMenu('zoomDown', "set:menu:%s" % prevMenu)
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
    self.addItem('data', 'Around route', 'generic', 'set:downloadType:data|set:downloadArea:route|set:menu:%s' % nextMenu)
    self.addItem('data', 'Around view', 'generic', 'set:downloadType:data|set:downloadArea:view|set:menu:%s' % nextMenu)
    self.setupDataSubMenu()
    if self.get("batchMenuEntered", None) == True:
      self.addItem('data', 'back to dl', 'generic', 'set:menu:batchTileDl')

  def setupRouteMenu(self):
     self.clearMenu('route')
     self.addItem('route', 'Point to Point', 'generic', 'set:menu:None|route:selectTwoPoints')
     self.addItem('route', 'Here to Point', 'generic', 'set:menu:None')
     self.addItem('route', 'Here to POI', 'generic', 'set:menu:showPOIRoute')
     self.addItem('route', 'Clear', 'generic', 'route:clear|set:menu:None')
     self.addItem('route', 'Current', 'generic', 'set:menu:currentRoute')

  def setupGeneralMenus(self):
    self.clearMenu('main', "set:menu:None")
    #self.addItem('main', 'map', 'generic', 'set:menu:layers')
    self.addItem('main', 'places', 'city', 'set:menu:placenames_categories')
#    self.addItem('main', 'waypoints', 'waypoints', 'set:menu:waypoints_categories')
    self.addItem('main', 'route', 'route', 'set:menu:route')
    self.addItem('main', 'POI', 'POI', 'set:menu:poi')
    self.addItem('main', 'search', 'business', 'set:menu:search')
    #self.addItem('main', 'view', 'view', 'set:menu:view')
    self.addItem('main', 'options', 'options', 'set:menu:options')
    self.addItem('main', 'download', 'generic', 'set:menu:data')
    self.addItem('main', 'mode', 'transport', 'set:menu:transport')
    self.addItem('main', 'centre', 'centre', 'toggle:centred|set:menu:None')
    self.addItem('main', 'tracklogs', 'tracklogs', 'set:menu:tracklogManager')
    self.addItem('main', 'fullscreen', 'fullscreen', 'menu:fullscreenTogle|set:menu:None')
    self.setupTransportMenu()
    self.setupSearchMenus()
    self.setupMaplayerMenus()
    self.setupPoiMenu()
    self.setupDataMenu()
    self.setupRouteMenu()
    self.clearMenu('options', "set:menu:main") # will be filled by mod_options
#    self.clearMenu('routeProfile', "set:menu:main") # will be filled by mod_routeProfile
    self.lists['places'] = 'placenames'
#    self.set('setUpEditMenu', True)

  def drawTextToSquare(self, cr, x, y, w, h, text):
    """draw lines of text to a square text box, | is used as a delimiter"""
#    (x1,y1,w1,h1) = self.get('viewport', None)
#    dx = w / 3
#    dy = h / 4
    border = 30
    spacing = 20
    lines = text.split('|')
    lineCount = len(lines)
    lineSpace = (h-2*spacing)/lineCount
    i = 0
    for line in lines:
      self.showText(cr, line, x+border, y+i*lineSpace+1*spacing, w-2*border)
      i = i + 1

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

    if w1>h1:
#        buttons = "landscape"
      (elem1) = (x1, y1)
      (elem2) = (x1, y1+1*dy)
      (elem3) = (x1, y1+2*dy)
      (elem4) = (x1+dx, y1)


    elif w1<=h1:
#        buttons = "portrait"
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
          "3h", # background for a 3x1 icon
          onClick)

        border = 20

        self.showText(cr, text1, x4+border, y+border, w-2*border)

        # 2nd line: current value
        self.showText(cr, text2, x4 + 0.15 * w, y + 0.6 * dy, w * 0.85 - border)

        # in corner: row number
        self.showText(cr, "%d/%d" % (index+1, numItems), x4+0.85*w, y + 0.42 * dy, w * 0.15 - border, 20)

  def drawThreePlusOneMenu(self, cr, menuName, parent, button1, button2, box):
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
    self.drawButton(cr, x1, y1, dx, dy, "", "up", "%s:reset|set:menu:%s" % (menuName, parent))
    # * draw the first button
    self.drawButton(cr, x2, y2, dx, dy, text1, icon1, action1)
    # * draw the second button
    self.drawButton(cr, x3, y3, dx, dy, text2, icon2, action2)
    # * draw info box
    w4 = w - x4
    h4 = h - y4
    self.drawButton(cr, x4, y4, w4, h4, "", "box480", boxAction)
    # * draw text to the box
    text = boxTextLines
    self.drawTextToSquare(cr, x4, y4, w4, h4, text) # display the text in the box

  def showText(self,cr,text,x,y,widthLimit=None,fontsize=40):
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

  def firstTime(self):
    self.set("menu",None)

  def handleMessage(self, message):
    if (message == "rebootDataMenu"):
      self.setupDataMenu() # we are returning from the batch menu, data menu needs to be "rebooted"
    elif(message == "setupEditBatchMenu"):
      self.setupEditBatchMenu()
    elif(message == 'screenClicked'):
      self.lastActivity = int(time.time())
    elif(message == 'fullscreenTogle'):
      # toggle fullscreen TODO: automatic fullscreen detection
      if self.fullscreen == True:
        self.mainWindow.get_toplevel().unfullscreen()
        self.fullscreen = False
        print "going out of fullscreen"
      else:
        self.mainWindow.get_toplevel().fullscreen()
        self.fullscreen = True
        print "going to fullscreen"
    
if(__name__ == "__main__"):
  a = menus({},{'viewport':(0,0,600,800)})
  #a.drawMapOverlay(None)
  a.setupSearchMenus()
  