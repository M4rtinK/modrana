#!/usr/bin/python
# -*- coding: utf-8 -*-
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
import marshal
import os
import modrana_utils

def getModule(m,d,i):
  return(Options(m,d,i))

class Options(ranaModule):
  """Handle options"""
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.options = {}
    """for fast searching defaults for corresponding keys"""
    self.keyDefault = {}

    # profile folder
    self.profileFolderPath = self.modrana.getProfilePath()
    # check the profile path and create the folders if necessary
    modrana_utils.createFolderPath(self.profileFolderPath)

    # load persistant options
    self.load()
    self.on = '<span color="green">ON</span>'
    self.off = '<span color="red">OFF</span>'

    # items menu cache
    self.itemMenus = {}

    # item tools special menu name
    self.keyStateListGroupID = None

  def getProfilePath(self):
    """return path to the profile folder"""
    # check if the path exists and create it if not
    modrana_utils.createFolderPath(self.profileFolderPath)
    return self.profileFolderPath

  def getOptionsFilePath(self):
    """return path to the options store filename"""
    return os.path.join(self.getProfilePath(),"options.bin")

  def getCacheFolderPath(self):
    """return path to a folder used for various cache data"""
    return self._assurePathFolder(self.getProfilePath(), "cache")

  def getTracklogsFolderPath(self):
    """return path to a folder for storing tracklogs"""
    path = None
    # first check if the user overrode the tracklog folder path
    config = self.m.get('config', None)
    if config:
      path = config.getTracklogFolderPath()
    if path == None:
    # try to get the path from device module
      if self.dmod:
        path = self.dmod.getTracklogFolderPath()

    if path == None: # this means there is no config or device path
      # use default path & assure it exists
      return self._assurePathFolder(self.getProfilePath(), "tracklogs")
    else:
      return self._assurePath(path)

  def getMapFolderPath(self):
    """return a path to folder for map data storage"""
    path = None
    # first check if the user overrode the map folder path
    config = self.m.get('config', None)
    if config:
      path = config.getMapFolderPath()
    if path == None:
    # try to get the path from device module
      if self.dmod:
        path = self.dmod.getMapFolderPath()

    if path == None: # this means there is no config or device path
      # use default path & assure it exists
      return self._assurePathFolder(self.getProfilePath(), "maps")
    else:
      return self._assurePath(path)

  def getPOIFolderPath(self):
    """return path to the POI folder"""
    if self.dmod:
      path = self.dmod.getPOIFolderPath()
      if path != None: # None means there is no device dependent path
        return self._assurePath(path)
      else:
        return self._assurePathFolder(self.getProfilePath(), "poi")
    else:
      return self._assurePathFolder(self.getProfilePath(), "poi")

  def getPOIDatabasePath(self):
    """return path to the POI database file"""
    POIDBFilename = self.get('POIDBFilename', 'modrana_poi.db')
    POIFolderPath = self.getPOIFolderPath()
    return os.path.join(POIFolderPath,POIDBFilename)

  def getLogFolderPath(self):
    """return path to the POI folder"""
    if self.dmod:
      path = self.dmod.getLogFolderPath()
      if path != None: # None means there is no device dependent path
        return self._assurePath(path)
      else:
        return self._assurePathFolder(self.getProfilePath(), "debug_logs")
    else:
      return self._assurePathFolder(self.getProfilePath(), "debug_logs")
  
  def _assurePathFolder(self, path, folder):
    """combine the given path and folder and make sure the path exists,
    return the resulting path"""
    path = os.path.join(path, folder)
    return self._assurePath(path)

  def _assurePath(self, path):
    """assure path exists and return it back"""
    # check if the path exists and create it if not
    modrana_utils.createFolderPath(path)
    return path

  def _getCategoryID(self, id):
    return "opt_cat_%s" % id # get a standardized id

  def addCategory(self,name,inId,icon,actionPrefix="",actionSufix=""):
    """this method should be run only after menu module instance
    is available in self.menuModule and the options menu is cleared,
    eq. has at least the escape button"""
    # first we add the category button to the options
    id = self._getCategoryID(inId) # get a standardized id
    action="%sset:menu:%s%s" % (actionPrefix,id,actionSufix)
    self.menuModule.addItem('options', name, icon, action)
    # initialize menu for the new category menu
    self.menuModule.clearMenu(id,"set:menu:options")
    # as a convenience, return the id
    return inId

  def _getGroupId(self, catId, id):
    parentId = self._getCategoryID(catId)
    return "%s_opt_group_%s" % (parentId, id)
  
  def addGroup(self,name,id,parentId,icon,actionPrefix="",
               actionSufix="", registerToMenu=True, backButtonAction=None):
    """this method ads a new (empty) options group to category specified by
    catId, as a convenience feature, the id of the new group is returned"""
    catId = self._getCategoryID(parentId)
    id = self._getGroupId(parentId, id) # get a standardized id
    """
    handle empty parent ids - such ids can be valid because the menu switching is handled
    handled entirely by the pre and post actions
    """
    if not parentId:
      action="%s%s" % (actionPrefix,actionSufix)
    else:
      action="%sset:menu:options#%s%s" % (actionPrefix,id,actionSufix)
      
    if registerToMenu: # add to options menu structure ?
      self.menuModule.addItem(catId, name, icon, action)
    if backButtonAction != None:
      self.options[id] = [backButtonAction ,0,[]]
    else:
      self.options[id] = ["set:menu:%s" % catId,0,[]]
    return id

  def setGroupParent(self, groupID, parentID):
    """set the parent id of a given group id"""
    if groupID in self.options:
      self.options[groupID][0] = "set:menu:options#%s" % parentID
    else:
      print('options - set group parent: group not found: %s' % groupID)

  def getGroupParent(self, groupID):
    """set the parent id of a given group id"""
    if groupID in self.options:
      return self.options[groupID][0]
    else:
      print('options - get group parent: group not found: %s' % groupID)

  def clearGroup(self, groupID):
    """clear a given group from any options,
    preserving its parent setting"""
    self.options[groupID][1] = 0
    self.options[groupID][2] = []


  def addBoolOption(self, title, variable, group, default=None, action=None):
    on = self.on
    off = self.off

    if action:
      states = ((False,off,action),(True,on,action))
    else:
      states = ((False,off),(True,on))
    data = {"type":"toggle",
               "states": states }
    self.addOption(title,variable,data,group,default)

  def addToggleOption(self, title, variable, choices, group, default=None):
    data = {"type":"toggle",
               "states": choices }
    self.addOption(title,variable,data,group,default)


  def addEditOption(self, title, variable, group, label="Edit variable", description=None):
    choices = {"type":"showAndEditVariable",
               "label": label,
               "description": description
              }
    self.addOption(title, variable, choices, group, None)

  def addItemsOption(self, title, variable, items, group, default=None, fakeMode=None):
    # the back action returns back to the group
    backAction = "set:menu:options#%s" % group
    # create and add the menu
    menu = self.menuModule.getClearedMenu(backAction)
    menuItems = [] # an ordered list of all the menu items
    itemDict = {} # for easily assigning keys to labels
    if fakeMode != None:
      mode = fakeMode
    else:
      mode = self.get('mode', 'car')

    id = 1 # id 0 us the escape button
    for key, name in items:
      item = self.menuModule.generateItem("#%s" % name, "generic",
      "setWithMode:%s:%s:%s|%s" % (mode, variable, key, backAction))

      menuItems.append(item)
      itemDict[key] = (name,id)
      id = id + 1
    # load all items to the menu
    menu = self.menuModule.addItemsToThisMenu(menu, menuItems)
    # store the menu in the menu module
    """NOTE: for the returning back to the group to work correctly,
    the menu is stored under a key combined from the variable and group names"""
    storageKey = self._getItemsOptionStorageKey(group, variable, mode)

    self.menuModule.addItemMenu(storageKey, menu, wideButtons=True)

    # also store in the local options structure
    choices = {"type":"selectOneItem",
              'label':"",
              'description':"",
              'default':default,
              'items':items,
              'itemDict' : itemDict,
              'storageKey' : storageKey}
    # this means we are probably showing the option in the per mode state list
    if fakeMode != None:
      choices['mode'] = fakeMode
      choices['noToolsIcon'] = True # disable the tools in the per mode state list
    self.addOption(title, variable, choices, group, default)

  def _getItemsOptionStorageKey(self, group, variable, mode):
    """return menu name for the special item selection itemized menu
    """
    return "options1Item*%s*%s*%s" % (group, variable, mode)

  def _highlightActiveItem(self, menu, variable):
    """highlight currently active item in the item selection menu"""
    # test if the key was initialized
    if self.optionsKeyExists(variable):
      text, icon, action, type, timedAction
    else: # not initialized, no need to highlight anything
      return menu

  def addOption(self, title, variable, choices, group, default=None):
    """add an option item"""
  
    """ add group name to choices,
    this is needed for the item tools menu to know where to return"""
    choices['groupName'] = group

    newOption = [title,variable, choices,group,default]
    if self.options.has_key(group):
      self.options[group][2].append(newOption)
      self.keyDefault[variable] = default
    else:
      print "options: group %s does not exist, call addGroup to create it first" % group

  def addRawOption(self, optionData):
    """add a raw option to options
    NOTE: the options contains its group ID"""
    (title,variable, choices,group,default) = optionData
    """ as some options have have side effects when they are created,
    we need to check option the type and replicate those effect as needed"""
    type = choices['type']
    choices = dict(choices)
    if type == 'selectOneItem':
      if 'mode' in choices:
        fakeMode = choices['mode']
      else:
        fakeMode = None
      items = choices['items']
      self.addItemsOption(title, variable, items, group, default, fakeMode = fakeMode)
    else: # no side effects, just add the raw option
      if self.options.has_key(group):
        self.options[group][2].append(optionData)
        self.keyDefault[variable] = default
      else:
        print "options: group %s does not exist, can't add a raw option to it" % group

  def removeOption(self, categoryId, groupId, variable):
    """remova an option given by group and variable name"""

    group = self._getGroupId(categoryId, groupId)

    if self.options.has_key(group):
      remove = lambda x:x[1]==variable
      self.options[group][2][:] = [x for x in self.options[group][2] if not remove(x)]
      if variable in self.keyDefault:
        del self.keyDefault[variable]
    else:
      print "options: group %s does not exist, so option with variable %s can not be removed" % (group,variable)

  def getOption(self, groupID, index):
    """get a options item from a given group by its index"""
    if self.options.has_key(groupID):
      try:
        return self.options[groupID][2][index]
      except IndexError:
        print "options: group %s has no index %d, so this option can not be returned" % (groupID, index)
        return False

    else:
      print "options: group %s does not exist, so option with index %d can not be returned" % (groupID, index)
      return False

  def getKeyDefault(self, key, default=None):
    """get default value for a given key"""
    return self.keyDefault.get(key, default)

  def firstTime(self):
    """Create a load of options.  You can add your own options in here,
    or alternatively create them at runtime from your module's firstTime()
    function by calling addOption.  That would be best if your module is
    only occasionally used, this function is best if the option is likely
    to be needed in all installations"""
    self.menuModule = self.m.get("menu", None)
    self.menuModule.clearMenu("options")

    # shortcuts
    addCat = self.addCategory
    addGroup = self.addGroup
    addOpt = self.addToggleOption
    addBoolOpt = self.addBoolOption
    addItems = self.addItemsOption

    # * the Map category *
    catMap = addCat("Map", "map", "map")

    # ** map layers
    group = addGroup("Map layers", "map_layers", catMap, "generic")
    layers = self.modrana.getMapLayers()
    layerNameKey = []
    for key in layers.keys():
      name = layers[key]['label']
      layerNameKey.append( (key, name) )
    layerNameKey.sort()
    layerNameKey.append((None, "Empty layer"))
    addItems("Main map", "layer", layerNameKey, group, "mapnik")

    # ** Overlay
    group = addGroup("Map overlay", "map_overlay", catMap, "generic")
    addBoolOpt("Map as overlay", "overlay", group, False)

    addItems("Main map", "layer", layerNameKey, group, "mapnik")
    addItems("Background map", "layer2", layerNameKey, group, "osma")

    addOpt("Transparency ratio", "transpRatio",
            [("0.25,1","overlay:25%"),
            ("0.5,1","overlay:50%"),
            ("0.75,1","overlay:75%"),
            ("1,1","overlay:100%")],
             group,
             "0.5,1")

    # ** Rotation
    group = addGroup("Rotation", "map_rotation", catMap, "generic")
    addBoolOpt("Rotate map in direction of travel", "rotateMap", group, False)

    # ** Scaling
    group = addGroup("Scaling", "map_scaling", catMap, "generic")
    addOpt("Map scale", "mapScale",
                 [(1,"1X"),
                  (2,"2X"),
                  (4,"4X")],
                   group,
                   1)

    # ** centering
    group = addGroup("Centering", "centering", catMap, "generic")
    addBoolOpt("Centre map", "centred", group, True)

    addOpt("Centering shift", "posShiftDirection",
      [("down","shift down"),
       ("up","shift up"),
       ("left","shift left"),
       ("right","shift right"),
       (False,"don't shift")],
       group,
       "down")

    addOpt("Centering shift amount", "posShiftAmount",
      [(0.25,"25%"),
       (0.5,"50%"),
       (0.75,"75%"),
       (1.0,"edge of the screen")],
       group,
       0.75)

    changedMsg = "mapView:centeringDisableThresholdChanged"
    addOpt("Disable by dragging", "centeringDisableThreshold",
      [(2048,"normal drag - <i>default</i>",changedMsg),
       (15000,"long drag",changedMsg),
       (40000,"really long drag",changedMsg),
       (80000,"extremely long drag",changedMsg),
       (False,self.off,changedMsg)],
       group,
       2048)

    # ** dragging
    group = addGroup("Dragging", "dragging", catMap, "generic")
    # check if we are on a powerful device or not and set the default accordingly
    if self.dmod.simpleMapDragging():
      defaultMode = "staticMapDrag"
    else:
      defaultMode = "default"

    addOpt("Map dragging", "mapDraggingMode",
      [("default","full redraw - <i>default</i>","mapView:dragModeChanged"),
       ("staticMapDrag","drag visible map - <i>fastest</i>", "mapView:dragModeChanged")],
       group,
       defaultMode)

    # ** tile storage
    group = addGroup("Tile storage", "tile_storage", catMap, "generic")
    addOpt("Tile storage", "tileStorageType",
                 [('files',"files (default, more space used)"),
                  ('sqlite',"sqlite (new, less space used)")],
                   group,
                   'files')
    addBoolOpt("Store downloaded tiles", "storeDownloadedTiles", group, True)

    # * the view category *
    catView = addCat("View", "view", "view")

    # ** GUI
    group = addGroup("GUI", "gui", catView, "generic")
    addOpt("Hide main buttons", "hideDelay",
                 [("never","never hide buttons"),
                  ("5","hide buttons after 5 seconds"),
                  ("10","hide buttons after 10 seconds"),
                  ("15","hide buttons after 15 seconds"),
                  ("30","hide buttons after 30 seconds"),
                  ("60","hide buttons after 1 minute"),
                  ("120", "hide buttons after 2 minutes")],
                   group,
                   "10")

    addOpt("GUI Rotation", "rotationMode",
                 [("auto","automatic","device:modeChanged"),
                  ("landscape","landscape","device:modeChanged"),
                  ("portrait","portrait","device:modeChanged")],
                   group,
                   "auto")


    # ** screen
    """only add if supported on device"""
    display = self.m.get('display', None)
    if display:
      if display.screenBlankingControlSupported():
        group = addGroup("Screen", "screen", catView, "generic")
        addOpt("Keep display ON", "screenBlankingMode",
        [("always", "always", "display:blankingModeChanged"),
         ("centred", "while centred", "display:blankingModeChanged"),
         ("moving", "while moving", "display:blankingModeChanged"),
         ("movingInFullscreen", "while moving in fullscreen", "display:blankingModeChanged"),
         ("fullscreen", "while in fullscreen", "display:blankingModeChanged"),
         ("gpsFix", "while there is a GPS fix", "display:blankingModeChanged"), #TODO: while there is actually a GPS lock
         ("never", "never", "display:blankingModeChanged")],
         group,
         "always")
      if display.usesDashboard():
        addBoolOpt("Redraw when on dashboard", "redrawOnDashboard", group, False)

      # ** themes
      icons = self.m.get('icons', None)
      if icons:
        group = addGroup("Themes", "themes", catView, "generic")
        defaultTheme = icons.defaultTheme
        themeList = icons.getThemeList()
        # check if current theme exists
        currentTheme = self.get('currentTheme', None)
        if currentTheme != None:
          if currentTheme not in themeList:
            self.set('currentTheme', defaultTheme) # theme not valid, reset to default

        themeChangedMessage = "icons:themeChanged"
        nameValueList = map(lambda x: (x,x,themeChangedMessage), themeList)
        
        addOpt("Current theme", "currentTheme",
        nameValueList,
         group,
         defaultTheme)


    # ** units
    group = addGroup("formats#Units and", "units", catView, "generic")
    addOpt("Units", "unitType",
                 [("km","use kilometers"),
                  ("mile", "use miles")],
                   group,
                   "km")

    addOpt("Time format", "currentTimeFormat",
                 [("24h","24 hours"),
                  ("12h", "12 hours")],
                   group,
                   "24h")

    # ** menus
    group = addGroup("Menus", "menus", catView, "generic")
    addOpt("Listable menu rows", "listableMenuRows",
                 [(2,"2 rows"),
                  (3,"3 rows"),
                  (4,"4 rows"),
                  (5,"5 rows"),
                  (6,"6 rows")],
                   group,
                   4)


    if self.dmod.hasButtons():
      # TODO: change this once there are more options for key shortcuts
      # * the Keys category *
      catKeys = addCat("Keys", "keys", "keys")
      # * Device buttons
      group = addGroup("Device buttons", "device_buttons", catKeys, "n900")
      if self.dmod.hasVolumeKeys():
        addBoolOpt("Use volume keys for zooming", "useVolumeKeys", group, True, "device:updateKeys")


    # * the Navigation category
    catNavigation = addCat("Navigation", "navigation", "navigation")

    # * turn by turn navigation
    group = addGroup("Turn by turn", "turn_by_turn", catNavigation, "generic")

    addOpt("Autostart navigation", "autostartNavigationDefaultOnAutoselectTurn",
      [('disabled',"OFF"),
       ('enabled',"ON")],
       group,
       'enabled')

    addOpt("Make final turn announcement at", "pointReachedDistance",
      [(10,"10 m"),
       (20,"20 m"),
       (30,"30 m"),
       (60,"60 m"),
       (100,"100 m"),
       (200,"200 m"),
       (300,"300 m"),
       (500,"500 m")],
       group,
       30)

    addOpt("Announce turns at least this far ahead", "minAnnounceDistance",
      [(10,"10 m"),
       (20,"20 m"),
       (30,"30 m"),
       (60,"60 m"),
       (100,"100 m"),
       (200,"200 m"),
       (300,"300 m"),
       (500,"500 m")],
       group,
       100)

    addOpt("Announce turns at least this long ahead", "minAnnounceTime",
      [(5,"5 s"),
       (10,"10 s"),
       (20,"20 s"),
       (30,"30 s"),
       (45,"45 s"),
       (60,"60 s"),
       (90,"90 s")],
       group,
       10)

    # Note: actual values are in m/s, accurate to 2 decimal places.  We
    # store them as strings so lookup will work reliably.
    addOpt("Increase turn announcement time above", "minAnnounceSpeed",
      [("5.56","20 km/h (12 mph)"),
       ("8.33","30 km/h (20 mph)"),
       ("11.11","40 km/h (25 mph)"),
       ("13.89","50 km/h (30 mph)"),
       ("22.22","80 km/h (50 mph)"),
       ("27.78","100 km/h (60 mph)")],
       group,
       "13.89")

    # Note: actual values are in m/s, accurate to 2 decimal places.  We
    # store them as strings so lookup will work reliably.
    addOpt("Constant turn announcement time above", "maxAnnounceSpeed",
      [("13.89","50 km/h (30 mph)"),
       ("22.22","80 km/h (50 mph)"),
       ("27.78","100 km/h (60 mph)"),
       ("33.33","120 km/h (75 mph)"),
       ("44.44","160 km/h (100 mph)")],
       group,
       "27.78")

    addOpt("Maximum turn announcement time", "maxAnnounceTime",
      [(20,"20 s"),
       (30,"30 s"),
       (45,"45 s"),
       (60,"60 s"),
       (90,"90 s"),
       (120,"120 s")],
       group,
       60)

    # Note: these are exponents, stored as strings so lookup will work reliably.
    addOpt("Announcement time increase type", "announcePower",
      [("1.0","Linear with speed"),
       ("0.5","Very quickly, then linear"),
       ("0.75","Quickly, then linear"),
       ("1.5","Slowly, then linear"),
       ("2.0","Quite slowly, then linear"),
       ("4.0","Very slowly, then quite fast")],
       group,
       "2.0")


    # * navigation language
    group = addGroup("Language", "tbt_language", catNavigation, "generic")

    # in the first string: first one goes to espeak, the second part goes to Google
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

    addItems("Language for directions", 'directionsLanguage',
         directionsLanguages,
         group,
         "en en") # TODO: use locale for default language ?

    addOpt("read Cyrillic with", "voiceNavigationCyrillicVoice",
      [('ru',"Russian voice"),
       (False,"current voice")],
       group,
       'ru')


    # ** online routing submenu
    group = addGroup("Online routing", "online_routing", catNavigation, "generic")
    addBoolOpt("Avoid major highways ", "routingAvoidHighways", group, False)

    addBoolOpt("Avoid toll roads", "routingAvoidToll", group, False)

    # * the POI category
    catPOI = addCat("POI", "poi", "opt_poi")

    # ** POI storage
    group = addGroup("POI storage", "poi_storage", catPOI, "generic")
    addOpt("POI database", "POIDBFilename",
      [("poi.db","shared with Mappero (EXPERIMENTAL)","storePOI:reconnectToDb"),
       ("modrana_poi.db","modRana only (default)", "storePOI:reconnectToDb")],
       group,
       "modrana_poi.db")

    """ExportPOIDatabaseToCSV is just a dummy value,
       we just need to send a dump message to storePOI"""
    addOpt("Export POI Database to CSV", "EportPOIDatabaseToCSV",
      [("dump","click to export","storePOI:dumpToCSV"),
       ("dump","click to export","storePOI:dumpToCSV")],
       group,
       "dump")

    # ** online POI search
    group = addGroup("Online search", "poi_online", catPOI, "generic")
    addOpt("Google local search ordering", "GLSOrdering",
      [("default","ordering from Google"),
       ("distance", "order by distance")
      ],
       group,
       "default")

    addOpt("Google local search results", "GLSResults",
      [("8","max 8 results"),
       ("16", "max 16 results"),
       ("32", "max 32 results")],
       group,
       "8")


    addOpt("Google local search captions", "drawGLSResultCaptions",
      [("True","draw captions"),
       ("False", "dont draw captions")],
       group,
       "True")

    # * the Location category *
    catLocation = addCat("Location", "location", "gps_satellite")

    # ** GPS
    group = addGroup("GPS", "gps", catLocation, "generic")
    addBoolOpt("GPS", "GPSEnabled", group, True, "location:checkGPSEnabled")
    if self.dmod.getLocationType() == 'gpsd':
      knots = "knots per second"
      meters = "meters per second"
      if self.device == 'neo':
        knots = "knots per second (old SHR)"
        meters = "meters per second (new SHR)"
      addOpt("GPSD reports speed in","gpsdSpeedUnit",
      [('knotsPerSecond', knots),
       ('metersPerSecond', meters)],
       group,
       'knotsPerSecond')

    # * the Network category *
    catNetwork = addCat("Network", "network", "network")
    # * network *
    group = addGroup("Network usage", "network_usage", catNetwork, "generic")
    addOpt("Network", "network",
#      [("off","No use of network"), #TODO: implement this :)
      [("minimal", "Only for important data"),
       ("full", "Unlimited use of network")],
       group,
       "full")

    addOpt("Max nr. of threads for tile auto-download","maxAutoDownloadThreads2",
      [(5, "5"),
       (10, "10 (default)"),
       (20, "20"),
       (30, "30"),
       (40, "40"),
       (50, "50")],
       group,
       10)

    # * the Sound category *
    catSound = addCat("Sound", "sound", "sound")
    # * sound output
    group = addGroup("Sound output", "sound_output", catSound, "sound")

    addBoolOpt("Application wide sound output", "soundEnabled", group, True)

    # * espeak group
    group = addGroup("Voice", "voice_out", catSound, "espeak")

    addOpt("Test voice output","voiceTest",
      [("test", "<b>press to start test</b>","voice:voiceTest"),
       ("test", "<b>press to start test</b>", "voice:voiceTest")],
       group,
       "test")

    addOpt("Voice parameters","voiceParameters",
      [("auto", "<b>automatic</b>","ms:options:espeakParams:auto"),
       ("manual", "<b>manual</b>", "ms:options:espeakParams:manual")],
       group,
       "auto")



    if self.get('voiceParameters', None) == "manual":
      self._updateVoiceManual('add')

    # *** special group for a list per mode item states ***
    self.keyStateListGroupID = addGroup("specialTools", 'specialGroup', 'specialParent',
    "generic", registerToMenu=False, backButtonAction="set:menu:optionsItemTools")    

#    addOpt("Network", "threadedDownload",
##      [("off","No use of network"),
#      [("True", "Use threads for download"),
#       ("False", "Don't use threads for download")],
#       "network",
#       "on")

#    addBoolOpt("Logging", "logging", "logging", True)
#    options = []
#    for i in (1,2,5,10,20,40,60):
#      options.append((i, "%d sec" % i))
#    addOpt("Frequency", "log_period", options, "logging", 2)

#    addBoolOpt("Vector maps", "vmap", "map", True)


#             [("0.5,0.5","over:50%,back:50%"),
#              ("0.25,0.75","over:25%,back:75%"),
#              ("0.75,0.25","over:75%,back:50%")],
#               "map",
#               "0.5,0.5")



#    addBoolOpt("Old tracklogs", "old_tracklogs", "map", False)
#    addBoolOpt("Latest tracklog", "tracklog", "map", True)

    # * the Debug category
    catDebug = addCat("Debug", "debug", "debug")

    # ** redraw
    group = addGroup("Redrawing", "redrawing", catDebug, "generic")
    addBoolOpt("Print redraw time to terminal", "showRedrawTime", group, False, "display:checkShowRedrawTime")
    # ** logging
    group = addGroup("Logging", "logging", catDebug, "generic")
    addBoolOpt("Log modRana stdout to file", "loggingStatus", group, False, "log:checkLoggingStatus")
    # ** tiles
    group = addGroup("Tiles", "tiles", catDebug, "generic")
    addBoolOpt("Print tile cache status to terminal", "reportTileCachStatus", group, False)
    addBoolOpt("Tile loading status to terminal", "tileLoadingDebug", group, False)
    addBoolOpt("Redraw screen once a new tile is loaded", "tileLoadedRedraw", group, True)
    addBoolOpt("Remove dups before batch dl", "checkTiles", group, False)
    # ** tracklog drawing
    group = addGroup("Tracklogs", "tracklogs", catDebug, "generic")
    addBoolOpt("Debug circles", "debugCircles", group, False)
    addBoolOpt("Debug squares", "debugSquares", group, False)
    # ** navigation
    group = self.addGroup("Navigation", "navigation", catDebug, "generic")
    addBoolOpt("Print Turn-By-Turn triggers", "debugTbT", group, False)
    # ** gps
    group = self.addGroup("GPS", "gps", catDebug, "generic")
    # only show relevant
    locationType = self.dmod.getLocationType()
    if locationType == 'liblocation':
      addBoolOpt("Show N900 GPS-fix", "n900GPSDebug", group, False)
    if locationType == 'gpsd':
      addBoolOpt("Show gpsd debug output", "gpsdDebugVerbose", group, False, "location:gpsdCheckVerboseDebugEnabled")



#    addOpt("Tracklogs", "showTracklog",
#    [(False, "Dont draw tracklogs"),
#     ("simple", "Draw simple tracklogs")],
#     "view",
#     False)
    self._setUndefinedToDefault()

  def _setUndefinedToDefault(self):
    # Set all undefined options to default values
    for category,options in self.options.items():
      for option in options[2]:
        (title,variable,choices,category,default) = option
        if(default != None):
          if(not self.d.has_key(variable)):
            self.set(variable, default)

  def _removeNonPersistent(self, inputDict):
    """keys that begin with # are not saved
    (as they mostly contain data that is either time sensitive or is
    reloaded on startup)
    ASSUMPTION: keys are strings of length>=1"""
    try:
      return dict((k, v) for k, v in inputDict.iteritems() if k[0] != '#')
    except Exception, e:
      print('options: error while filtering options\nsome nonpersistent keys might have been left in\nNOTE: keys should be strings of length>=1\n', e)
      return self.d

  def _reloadKeyStateList(self, groupID, index, key):
    """reload the key state list to represent currently selected option"""

    # clear the group
    self.clearGroup(self.keyStateListGroupID)
    """ for each mode show the current key state"""
    modes = self.modrana.getModes().keys()
    modes.sort()

    # get data for the given option
    optionData = self.getOption(groupID, index)


    # modify the option
    for mode in modes:
      optionD = list(optionData) # make a copy
      # modify the choices dictionary
      # NOTE: somehow, it is needed to do a copy not just to modify it in the option
      # or else the mode value is for all options added the same
      d = dict(optionD[2])
      d['noToolsIcon'] = True # disable the tools icon
      d['mode'] = mode # force a mode
      optionD[2] = d
      optionD[3] = self.keyStateListGroupID # set the group to the state list
      self.addRawOption(optionD)

  def save(self):
    print "options: saving options"
    try:
      f = open(self.getOptionsFilePath(), "w")
      # remove keys marked as nonpersistent
      self.d['keyModifiers'] = self.modrana.keyModifiers
      d = self._removeNonPersistent(self.d)
      marshal.dump(d, f)
      f.close()
      print "options: successfully saved"
    except IOError:
      print "Can't save options"

  def load(self):
    try:
      f = open(self.getOptionsFilePath(), "r")
      newData = marshal.load(f)
      f.close()
      if 'tileFolder' in newData: #TODO: do this more elegantly
        del newData['tileFolder']
      if 'tracklogFolder' in newData: #TODO: do this more elegantly
        del newData['tracklogFolder']
      for k,v in newData.items():
        self.set(k,v)
    except Exception, e:
      print "options: exception while loading saved options:\n%s" % e
      #TODO: a yes/no dialog for clearing (renaming with timestamp :) the corrupted options file (options.bin)
      self.sendMessage('ml:notification:m:Loading saved options failed;7')

    self.overrideOptions()

  def overrideOptions(self):
    """
    without this, there would not be any projection values at start,
    because modRana does not know, what part of the map to show
    """
    self.set('centred', True) # set centering to True at start to get setView to run
    self.set('editBatchMenuActive', False)

  
  def handleMessage(self, message, type, args):
    if type=="ml" and message=="scroll":
      (direction,menuName) = args
      index = self.options[menuName][1]
      maxIndex = len(self.options[menuName][2])-1
      if direction == "up" and index > 0:
        newIndex = index - 1
        self.options[menuName][1] = newIndex
      elif direction == "down" and index < maxIndex:
        newIndex = index + 1
        self.options[menuName][1] = newIndex
    elif(message == "save"):
      self.save()

    elif type == 'ml' and message == "go2ItemToolsMenu":
      (groupID, index, key) = args
      index = int(index)
      # reload the tools menu
      menus = self.m.get('menu', None)
      if menus:
        menuName = 'optionsItemTools'
        reset='ms:options:resetKey:%s' % key
        notify = "ml:notification:m:Item has been reset to default;3"
        resetAction = "%s|%s|set:menu:options#%s" % (reset, notify, groupID)
        menus.clearMenu(menuName, 'set:menu:options#%s' % groupID)
        menus.addItem(menuName, 'state list#per mode', 'generic',
                      'ml:options:go2ItemStateListMenu:%s;%d;%s' % (groupID, index, key)
                      )
        menus.addItem(menuName, 'default#reset to', 'generic', resetAction)
        self.set('menu', menuName)
    elif type == 'ml' and message == "go2ItemStateListMenu":
      (groupID, index, key) = args
      index = int(index)
      """reload the option key state list for the given key"""
      self._reloadKeyStateList(groupID, index, key)
      # go to the menu
      self.set('menu', 'options#%s' % self.keyStateListGroupID)

    elif type == 'ms' and message == 'resetKey':
      """ reset a given options item to default, including any key modifiers"""
      key = args
      self.modrana.purgeKey(key)
      default = self.getKeyDefault(key)
      self.set(key, default)
      
    elif type == 'ml' and message == 'addKeyModifier':
      """make the value of a key mode specific"""
      (key, mode) = args
      self.modrana.addKeyModifier(key, mode=mode)
    elif type == 'ml' and message == 'removeKeyModifier':
      (key, mode) = args
      """make the value of a key mode unspecific"""
      self.modrana.removeKeyModifier(key, mode=mode)

    elif type=="ms" and message == "espeakParams":
      # switch between espeak parameter modes
      if args == "manual":
        self._updateVoiceManual("remove")
      elif args == "auto":
        self._updateVoiceManual("add")

    elif type == "ml" and message == "editVariable":
      (variable, label, description) = args
      initialText = self.get(variable, "")
      entry = self.m.get('textEntry', None)
      if entry:
        key = "editVariable_%s" % variable
        entry.entryBox(self,key, label, initialText, description)

    #messages to toggles a key to be mode un/specific
    #Mode specific keys:
    #this means that the options key can have a different value
    #depending on the current mode, thus enabling better customization"""
    elif type == "ms" and message == "makeKeyModeSpecific":
      self.modrana.addKeyModifier(args)
    elif type == "ms" and message == "makeKeyModeUnSpecific":
      self.modrana.removeKeyModifier(args)

  def _updateVoiceManual(self, action):
    """add or remove custom voce parameters option items"""

    if action == "add":
      groupId = self._getGroupId("sound", "voice_out")
      description="<b>Note:</b> <tt>%language%</tt> will be replaced by current language code, <tt>%message%</tt> will be replaced by the message and <tt>%qmessage%</tt> will be replaced by the message in quotes"

      self.addEditOption("Edit voice string", "voiceString", groupId, "Edit voice string", description=description)

      message = "ms:voice:resetStringToDefault:espeak"
      self.addToggleOption("Reset voice string with <b>Espeak</b> default", "placeholder",
      [("foo","<i>click to use this default</i>",message)],
       groupId,
       "foo")

    elif action == "remove":
      self.removeOption("sound", "voice_out", "voiceString")
      self.removeOption("sound", "voice_out", "placeholder")

  def handleTextEntryResult(self, key, result):
    (type, variable) = key.split("_", 1)
    if type == "editVariable":
      print "editing variable: %s with: %s" % (variable, result)
      self.set(variable,result)

  def drawMenu(self, cr, menuName, args=None):
    # custom options list drawing
    clickHandler = self.m.get('clickHandler', None)
    if self.menuModule and clickHandler:
      # elements allocation
      (e1,e2,e3,e4,alloc) = self.menuModule.threePlusOneMenuCoords()
      (x1,y1) = e1
      (x2,y2) = e2
      (x3,y3) = e3
      (x4,y4) = e4
      (w1,h1,dx,dy) = alloc

      (cancelButtonAction, firstItemIndex, options) = self.options[menuName]

      # Top row:
      # * parent menu
      timeout = self.modrana.gui.msLongPress
      self.menuModule.drawButton(cr, x1, y1, dx, dy, "", "up", cancelButtonAction, timedAction=(timeout,"set:menu:None"))
      # * scroll up
      self.menuModule.drawButton(cr, x2, y2, dx, dy, "", "up_list", "ml:options:scroll:up;%s" % menuName)
      # * scroll down
      self.menuModule.drawButton(cr, x3, y3, dx, dy, "", "down_list", "ml:options:scroll:down;%s" % menuName)

      # One option per row
      for row in (0,1,2):
        index = firstItemIndex + row
        numItems = len(options)
        cAction = None
        if(0 <= index < numItems):
          (title,variable,choices,group,default) = options[index]
          # What's it set to currently?
          if 'mode' in choices:
            mode = choices['mode']
          else:
            mode = self.get('mode', 'car')
          value = self.get(variable, None, mode=mode)

          """ if the key has a modifier in this mode,
          append the mode label to the title"""

          if 'mode' in choices:
            # this currently means we are in the option state list
            if self.get('mode', 'car') == choices['mode']:
              # current mode
              title = "%s: <small><sup><b>[%s]</b></sup></small>" % (
              title, self.modrana.getModeLabel(mode))
            else:
              title = "%s: <small><sup>[%s]</sup></small>" % (
              title, self.modrana.getModeLabel(mode))

          else:
            # nromal option display
            if self.modrana.hasKeyModifierInMode(variable, mode):
              title = "%s: <small><sup><b>[%s]</b></sup></small>" % (
              title, self.modrana.getModeLabel(mode))
            else:
              title = "%s:" % title

          # Lookup the description of the currently-selected choice.
          # (if any, use str(value) if it doesn't match any defined options)
          # Also lookup the _next_ choice in the list, because that's what
          # we will set the option to if it's clicked

          optionType = choices["type"]

          if optionType == "showAndEditVariable":
            label = choices["label"]
            description = choices["description"]
            # show and edit the exact value of a variable manually
            valueDescription = self.get(variable, "variable is not set yet")
            valueDescription = "<tt><b>%s</b></tt>" % valueDescription
            payload = "%s;%s;%s" % (variable, label, description)
            onClick = "ml:options:editVariable:%s|set:needRedraw:True" % payload

          elif optionType == "selectOneItem":
            #show multiple items and make it possible to select one of them

            # get current value
            default = choices['default']
            value = self.get(variable, default, mode=mode)
            # show label for the given value
            valueDescription, highlightId = choices['itemDict'].get(value, (value,None))
            """if no description is found, just display the value"""
            valueDescription = "<tt><b>%s</b></tt>" % valueDescription

            #assure highlighting
            if highlightId != None:
              """ run an action before switching to the next menu that
              assures that items in the next menu are properly highlighted
              according to the state of the corresponding variable"""
              pre = "ml:menu:highlightItem:%s;%d|" % (choices['storageKey'], highlightId)
            else:
              pre = "" # no id that needs highlighting found

            onClick = "%sset:menu:options1Item*%s*%s*%s" % (pre, group, variable, mode)

          elif optionType == 'toggle':
            states = choices['states']
            nextChoice = states[0]
            valueDescription = str(value)
            useNext = False
            for c in states:
              (cVal, cName) = (c[0],c[1])
              if(useNext):
                nextChoice = c
                useNext = False
              if(str(value) == str(cVal)):
                valueDescription = cName
                useNext = True
                if len(c) == 3:
                  cAction = c[2]

            # What should happen if this option is clicked -
            # set the associated option to the next value in sequence
            onClick = "setWithMode:%s:%s:%s" % (mode, variable, str(nextChoice[0]))
            if cAction:
              onClick += "|%s" % cAction
            onClick += "|options:save"
            onClick += "|set:needRedraw:1"


          y = y4 + (row) * dy
          if w1 > h1: # landscape
            dx = (x4-x1)
            w = w1 - dx
          else: # portrait
            dx = (x2)
            w = w1

          smallButtonW = dx/2.0
          smallButtonH = dy/2.0

          # Draw the option button and make it clickable
          self.menuModule.drawButton(cr,
            x4,
            y,
            w,
            dy,
            None,
            "generic", # background for a 3x1 icon
            "")
          # due to the button on the righ, register a slightly smaller area
          clickHandler.registerXYWH(x4, y, w-smallButtonW, dy, onClick)
            
          # draw mode specific combined toggle & indicator
          if self.modrana.hasKeyModifierInMode(variable, mode):
            toggleText = '<span color="green">ON</span>#per Mode'
            modeSpecToggleAction = "ml:options:removeKeyModifier:%s;%s" % (variable, mode)
          else:
            toggleText = "OFF#per Mode"
            modeSpecToggleAction = "ml:options:addKeyModifier:%s;%s" % (variable, mode)

          self.menuModule.drawButton(cr,
            x4+w-smallButtonW,
            y,
            smallButtonW,
            smallButtonH,
            toggleText,
            "generic",
            modeSpecToggleAction)

          groupName = choices['groupName']
          if 'noToolsIcon' not in choices:
            # draw tools button
            self.menuModule.drawButton(cr,
              x4+w-smallButtonW,
              y+smallButtonH,
              smallButtonW,
              smallButtonH,
              None,
              "tools", # tools icon
              "ml:options:go2ItemToolsMenu:%s;%d;%s" % (groupName, index, variable))


          border = 20

          # 1st line: option name
          self.menuModule.showText(cr, title, x4+border, y+border, w*0.95 - smallButtonW - border)

          # 2nd line: current value
          self.menuModule.showText(cr, valueDescription, x4 + 0.15 * w, y + 0.6 * dy, w*0.85 - smallButtonW - border)

          # in corner: row number
          indexX = x4+w*0.90-smallButtonW
          self.menuModule.showText(cr, "%d/%d" % (index+1, numItems), indexX, y+dy*0.07, w * 0.10 - border, 20)

#  def checkProfilePath(self):
#    """check if the profile folder exists, try to create it if not"""
#    if os.path.exists(self.getProfilePath()):
#      return True
#    else:
#      try:
#        os.makedirs(self.profileFolderPath)
#        print "creating profile folder in: %s" % self.profileFolderPath
#        return True
#      except Exception, e:
#        print "options:Creating profile folder in path: %s failed:\n%s" % (self.profileFolderPath, e)
#        return False

  def shutdown(self):
    """save the dictionary on exit"""
    self.save()

if(__name__ == "__main__"):
  a = options({},{'viewport':(0,0,600,800)})
  a.firstTime()
