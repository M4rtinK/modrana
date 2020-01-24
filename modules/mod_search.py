# -*- coding: utf-8 -*-
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
from core.point import Point
from modules.base_module import RanaModule
from core import geo
import math
import re

try:  # Python 2.7+
    from collections import OrderedDict as odict
except ImportError:
    from core.backports.odict import odict  # Python <2.7


def getModule(*args, **kwargs):
    return Search(*args, **kwargs)


class Search(RanaModule):
    """Search for POI"""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self.localSearchResults = None # GLS results from onlineServices
        self.scroll = 0
        self.list = None # processed results: (distance from pos, result, absolute index)
        self.maxIndex = 0 # based on the number of items in the list
        self.where = 'position'
        self.filters = {}
        # names of marker groups used for search results
        self._relatedMarkerGroups = ["addressResults", "wikipediaResults"]

    def loadFilters(self):
        """fill the filter directory
        the different categories are all represented by ordered dictionaries"""
        filters = {}
        a = odict()
        a["hotel"] = {"name": "Hotel", "search": "hotel"}
        a["hostel"] = {"name": "Hostel", "search": "hostel"}
        a["motel"] = {"name": "Motel", "search": "motel"}
        a["camp"] = {"name": "Camp", "search": "camp"}
        filters['Sleep'] = a

        a = odict()
        a["supermarket"] = {"name": "Supermarket", "search": "supermarket"}
        a["hypermarket"] = {"name": "Hypermarket", "search": "hypermarket"}
        a["shopping_center"] = {"name": "Shopping center", "search": "shopping center"}
        a["gas_station"] = {"name": "Gas station", "search": "gas station"}
        a["outdoor"] = {"name": "Outdoor", "search": "outdoor"}
        a["diy"] = {"name": "DIY", "search": "DIY"}
        a["bank"] = {"name": "Bank", "search": "bank"}
        a["atm"] = {"name": "ATM", "search": "ATM"}
        a["bookstore"] = {"name": "Bookstore", "search": "bookstore"}
        a["computer_store"] = {"name": "Computer store", "search": "computer store"}
        filters['Buy'] = a

        a = odict()
        a["pub"] = {"name": "Pub", "search": "pub"}
        a["pub_food"] = {"name": "Pub food", "search": "pub food"}
        a["bar"] = {"name": "Bar", "search": "bar"}
        a["food"] = {"name": "Food", "search": "food"}
        a["restaurant"] = {"name": "Restaurant", "search": "restaurant"}
        a["cafe"] = {"name": "Cafe", "search": "cafe"}
        a["pizza"] = {"name": "Pizza", "search": "pizza"}
        a["fast_food"] = {"name": "Fast food", "search": "fast food"}
        filters['Food'] = a

        a = odict()
        a["police"] = {"name": "Police station", "search": "police"}
        a["fire_station"] = {"name": "Fire dpt.", "search": "fire"}
        a["info"] = {"name": "Information", "search": "information"}
        a["hospital"] = {"name": "Hospital", "search": "hospital"}
        a["pharmacy"] = {"name": "Pharmacy", "search": "pharmacy"}
        a["ranger"] = {"name": "Ranger", "search": "ranger"}
        a["law"] = {"name": "Law", "search": "law"}
        a["embassy"] = {"name": "Embassy", "search": "embassy"}
        filters['Help'] = a

        a = odict()
        a["car_hire"] = {"name": "Car hire", "search": "car hire"}
        a["bike_hire"] = {"name": "Bike hire", "search": "bike hire"}
        a["ski_hire"] = {"name": "Ski hire", "search": "Sky hire"}
        filters['Hire'] = a

        a = odict()
        a["car_park"] = {"name": "Car park", "search": "car park"}
        a["free_car_park"] = {"name": "Free car park", "search": "free car park"}
        a["bike_park"] = {"name": "Bike park", "search": "bike park"}
        a["lay_by"] = {"name": "Lay-by", "search": "lay by"}
        filters['Park'] = a

        a = odict()
        a["airport"] = {"name": "Airport", "search": "airport"}
        a["heliport"] = {"name": "Heliport", "search": "heliport"}
        a["spaceport"] = {"name": "Spaceport", "search": "spaceport"}
        a["train_station"] = {"name": "Train station", "search": "train station"}
        a["bus"] = {"name": "Bus", "search": "bus"}
        a["tram"] = {"name": "Tram", "search": "tram"}
        a["subway"] = {"name": "Subway", "search": "subway"}
        a["station"] = {"name": "Station", "search": "station"}
        a["ev"] = {"name": "EV charging", "search": "EV charging station"}
        a["gas_station"] = {"name": "Gas station", "search": "gas station"}
        a["ferry"] = {"name": "Ferry", "search": "ferry"}
        a["harbour"] = {"name": "Harbour", "search": "harbour"}
        filters['Travel'] = a

        a = odict()
        a["bike_shop"] = {"name": "Bike shop", "search": "bike shop"}
        a["garage"] = {"name": "Garage", "search": "garage"}
        filters['Repair'] = a

        a = odict()
        a["hotspot"] = {"name": "Hotspot", "search": "hotspot"}
        a["free_wifi"] = {"name": "Free wifi", "search": "free wifi"}
        a["wireless_internet"] = {"name": "Wireless", "search": "wireless internet"}
        a["internet_cafe"] = {"name": "Internet cafe", "search": "Category: Internet cafe"}
        a["library"] = {"name": "Library", "search": "library"}
        filters['Internet'] = a

        a = odict()
        a["sightseeing"] = {"name": "Sightseeing", "search": "sightseeing"}
        a["tourist_information"] = {"name": "Tourist info", "search": "tourist information"}
        a["cinema"] = {"name": "Cinema", "search": "cinema"}
        a["theater"] = {"name": "Theater", "search": "theater"}
        a["gallery"] = {"name": "Gallery", "search": "gallery"}
        a["museum"] = {"name": "Museum", "search": "museum"}
        a["wine_cellar"] = {"name": "Wine cellar", "search": "wine cellar"}
        a["national_park"] = {"name": "National park", "search": "national park"}
        a["wc"] = {"name": "WC", "search": "WC"}
        a["swimming_pool"] = {"name": "Swimming pool", "search": "swimming pool"}
        filters['Tourism'] = a

        self.filters = filters

    def handleMessage(self, message, messageType, args):
        # without this if, we would search also for the commands that move the listable menu
        # lets hope no one needs to search for reset, up or down :)

        if message == 'clearSearch':
            self.localSearchResults = None
            self.list = None
            # also remove all search related marker groups
            markers = self.m.get("markers")
            if markers:
                for group in self._relatedMarkerGroups:
                    markers.removeGroup(group)
            self.notify("all search results cleared", 2000)
            #TODO: also clear address & Wikipedia search results
        elif message == 'storePOI':
            store = self.m.get('storePOI', None)
            if store is None:
                return
            resultNr = self.get('searchResultsItemNr', None)
            if resultNr is None:
                return
            resultTuple = filter(lambda x: x[2] == int(resultNr), self.list).pop()
            result = resultTuple[1]
            store.storeLocalSearchResult(result)

        elif message == 'setWhere': # set the search region
            if messageType == 'ms' and args:
                self.where = args

        elif message == 'localSearch':
            if messageType == 'ml' and args:
                query = None
                location = None
                online = self.m.get('onlineServices', None)
                if not online:
                    self.log.error("online services module not present")
                    return
                lsType = args[0]
                sensor = 'false'
                if lsType == "coords": # search around coordinates
                    # format: type;lat,lon;query
                    # parse coordinates
                    lat = float(args[1])
                    lon = float(args[2])
                    location = Point(lat, lon)
                    query = args[3]
                elif lsType == "location":
                    # search around a location (address, coordinates, etc. ),
                    # modRana just forwards the location to the search engine
                    location = args[1]
                    query = args[2]
                elif lsType == "position": # search around current position
                    query = args[1]
                    sensor = 'true'
                    fix = self.get('fix', 0)
                    pos = self.get('pos', None)
                    if fix > 1 and pos:
                        lat, lon = pos
                        location = Point(lat, lon)
                    else:
                        self.log.info("position unknown - trying to get GPS lock")
                        # location = None will trigger GPS fix attempt (provided GPS is enabled in Options)
                        location = None
                elif lsType == "view": #search around current map center
                    query = args[1]
                    proj = self.m.get('projection', None)
                    if proj:
                        centreLL = proj.getScreenCentreLL()
                        if centreLL:
                            (lat, lon) = centreLL
                            location = Point(lat, lon)
                        else:
                            self.log.warning("screen center coordinates unknown")
                            return

                if query:
                    online.localSearchAsync(query, self._handleLocalSearchResultsCB,
                                            around=location, sensor=sensor)

        elif message == "search":
            if messageType == "ml" and args:
                sType = args[0]
                if sType == "address":
                    self.log.info("address search")
                    query = args[1]
                    online = self.m.get('onlineServices', None)
                    if online:
                        # geocode the text input asynchronously
                        online.geocodeAsync(query, self._address2llCB)
                    else:
                        self.log.error("online services module missing")
                elif sType == "wikipedia":
                    self.log.info("Wikipedia search")
                    query = args[1]
                    online = self.m.get('onlineServices', None)
                    if online:
                        # search Wikipedia asynchronously
                        online.wikipediaSearchAsync(query, self._handleWikipediaResultsCB)
                    else:
                        self.log.error("online services module missing")

        # DEPRECIATED ?, use the localSearch method
        # TODO: depreciate this
        elif message == 'searchThis': # search for a term in the message string
            if messageType == 'ms' and args:
                searchTerm = args
                lat = None
                lon = None
                online = self.m.get('onlineServices', None)
                if online is None:
                    self.log.error("online services module not present")
                    return

                if self.where == 'position':
                    self.log.info("near position")
                    pos = self.get('pos', None)
                    sensor = 'true'
                    if pos is None:
                        self.log.error("our position is not known")
                        return
                    else:
                        (lat, lon) = pos
                elif self.where == 'view':
                    self.log.info("near view")
                    proj = self.m.get('projection', None)
                    sensor = 'false'
                    if proj:
                        centreLL = proj.getScreenCentreLL()
                        if centreLL:
                            (lat, lon) = centreLL
                        else:
                            self.log.error("screen center coordinates unknown")
                            return
                if lat and lon:
                    location = Point(lat, lon)
                    online.localSearchAsync(searchTerm, self._handleLocalSearchResultsCB,
                                            around=location, sensor=sensor)

            #        try:
            #          searchList = []
            #          filters = self.filters
            #          for topLevel in filters: # iterate over the filter categories
            #            for key in filters[topLevel]: # iterate over the search keywords
            #              if filters[topLevel][key] == searchTerm: # is this the search word for the current amenity ?
            #                searchList.append(key) # add the matching search word to the list
            #          term = searchList[0] # we have a list, because an amenity can have theoretically more "providers"
            #
            #        except:
            #          self.log.error("search: key not present in the filter dictionary, using the key as search term")
            #          term = searchTerm

            # initiate asynchronous search, that is running in a separate thread

            #        if local['responseStatus'] != 200:
            #          self.log.error("search: google returned %d return code" % local['responseStatus'])
            #        self.log.error(("search: local search returned %d results") % len(local['responseData']['results']))
            #        self.localSearchResults = local

        elif message == "customQuery":
            # start text input for custom query
            entry = self.m.get('textEntry', None)
            if entry:
                entryText = ""
                entry.entryBox(self, 'customQuery', 'Enter your search query', entryText,
                               persistentKey="lastCustomLocalSearchQuery")

        elif message == "searchAddress":
            # start text input for an address
            entry = self.m.get('textEntry', None)
            if entry:
                entry.entryBox(self, 'address', description='Enter an address or location description',
                               persistentKey="lastAddressSearchInput")

        elif message == "searchWikipedia":
            # start text input for an address
            entry = self.m.get('textEntry', None)
            if entry:
                entry.entryBox(self, 'wikipedia', description='Wikipedia search query',
                               persistentKey="lastWikipediaSearchInput")

        elif message == "routeToActiveResult":
            # get a route from current position to active search result
            # * center on the current position
            # -> we want to actually got to there :)
            activeResultTuple = self.getActiveResultTupple()
            activeResult = activeResultTuple[1]
            lat, lon = activeResult.getLL()
            # clear any old route and route to the result
            self.sendMessage('route:clearRoute|md:route:route:type=pos2ll;toLat=%f;toLon=%f;show=start' % (lat, lon))

    def getActiveResultTupple(self):
        resultNumber = int(self.get('searchResultsItemNr', 0))
        return self.getResult(resultNumber)

    def getResult(self, resultNumber, resultList=None):
        if resultList is None:
            resultList = self.updateDistance()
        return filter(lambda x: x[2] == resultNumber, resultList).pop() # get the result for the ABSOLUTE key

    def describeItem(self, index, category, itemList):
    #    longName = name = item.getTracklogName()
    #    self.log.debug(filter(lambda x: x.getTracklogName() == longName, loadedTracklogs))
    #    self.log.debug(loadedTracklogs.index(item))
        action = "set:menu:search#searchResultsItem"
        action += "|set:searchResultsItemNr:%d" % itemList[index][
            2] # here we use the ABSOLUTE index, not the relative one
        #    action += "|set:menu:"
        #    name = item.getTracklogName().split('/').pop()

        #    action += "|set:searchResultShowLatLon:%s,%s" % (lat,lon)

        point = itemList[index][1]
        # Pango does not like & so we need to replace it with &amp
        name = re.sub('&', '&amp;', point.name)

        units = self.m.get('units', None)
        distanceString = units.km2CurrentUnitString(itemList[index][0], dp=2) # use correct units

        description = "%s" % distanceString

        return (
            name,
            description,
            action)

    def showText(self, cr, text, x, y, widthLimit=None, fontsize=40):
        if text:
            cr.set_font_size(fontsize)
            stats = cr.text_extents(text)
            (textWidth, textHeight) = stats[2:4]

            if widthLimit and textWidth > widthLimit:
                cr.set_font_size(fontsize * widthLimit / textWidth)
                stats = cr.text_extents(text)
                (textWidth, textHeight) = stats[2:4]

            cr.move_to(x, y + textHeight)
            cr.show_text(text)

    def updateDistance(self):
        if self.localSearchResults:
            position = self.get("pos", None) # our lat lon coordinates
            resultList = []
            index = 0
            for point in self.localSearchResults: # we iterate over the local search results
                if position is not None:
                    (lat1, lon1) = position
                    (lat2, lon2) = point.getLL()
                    distance = geo.distance(lat1, lon1, lat2, lon2)
                    resultTuple = (distance, point, index)
                    resultList.append(resultTuple) # we pack each result into a tuple with ist distance from us
                else:
                    resultTuple = (
                    0, point, index) # in this case, we dont know our position, so we say the distance is 0
                    resultList.append(resultTuple)
                index += 1
            self.list = resultList
            return resultList
        else:
            self.log.error("error -> distance update on empty results")

    def _address2llCB(self, points):
        if points:
            self.log.info("geocoding done - something found")
            markers = self.m.get('markers', None)
            name = 'addressResults'
            if markers:
                g = markers.addGroup(name, points, menu=True)
                menu = g.getMenuInstance()
                if len(points) == 1: # if only one result is found, center on it righ away
                    point = points[0]
                    self._jumpToPoint(point)
                else:
                    self.sendMessage('set:menu:menu#list#%s' % name)
                menu.setOnceBackAction('set:menu:searchWhat')
            else: # just jump to the first result
                point = points[0]
                self._jumpToPoint(point)
        else:
            self.log.info("geocoding done - nothing found")
            self.sendMessage('ml:notification:m:No results found for this address.;5')


    def _handleLocalSearchResultsCB(self, results):
        self.log.info("local search result received")
        # only show the results list if there are some results
        if results:
            self.localSearchResults = results
            self.set('menu', 'search#searchResults')

    def _handleWikipediaResultsCB(self, results):
        """Handle results from the asynchronous Wikipedia search"""
        if results:
            self.log.info("wikipedia search done - something found")
            name = 'wikipediaResults'
            markers = self.m.get('markers', None)
            if markers:
                g = markers.addGroup(name, results, menu=True)
                menu = g.getMenuInstance()
                if len(results) == 1: # if only one result is found, center on it righ away
                    point = results[0]
                    self._jumpToPoint(point)
                else:
                    self.sendMessage('set:menu:menu#list#%s' % name)
                menu.setOnceBackAction('set:menu:searchWhat')
            else: # just jump to the first result
                point = results[0]
                self._jumpToPoint(point)
        else:
            self.log.info("wikipedia search done - nothing found")
            self.sendMessage('ml:notification:m:No results found for this query.;5')

    def _jumpToPoint(self, point):
        mw = self.m.get('mapView', None)
        if mw:
            mw.jump2point(point)


