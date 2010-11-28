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
  
  def addBoolOption(self, title, variable, category='misc',default=None, action=None):
    if action:
      self.addOption(title,variable,((False,'OFF',action),(True,'ON',action)),category,default)
    else:
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


    # * the debug submenu
    self.addBoolOption("Print redraw time to terminal", "showRedrawTime", "debug", False)
    self.addBoolOption("Log modRana stdout to file", "loggingStatus", "debug", False, "log:checkLoggingStatus")
    self.addBoolOption("Debug circles", "debugCircles", "debug", False)
    self.addBoolOption("Debug squares", "debugSquares", "debug", False)

#    self.addBoolOption("Debug squares", "debugSquares", "debug", False)
    self.addBoolOption("Remove dups berofe batch dl", "checkTiles", "debug", False)

    self.addBoolOption("Show N900 GPS-fix", "n900GPSDebug", "debug", False)



    # * the view submenu *


    self.addOption("Units", "unitType",
                 [("km","use kilometers"),
                  ("mile", "use miles")],
                   "view",
                   "km")

    self.addOption("Hide main buttons", "hideDelay",
                 [("never","never hide buttons"),
                  ("5","hide buttons after 5 seconds"),
                  ("10","hide buttons after 10 seconds"),
                  ("15","hide buttons after 15 seconds"),
                  ("30","hide buttons after 30 seconds"),
                  ("60","hide buttons after 1 minute"),
                  ("120", "hide buttons after 2 minutes")],
                   "view",
                   "10")

    self.addOption("GUI Rotation", "rotationMode",
                 [("auto","automatic","device:modeChanged"),
                  ("landscape","landscape","device:modeChanged"),
                  ("portrait","portrait","device:modeChanged")],
                   "view",
                   "auto")

    self.addOption("Tracklogs", "showTracklog",
    [(None, "Dont draw tracklogs"),
     ("simple", "Draw simple tracklogs")],
     "view",
     None)

    self.addOption("Time format", "currentTimeFormat",
                 [("24h","24 hours"),
                  ("12h", "12 hours")],
                   "view",
                   "24h")

    self.addOption("Listable menu rows", "listableMenuRows",
                 [(2,"2 rows"),
                  (3,"3 rows"),
                  (4,"4 rows"),
                  (5,"5 rows"),
                  (6,"6 rows")],
                   "view",
                   4)
     
    self.addBoolOption("Centre map", "centred", "view", True)



    # * network *
    self.addOption("Network", "network",
#      [("off","No use of network"),
      [("minimal", "Only for important data"),
       ("full", "Unlimited use of network")],
       "network",
       "full")

    # * GPS *
    self.addBoolOption("GPS", "GPSEnabled", "GPS", True, "gpsd:checkGPSEnabled")

    # * screen *
    """only add if supported on device"""
    display = self.m.get('display', None)
    if display:
      if display.screenBlankingControlSupported():
        self.addOption("Keep display ON", "screenBlankingMode",
        [("always", "always", "display:blankingModeChanged"),
         ("centred", "while centred", "display:blankingModeChanged"),
         ("moving", "while moving", "display:blankingModeChanged"),
         ("movingInFullscreen", "while moving in fullscreen", "display:blankingModeChanged"),
         ("fullscreen", "while in fullscreen", "display:blankingModeChanged"),
         ("gpsFix", "while there is a GPS fix", "display:blankingModeChanged"), #TODO: while there is actually a GPS lock
         ("never", "never", "display:blankingModeChanged")],
         "Display",
         "always")

#    self.addOption("Network", "threadedDownload",
##      [("off","No use of network"),
#      [("True", "Use threads for download"),
#       ("False", "Dont use threads for download")],
#       "network",
#       "on")

#    self.addBoolOption("Logging", "logging", "logging", True)
#    options = []
#    for i in (1,2,5,10,20,40,60):
#      options.append((i, "%d sec" % i))
#    self.addOption("Frequency", "log_period", options, "logging", 2)

#    self.addBoolOption("Vector maps", "vmap", "map", True)

    tiles = self.m.get("mapTiles", None)
    if(tiles):
      tileOptions = [("","None")]
      layers = tiles.layers().items()
      layers.sort()
      for name,layer in layers:
        tileOptions.append((name, layer.get('label',name)))
      self.addOption("Map images", "layer", tileOptions, "map", "mapnik")

      self.addBoolOption("Map as overlay", "overlay", "map", False)

      self.addOption("Background map", "layer2", tileOptions, "map", "osma")

      self.addOption("Transparency ratio:", "transpRatio",
              [("0.25,1","overlay:25%"),
              ("0.5,1","overlay:50%"),
              ("0.75,1","overlay:75%"),
              ("1,1","overlay:100%")],
               "map",
               "0.5,1")
               
      self.addBoolOption("Rotate map in direction of travel", "rotateMap", "map", False)

      self.addOption("Map scale", "mapScale",
                   [(1,"1X"),
                    (2,"2X"),
                    (4,"4X")],
                     "map",
                     1)

      self.addOption("Tile storage (EXPERIMENTAL)", "tileStorageType",
                   [('files',"files (default, more space used)"),
                    ('sqlite',"sqlite (new, less space used)")],
                     "map",
                     'files')


#             [("0.5,0.5","over:50%,back:50%"),
#              ("0.25,0.75","over:25%,back:75%"),
#              ("0.75,0.25","over:75%,back:50%")],
#               "map",
#               "0.5,0.5")



#    self.addBoolOption("Old tracklogs", "old_tracklogs", "map", False)
#    self.addBoolOption("Latest tracklog", "tracklog", "map", True)

    # * online services submenu
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


    self.addOption("Google local search captions", "drawGLSResultCaptions",
      [("True","draw captions"),
       ("False", "dont draw captions")],
       "Online services",
       "True")

    # * online routing submenu
    self.addBoolOption("Avoid major highways ", "routingAvoidHighways", "Online routing", False)

    self.addBoolOption("Avoid toll roads", "routingAvoidToll", "Online routing", False)


    # * navigation

    # in the first string: first one goes to espeak, the seccond part goes to Google
    directionsLanguages =[('ca ca', 'Catalan'),
                          ('zh-yue zh-TW', 'Chinese(Cantonese)'),
                          ('zh zh-CN', 'Chinese(Mandarin)'),
                          ('hr hr', 'Croatian'),
                          ('cs cs', 'Czech'),
                          ('nl nl', 'Dutch'),
                          ('en en', 'English'),
                          ('fi fi', 'Finnish'),
                          ('fr fr', 'French'),
                          ('de de', 'German'),
                          ('el el', 'Greek'),
                          ('hi hi', 'Hindi'),
                          ('hu hu', 'Hungarian'),
                          ('id id', 'Indonesian'),
                          ('it it', 'Italian'),
                          ('lv lv', 'Latvian'),
                          ('no no', 'Norwegian'),
                          ('pl pl', 'Polish'),
                          ('pt pt-BR', 'Portuguese(Brazil)'),
                          ('pt-pt pt-PT', 'Portuguese(European)'),
                          ('ro ro', 'Romanian'),
                          ('ru ru', 'Russian'),
                          ('sr sr', 'Serbian'),
                          ('sk sk', 'Slovak'),
                          ('es es', 'Spanish'),
                          ('ta ta', 'Tamil'),
                          ('tr tr', 'Turkish'),
                          ('vi vi', 'Vietnamese')]

    self.addOption("Language for directions", "directionsLanguage",directionsLanguages,
       "Navigation",
       "en en") # TODO: use locale for default language ?

    self.addOption("Autostart navigation", "autostartNavigationDefaultOn",
      [('disabled',"Disabled"),
       ('first',"From first point"),
       ('closest',"From closest point")],
       "Navigation",
       'closest')

    self.addOption("Point reached distance", "pointReachedDistance",
      [(10,"10 m"),
       (20,"20 m"),
       (30,"30 m"),
       (60,"60 m"),
       (100,"100 m"),
       (200,"200 m"),
       (300,"300 m"),
       (500,"500 m")],
       "Navigation",
       30)

    self.addOption("read Cyrillic with:", "voiceNavigationCyrillicVoice",
      [('ru',"Russian voice"),
       (None,"current voice")],
       "Navigation",
       'ru')


    # * POI
    self.addOption("POI database", "POIDBFilename",
      [("poi.db","shared with Mappero (EXPERIMENTAL)","storePOI:reconnectToDb"),
       ("modrana_poi.db","modRana only (default)", "storePOI:reconnectToDb")],
       "POI",
       "modrana_poi.db")

    """EportPOIDatabaseToCSV is just a dummy value,
       we just need to send a dump message to storePOI"""
    self.addOption("Export POI Database to CSV", "EportPOIDatabaseToCSV",
      [("dump","click to export","storePOI:dumpToCSV"),
       ("dump","click to export","storePOI:dumpToCSV")],
       "POI",
       "dump")

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
    print "saving options"
    try:
      f = open(self.optionsFilename(), "w")
      marshal.dump(self.d, f)
      f.close()
      print "success"
    except IOError:
      print "Can't save options"

  def load(self):
    try:
      f = open(self.optionsFilename(), "r")
      newData = marshal.load(f)
      f.close()
      if 'tileFolder' in newData: #TODO: do this more elegantly
        del newData['tileFolder']
      if 'tracklogFolder' in newData: #TODO: do this more elegantly
        del newData['tracklogFolder']
      for k,v in newData.items():
        self.set(k,v)
    except IOError:
      print "options: error while loading the saved options"

    self.overrideOptions()

  def overrideOptions(self):
    """
    without this, there would not be any projcetion values at start,
    becuase modRana does not know, what part of the map to show
    """
    self.set('centred', True) # set centering to True at start to get setView to run
    self.set('editBatchMenuActive', False)

      
  def optionsFilename(self):
    return("data/options.bin")
  
  def handleMessage(self, message, type, args):
    if(message == "up"):
      if(self.scroll > 0):
        self.scroll -= 1
        self.set("needRedraw", True)
    elif(message == "down"):
      self.scroll += 1
      self.set("needRedraw", True)
    elif(message == "reset_scroll"):
      self.scroll = 0
      self.set("needRedraw", True)
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
#    (x1,y1,w,h) = self.get('viewport', None)
#
#    dx = w / 3
#    dy = h / 4


    
    if(self.menuModule):
      
      # elements allocation
      (e1,e2,e3,e4,alloc) = self.menuModule.threePlusOneMenuCoords()
      (x1,y1) = e1
      (x2,y2) = e2
      (x3,y3) = e3
      (x4,y4) = e4
      (w1,h1,dx,dy) = alloc

      # Top row:
      # * parent menu
      self.menuModule.drawButton(cr, x1, y1, dx, dy, "", "up", "set:menu:options")
      # * scroll up
      self.menuModule.drawButton(cr, x2, y2, dx, dy, "", "up_list", "options:up")
      # * scroll down
      self.menuModule.drawButton(cr, x3, y3, dx, dy, "", "down_list", "options:down")

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
            cAction = None
            if len(c) == 3:
              (cVal, cName, cAction) = c
            else:
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
          if cAction:
            onClick += "|%s" % cAction
          onClick += "|options:save"
          onClick += "|set:needRedraw:1"

#          y = y1 + (row+1) * dy
          y = y4 + (row) * dy
          w = w1 - (x4-x1)
          
          # Draw background and make clickable
          self.menuModule.drawButton(cr,
            x4,
            y,
            w,
            dy,
            None,
            "generic", # background for a 3x1 icon
            onClick)

          border = 20

          # 1st line: option name
          self.showText(cr, title+":", x4+border, y+border, w-2*border)

          # 2nd line: current value
          self.showText(cr, valueDescription, x4 + 0.15 * w, y + 0.6 * dy, w * 0.85 - border)

          # in corner: row number
          self.showText(cr, "%d/%d" % (index+1, numItems), x4+0.85*w, y+3*border, w * 0.15 - border, 20)

            
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

  def shutdown(self):
    """save the dictionary on exit"""
    self.save()

  
if(__name__ == "__main__"):
  a = options({},{'viewport':(0,0,600,800)})
  a.firstTime()

  