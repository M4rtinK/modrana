#!/usr/bin/python
#----------------------------------------------------------------------------
# Handle option menus
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
import marshal

def getModule(m,d):
  return(options(m,d))

class options(ranaModule):
  """Handle options"""
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.options = {}
    self.scroll = 0
    self.load()
  
  def addBoolOption(self, title, variable, category='misc',default=None):
    self.addOption(title,variable,((False,'OFF'),(True,'ON')),category,default)

  def addOption(self, title, variable, choices, category='misc', default=None):
    newOption = (title,variable, choices,category,default)
    if self.options.has_key(category):
      self.options[category].append(newOption)
    else:
      self.options[category] = [newOption,]

  def firstTime(self):
    """Create a load of options.  You can add your own options in here,
    or alternatively create them at runtime from your module's firstTime()
    function by calling addOption.  That would be best if your module is
    only occasionally used, this function is best if the option is likely
    to be needed in all installations"""
    self.addBoolOption("Centre map", "centre", "view", True)

    self.addBoolOption("Debug circles", "debugCircles", "debug", False)

    self.addBoolOption("Debug squares", "debugSquares", "debug", False)

    self.addOption("Tracklogs", "showTracklog",
    [(None, "Dont draw tracklogs"),
     ("Simple", "Draw simple tracklogs")],
     "view",
     False)

    self.addOption("Units", "unitType",
                 [("km","use kilometers"),
                  ("mile", "use miles")],
                   "view",
                   "km")

    self.addOption("Hide main buttons", "hideDelay",
                 [("never","never hide buttons"),
                  ("5","hide buttons after 5 seconds"),
                  ("15","hide buttons after 15 seconds"),
                  ("30","hide buttons after 30 seconds"),
                  ("60","hide buttons after 1 minute"),
                  ("120", "hide buttons after 2 minutes")],
                   "view",
                   "never")

    self.addOption("Network", "network",
      [("off","No use of network"),
       ("minimal", "Only for important data"),
       ("full", "Unlimited use of network")],
       "network",
       "off")

    self.addBoolOption("Logging", "logging", "logging", True)
    options = []
    for i in (1,2,5,10,20,40,60):
      options.append((i, "%d sec" % i))
    self.addOption("Frequency", "log_period", options, "logging", 2)

    self.addBoolOption("Vector maps", "vmap", "map", True)

    tiles = self.m.get("mapTiles", None)
    if(tiles):
      tileOptions = [("","None")]
      for name,layer in tiles.layers().items():
        tileOptions.append((name, layer.get('label',name)))
      self.addOption("Map images", "layer", tileOptions, "map", None)
    self.addBoolOption("Old tracklogs", "old_tracklogs", "map", False)
    self.addBoolOption("Latest tracklog", "tracklog", "map", True)

    self.addOption("Google local search ordering", "GLSOrdering",
      [("default","ordering from Google"),
       ("distance", "order by distance")
      ],
       "Online services",
       "default")

    self.addOption("Google local search results", "GLSResults",
      [("8","max 8 results"),
       ("16", "max 16 results"),
       ("32", "max 32 results")],
       "Online services",
       "8")

    # Add all our categories to the "options" menu
    self.menuModule = self.m.get("menu", None)
    if(self.menuModule):
      for i in self.options.keys():
        self.menuModule.addItem(
          'options', # which menu to add to
          i, # title
          "opt_"+i, # icon name
          "set:menu:opt_%s|options:reset_scroll"%i ) # action

    # Set all undefined options to default values
    for category,options in self.options.items():
      for option in options:
        (title,variable,choices,category,default) = option
        if(default != None):
          if(not self.d.has_key(variable)):
            self.set(variable, default)

  def save(self):
    try:
      f = open(self.optionsFilename(), "w")
      marshal.dump(self.d, f)
      f.close()
    except IOError:
      print "Can't save options"

  def load(self):
    try:
      f = open(self.optionsFilename(), "r")
      newData = marshal.load(f)
      f.close()
      for k,v in newData.items():
        self.set(k,v)
    except IOError:
      pass
      
  def optionsFilename(self):
    return("data/options.bin")
  
  def handleMessage(self, message):
    if(message == "up"):
      if(self.scroll > 0):
        self.scroll -= 1
    elif(message == "down"):
      self.scroll += 1
    elif(message == "reset_scroll"):
      self.scroll = 0
    elif(message == "save"):
      self.save()
    
  def drawMenu(self, cr, menuName):
    """Draw menus"""
    if(menuName[0:4] != "opt_"):
      return
    menuName = menuName[4:]
    if(not self.options.has_key(menuName)):
      return
    
    # Find the screen
    if not self.d.has_key('viewport'):
      return
    (x1,y1,w,h) = self.get('viewport', None)

    dx = w / 3
    dy = h / 4
    
    if(self.menuModule):
      # Top row:
      # * parent menu
      self.menuModule.drawButton(cr, x1, y1, dx, dy, "", "up", "set:menu:options")
      # * scroll up
      self.menuModule.drawButton(cr, x1+dx, y1, dx, dy, "", "up_list", "options:up")
      # * scroll down
      self.menuModule.drawButton(cr, x1+2*dx, y1, dx, dy, "", "down_list", "options:down")

      options = self.options[menuName]


      # One option per row
      for row in (0,1,2):
        index = self.scroll + row
        numItems = len(options)
        if(0 <= index < numItems):
          (title,variable,choices,category,default) = options[index]
          # What's it set to currently?
          value = self.get(variable, None)

          # Lookup the description of the currently-selected choice.
          # (if any, use str(value) if it doesn't match any defined options)
          # Also lookup the _next_ choice in the list, because that's what
          # we will set the option to if it's clicked
          nextChoice = choices[0]
          valueDescription = str(value)
          useNext = False
          for c in choices:
            (cVal, cName) = c
            if(useNext):
              nextChoice = c
              useNext = False
            if(str(value) == str(cVal)):
              valueDescription = cName
              useNext = True

          # What should happen if this option is clicked -
          # set the associated option to the next value in sequence
          onClick = "set:%s:%s" % (variable, str(nextChoice[0]))
          onClick += "|options:save"
          onClick += "|set:needRedraw:1"

          y = y1 + (row+1) * dy
          
          # Draw background and make clickable
          self.menuModule.drawButton(cr,
            x1,
            y,
            w,
            dy,
            None,
            "3h", # background for a 3x1 icon
            onClick)

          border = 20

          # 1st line: option name
          self.showText(cr, title+":", x1+border, y+border, w-2*border)

          # 2nd line: current value
          self.showText(cr, valueDescription, x1 + 0.15 * w, y + 0.6 * dy, w * 0.85 - border)

          # in corner: row number
          self.showText(cr, "%d/%d" % (index+1, numItems), x1+0.85*w, y+border, w * 0.15 - border, 20)

            
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
  
if(__name__ == "__main__"):
  a = options({},{'viewport':(0,0,600,800)})
  a.firstTime()

  