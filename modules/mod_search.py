
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
    self.localSearchResults = None # GLS results from onlineServices
    self.scroll = 0
    self.list = None # processed results: (distancefrom pos, rusult, absolut index)  
    self.filters = {
      'Sleep':{
        'Hotel':'tourism=hotel',
        'Hostel':'tourism=hostel',
        'Motel':'tourism=motel',
        'Camp':'amenity=camp'},
      'Buy':{
        'Supermarket':'amenity=supermarket',
        'Hypermarket':'amenity=hypermarket',
        'Shopping center':'amenity=shopping_center',
        'Gas station':'amenity=gas_station',
        'Outdoor':'shop=outdoor',
        'DIY':'search:tourism=diy',
        'Bank':'amenity=bank',
        'ATM':'amenity=atm',
        'Bookstore':'search:tourism=bookstore',
        'Computer store':'search:tourism=computer_store '},
      'Food':{
        'Pub food':'amenity=pub;food=yes',
        'Food':'amenity=food',
        'Restaurant':'amenity=restaurant',
        'Cafe':'amenity=cafe',
        'Pizza':'amenity=pizza',
        'Fast food':'amenity=fast_food'},
      'Help':{
#        'Police Stn':'amenity=police',
        'Police Station':'amenity=police',
        'Fire Stn':'amenity=fire',
        'Information center':'amenity=information',
        'Hospital':'amenity=hospital',
        'Ranger':'amenity=ranger_station',
        'Pharmacy':'amenity=pharmacy',
        'Law':'amenity=law',
        'Embassy':'amenity=law'},
      'Hire':{
        'Car hire':'amenity=car_hire',
        'Bike hire':'amenity=bike_hire',
        'Ski hire':'amenity=ski_hire'},
      'Park':{
        'Car park':'amenity=parking',
        'Free car park':'amenity=parking;cost=free',
        'Bike park':'amenity=cycle_parking',
        'Lay-by':'amenity=layby'},
      'Travel':{
        'Airport':'amenity=airport',
        'Heliport':'amenity=heliport',
        'Spaceport':'amenity=spaceport',
        'Train station':'amenity=train_station',
        'Bus':'amenity=bus',
        'Tram':'amenity=Tram',
        'Subway station':'amenity=subway_station',
        'Station':'amenity=station',
        'Ferry':'amenity=ferry',
        'Harbour':'amenity=harbour'},
      'Repair':{
        'Bike shop':'amenity=bike_shop',
        'Garage':'amenity=garage'},
      'Internet':{
        'Hotspot':'amenity=hotspot',
        'Wireless internet':'amenity=wireless_internet',
        'Category: Internet cafe':'amenity=internet_cafe', # TODO: improve this, it finds more internet cafais but looks ugly :)
        'Library':'amenity=library',
        'Free wifi':'amenity=free_wifi'},
      'Tourism':{
        'Sightseeing':'amenity=sightseeing',
        'Tourist information':'amenity=tourist_information',
        'Cinema':'amenity=cinema',
        'Theater':'amenity=theater',
        'Gallery':'amenity=gallery',
        'Museum':'amenity=museum',
        'Wine celar':'amenity=wine_celar', # TODO: improve this, it finds more internet cafais but looks ugly :)
        'National park':'amenity=national_park',
        'Swimming pool':'amenity=swimming_pool'},
      }

  def handleMessage(self, message, type, args):
    # without this if, we would search also for the commands that move the listable menu
    # lets hope no one needs to search for reset, up or down :)
    if message=="up" or message=="down" or message=="reset" or message=='clearSearch' or message=='storePOI':
      if(message == "up"):
        if(self.scroll > 0):
          self.scroll -= 1
          self.set("needRedraw", True)
      if(message == "down"):
        print "down"
        self.scroll += 1
        self.set("needRedraw", True)
      if(message == "reset"):
        self.scroll = 0
        self.set("needRedraw", True)
      if (message == 'clearSearch'):
        self.localSearchResults = None
        self.list = None
      if (message == 'storePOI'):
        store = self.m.get('storePOI', None)
        if store == None:
          return
        resultNr = self.get('searchResultsItemNr', None)
        if resultNr == None:
          return
        tupple = filter(lambda x: x[2] == int(resultNr), self.list).pop()
        result = tupple[1]
        store.storeGLSResult(result)

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

    if menuName == 'searchResults':
      menus = self.m.get("menu",None)

      # get coordinate allocation for the menu elements
      (e1,e2,e3,e4,alloc) = menus.threePlusOneMenuCoords()
      (x1,y1) = e1
      (x2,y2) = e2
      (x3,y3) = e3
      (x4,y4) = e4
      (w1,h1,dx,dy) = alloc

      # * draw "escape" button
      menus.drawButton(cr, x1, y1, dx, dy, "", "up", "search:reset|set:menu:search")
      # * scroll up
      menus.drawButton(cr, x2, y2, dx, dy, "", "up_list", "%s:up" % self.moduleName)
      # * scroll down
      menus.drawButton(cr, x3, y3, dx, dy, "", "down_list", "%s:down" % self.moduleName)
      
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

          y = y4 + (row) * dy
          w = w1 - (x4-x1)

          # Draw background and make clickable
          menus.drawButton(cr,
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
      self.list = list
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


    # get coordinate allocation for the menu elements
    menus = self.m.get("menu",None)
    (e1,e2,e3,e4,alloc) = menus.threePlusOneMenuCoords()
    (x1,y1) = e1
    (x2,y2) = e2
    (x3,y3) = e3
    (x4,y4) = e4
    (w,h,dx,dy) = alloc

    (distance, result,index) = resultTupple
    lat = float(result['lat'])
    lon = float(result['lng'])
    units = self.m.get('units', None)
    distanceString = units.km2CurrentUnitString(float(distance))
    # * draw "escape" button
    menus.drawButton(cr, x1, y1, dx, dy, "", "up", "search:reset|set:menu:searchResults")
    # * draw "show" button
    action2 = "search:reset|set:menu:None|set:searchResultsItemNr:%d|mapView:recentre %f %f" % (index, lat, lon)
    menus.drawButton(cr, x2, y2, dx, dy, "on map#show", "generic", action2)
    # * draw "add POI" button
    menus.drawButton(cr, x3, y3, dx, dy, "add to POI", "generic", "search:reset|search:storePOI|set:menu:searchResults")
    # * draw info box
    w4 = w - x4
    h4 = h - y4
    menus.drawButton(cr, x4, y4, w4, h4, "", "generic", "set:menu:None")

    # * draw details from the search result
    text = "%s (%s)" % (result['titleNoFormatting'],distanceString)

    try: # the adress can be unknown
      print result['addressLines']
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

    menus.drawTextToSquare(cr, x4, y4, w4, h4, text) # display the text in the box

  def drawMapOverlay(self, cr):
    """Draw overlay that's part of the map"""
    # draw the GLS results on the map
    if self.localSearchResults == None:
      return
    proj = self.m.get('projection', None)
    captions = self.get('drawGLSResultCaptions', True)

    highlightNr = int(self.get('searchResultsItemNr', None))

    # highlight the currently selected result on the map


    for tupple in self.list:
      (distance, point, index) = tupple
      if index == highlightNr: # the highlighted result is draw in the end
        continue
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
      (rx,ry,rw,rh) = (x - border+10, y + border+h*0.2, w + 4*border, -(h*1.4))
      cr.rectangle(rx,ry,rw,rh) # create the transparent background rectangle
      m = self.m.get('clickHandler', None)
      # register clickable area
      if(m != None):
        m.registerXYWH(rx,ry-(-rh),rw,-rh, "search:reset|set:searchResultsItemNr:%d|set:menu:searchResultsItem" % index)
      cr.fill()
      # draw the actual text
      cr.set_source_rgba(1, 1, 1, 0.95) # slightly trasparent white
      cr.move_to(x+10,y)
      cr.show_text(text) # show the trasparent result caption
      cr.stroke()
      cr.fill()

    if highlightNr != None: # is there some search result to highlight ?
      tupple = filter(lambda x: x[2] == int(highlightNr), self.list).pop()
      result = tupple[1]
      lat = float(result['lat'])
      lon = float(result['lng'])
      (x,y) = proj.ll2xy(lat, lon)

      # draw the highlighting circle
      cr.set_line_width(8)
      cr.set_source_rgba(0, 0, 1, 0.55) # transparent blue
      cr.arc(x, y, 15, 0, 2.0 * math.pi)
      cr.stroke()
      cr.fill()

      # draw the point
      cr.set_source_rgb(0.0, 0.0, 0.0)
      cr.set_line_width(10)
      cr.arc(x, y, 3, 0, 2.0 * math.pi)
      cr.stroke()
      cr.set_source_rgb(1.0, 0.0, 0.0)
      cr.set_line_width(8)
      cr.arc(x, y, 2, 0, 2.0 * math.pi)
      cr.stroke()

      # draw a caption with transparent background
      text = "%s" % result['titleNoFormatting'] # result caption
      cr.set_font_size(20)
      extents = cr.text_extents(text) # get the text extents
      (w,h) = (extents[2], extents[3])
      border = 2
      cr.set_line_width(2)
      cr.set_source_rgba(0, 0, 1, 0.45) # trasparent blue
      (rx,ry,rw,rh) = (x - border+12, y + border+h*0.2 + 6, w + 4*border, -(h*1.4))
      cr.rectangle(rx,ry,rw,rh) # create the transparent background rectangle
      cr.fill()

      # register clickable area
      m = self.m.get('clickHandler', None)
      if(m != None):
        m.registerXYWH(rx,ry-(-rh),rw,-rh, "search:reset|set:searchResultsItemNr:%d|set:menu:searchResultsItem" % highlightNr)
      cr.fill()
      
      # draw the actual text
      cr.set_source_rgba(1, 1, 0, 0.95) # slightly trasparent white
      cr.move_to(x+15,y+7)
      cr.show_text(text) # show the trasparent result caption
      cr.stroke()

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
        