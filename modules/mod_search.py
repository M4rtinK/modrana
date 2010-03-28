#!/usr/bin/python
#----------------------------------------------------------------------------
# Search for POI
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
import geo
import math

def getModule(m,d):
  return(search(m,d))

class search(ranaModule):
  """Search for POI"""
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.localSearchResults = None
    self.scroll = 0
    self.filters = {
      'Sleep':{
        'Hotel':'tourism=hotel',
        'Hostel':'tourism=hostel'},
      'Buy':{
        'Supermarket':'amenity=supermarket',
        'Outdoor':'shop=outdoor',
        'DIY':'search:tourism=diy'},
      'Food':{
        'Pub food':'amenity=pub;food=yes',
        'Restaurant':'amenity=restaurant',
        'Cafe':'amenity=cafe',
        'Fast food':'amenity=fast_food'},
      'Help':{
        'Police Stn':'amenity=police',
        'Fire Stn':'amenity=fire',
        'Hospital':'amenity=hospital',
        'Ranger':'amenity=ranger_station',
        'Pharmacy':'amenity=pharmacy'},
      'Hire':{
        'Car hire':'amenity=car_hire',
        'Bike hire':'amenity=bike_hire',
        'Ski hire':'amenity=ski_hire'},
      'Park':{
        'Car park':'amenity=parking',
        'Free car park':'amenity=parking;cost=free',
        'Bike park':'amenity=cycle_parking',
        'Lay-by':'amenity=layby'},
      'Repair':{
        'Bike shop':'amenity=bike_shop',
        'Garage':'amenity=garage'},
      }

  def handleMessage(self, message):
    # without this if, we would search also for the commands that move the listable menu
    # lets hope no one needs to search for reset, up or down :)
    if message=="up" or message=="down" or message=="reset" or message == 'centerOnResult' or message=='clearSearch':
      if(message == "up"):
        if(self.scroll > 0):
          self.scroll -= 1
      if(message == "down"):
        print "down"
        self.scroll += 1
      if(message == "reset"):
        self.scroll = 0
      if (message == "centerOnResult"):
        proj = self.m.get('projection', None)
        if proj == None:
          return
        ll = self.get('showGLSResultLL', None)
        if ll == None:
          return
        list = ll.split(',')
        lat = float(list[0])
        lon = float(list[1])
        self.set("centred",False) # turn off centering before moving screen to the result
        proj.recentre(lat, lon)
      if (message == 'clearSearch'):
        self.localSearchResults = None
        ll = self.set('showGLSResultLL', None)
      self.set("needRedraw", True)
      return


    online = self.m.get('onlineServices', None)
    if online == None:
      print "search: online services module not pressent"
      return

    position = self.get('pos', None)
    if position == None:
      print "search: our position is not known"
      return

    try:
      searchList = []
      filters = self.filters
      for topLevel in filters: # iterate over the filter cathegories
        for key in filters[topLevel]: # iterate over the search keywords
          if filters[topLevel][key] == message: # is this the search word for the current amenity ?
            searchList.append(key) # add the matching search word to the list
      term = searchList[0] # we have a list, because an amenity can have theoreticaly more "providers"

    except:
      print "search: key not present in the filter dictionary, using the key as search term"
      term = message

    (lat,lon) = position
    sufix = " near %f,%f" % (lat,lon)
    query = term + sufix
    print query
    local = online.googleLocalQuery(query)
    if local['responseStatus'] != 200:
      print "search: google returned %d return code" % local['responseStatus']
    print ("search: local search returned %d results") % len(local['responseData']['results'])
    self.localSearchResults = local


  def drawMenu(self, cr, menuName):
    # is this menu the correct menu ?
    if menuName != 'searchResults' and menuName != 'searchResultsItem':
      return # we arent the active menu so we dont do anything
    else:
      # setup the viewport
      (x1,y1,w,h) = self.get('viewport', None)
      dx = w / 3
      dy = h / 4

#      if w>h:
#        buttons = "left"
#      elif w<h:
#        buttons = "up"
#      elif w==h:
#        buttons = "up"

    if menuName == 'searchResults':
      menus = self.m.get("menu",None)

      # * draw "escape" button
      menus.drawButton(cr, x1, y1, dx, dy, "", "up", "search:reset|set:menu:search")
      # * scroll up
      menus.drawButton(cr, x1+dx, y1, dx, dy, "", "up_list", "%s:up" % self.moduleName)
      # * scroll down
      menus.drawButton(cr, x1+2*dx, y1, dx, dy, "", "down_list", "%s:down" % self.moduleName)
      
      list = self.updateDistance()

      if self.get('GLSOrdering', 'default') == 'distance': # if ordering by distance is turned on, sort the list
        list.sort()

      category = ""

      # One option per row
      for row in (0,1,2): # TODO: dynamic adjustment (how to guess the screensize vs dpi ?)
        index = self.scroll + row
        numItems = len(list)
        if(0 <= index < numItems):

          (text1,text2,onClick) = self.describeItem(index, category, list)

          y = y1 + (row+1) * dy

          # Draw background and make clickable
          menus.drawButton(cr,
            x1,
            y,
            w,
            dy,
            "",
            "3h", # background for a 3x1 icon
            onClick)

          border = 20

          self.showText(cr, text1, x1+border, y+border, w-2*border)

          # 2nd line: current value
          self.showText(cr, text2, x1 + 0.15 * w, y + 0.6 * dy, w * 0.85 - border)

          # in corner: row number
          self.showText(cr, "%d/%d" % (index+1, numItems), x1+0.85*w, y + 0.42 * dy, w * 0.15 - border, 20)

    if menuName == 'searchResultsItem':
      """draw the menu describing a single GLS result"""
      list = self.updateDistance()

      if self.get('GLSOrdering', 'default') == 'distance': # if ordering by distance is turned on, sort the list
        list.sort()

      resultNumber = int(self.get('searchResultsItemNr', 0))

      """
         because the results can be ordered in different manners, we use the absolute index,
         which is created from the initial ordering
         without this,(with distance sort) we would get different results for a key, if we moved fast enoght :)
      """
      result = filter(lambda x: x[2] == resultNumber, list).pop() # get the result for the ABSOLUTE key
      self.drawGLSResultMenu(cr, result)

    return

  def describeItem(self, index, category, list):
#    longName = name = item.getTracklogName()
#    print filter(lambda x: x.getTracklogName() == longName, loadedTracklogs)
#    print loadedTracklogs.index(item)
    action = "set:menu:searchResultsItem"
    action += "|set:searchResultsItemNr:%d" % list[index][2] # here we use the ABSOLUTE index, not the relative one
#    action += "|set:activeTracklog:%d|set:menu:tracklogInfo" % list['responseData']['results'][item]['titleNoFormatting']
#    action += "|set:menu:"
#    name = item.getTracklogName().split('/').pop()

#    lat = list[index][1]['lat']
#    lon = list[index][1]['lng']
#    action += "|set:searchResultShowLatLon:%s,%s" % (lat,lon)

    name = "%s" % list[index][1]['titleNoFormatting']

    units = self.m.get('units', None)
    distanceString = units.km2CurrentUnitString(list[index][0]) # use correct units

    description = "%s" % distanceString

    return(
      name,
      description,
      action)

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

  def updateDistance(self):
      position = self.get("pos", None) # our lat lon coordinates
      list = []
      index = 0
      for item in self.localSearchResults['responseData']['results']: # we iterate over the local search results
        if position != None:
          (lat1,lon1) = position
          (lat2,lon2) = (float(item['lat']), float(item['lng']))
          distance = geo.distance(lat1,lon1,lat2,lon2)
          tupple = (distance, item, index)
          list.append(tupple) # we pack each result into a tupple with ist distance from us
        else:
          tupple = (0, item, index) # in this case, we dont know our position, so we say the distance is 0
          list.append(tupple)
        index = index + 1
      return list

  def updateItemDistance(self):
      position = self.get("pos", None) # our lat lon coordinates
      if position != None:
        (lat1,lon1) = position
        (lat2,lon2) = (float(item['lat']), float(item['lng']))
        distance = geo.distance(lat1,lon1,lat2,lon2)
      else:
        distance = 0 # in this case, we dont know our position, so we say the distance is 0
      return distance


  def drawGLSResultMenu(self, cr, resultTupple):
    """draw an info screen for a Google local search result"""
    (x1,y1,w,h) = self.get('viewport', None)
    dx = w / 3
    dy = h / 4

    (distance, result,index) = resultTupple
    lat = float(result['lat'])
    lon = float(result['lng'])
    menus = self.m.get("menu",None)
    units = self.m.get('units', None)
    distanceString = units.km2CurrentUnitString(float(distance))
    # * draw "escape" button
    menus.drawButton(cr, x1, y1, dx, dy, "", "up", "search:reset|set:menu:searchResults")
    # * draw "show" button
    menus.drawButton(cr, x1+dx, y1, dx, dy, "show", "generic", "search:reset|set:menu:None|set:showGLSResultLL:%f,%f|search:centerOnResult" % (lat,lon))
    # * draw "add POI" button
    menus.drawButton(cr, x1+2*dx, y1, dx, dy, "add POI", "generic", "search:reset|set:menu:searchResults")
    # * draw info box
    menus.drawButton(cr, x1, y1+dy, w, h-dy, "", "3h", "set:menu:None")

    # * draw details from the search result
    text = "%s (%s)" % (result['titleNoFormatting'],distanceString)

    try: # the adress can be unknown
      for addressLine in result['addressLines']:
        text += "|%s" % addressLine
    except:
      text += "|%s" % "no adress found"

    try: # it seems, that this entry is no guarantied
      for phoneNumber in result['phoneNumbers']:
        type = ""
        if phoneNumber['type'] != "":
          type = " (%s)" % phoneNumber['type']
        text += "|%s%s" % (phoneNumber['number'], type)
    except:
      text += "|%s" % "no phone numbers found"

    text += "|coordinates: %f, %f" % (lat,lon)

    menus.drawTextToSquare(cr, x1, y1+dy, w, h-dy, text) # dsiplay the text in the box

  def drawMapOverlay(self, cr):
    """Draw overlay that's part of the map"""
    # draw the GLS results on the map
    if self.localSearchResults == None:
      return
    proj = self.m.get('projection', None)
    captions = self.get('drawGLSResultCaptions', True)

    ll = self.get('showGLSResultLL', None)

    # highlight the currently selected result on the map
    if ll != None:
      list = ll.split(',')
      lat = float(list[0])
      lon = float(list[1])
      (x,y) = proj.ll2xy(lat, lon)
      cr.set_line_width(8)
      cr.set_source_rgba(0, 0, 1, 0.7)
      cr.arc(x, y, 15, 0, 2.0 * math.pi)
      cr.stroke()
      cr.fill()

    for point in self.localSearchResults['responseData']['results']:
      (lat,lon) = (float(point['lat']), float(point['lng']))
      (x,y) = proj.ll2xy(lat, lon)
      cr.set_source_rgb(0.0, 0.0, 0.0)
      cr.set_line_width(10)
      cr.arc(x, y, 3, 0, 2.0 * math.pi)
      cr.stroke()
      cr.set_source_rgb(1.0, 0.0, 0.0)
      cr.set_line_width(8)
      cr.arc(x, y, 2, 0, 2.0 * math.pi)
      cr.stroke()

      if captions == False:
        continue
      # draw caption with transparent background
      text = "%s" % point['titleNoFormatting'] # result caption

      cr.set_font_size(20)
      extents = cr.text_extents(text) # get the text extents
      (w,h) = (extents[2], extents[3])

      border = 2
      cr.set_line_width(2)
      cr.set_source_rgba(0, 0, 1, 0.45) # trasparent blue
      (rx,xy,rw,rh) = (x - border+10, y + border+h*0.2, w + 4*border, -(h*1.4))
      cr.rectangle(rx,xy,rw,rh) # create the transparent background rectangle
      cr.fill()

      cr.set_source_rgba(1, 1, 1, 0.95) # slightly trasparent white
      cr.move_to(x+10,y)
      cr.show_text(text) # show the trasparent result caption
      cr.stroke()


      cr.fill()







  def firstTime(self):
    m = self.m.get("menu", None)
    if(m):
      m.clearMenu("search", 'set:menu:main')
      #m.addItem('search', 'centre', 'centre', 'set:menu:search_')
      for category, items in self.filters.items():
        m.clearMenu("search_"+category, 'set:menu:search')
        m.addItem('search', category, category.lower(), 'set:menu:search_'+category)
        for name,filter in items.items():
          m.addItem('search_'+category, name, name.lower(), "set:menu:searchResults|search:"+filter)
      m.addItem('search', 'clear', 'clear', 'search:clearSearch|set:menu:None')
        