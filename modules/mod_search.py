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
from modules.base_module import RanaModule

from collections import OrderedDict as odict

def getModule(*args, **kwargs):
    return Search(*args, **kwargs)


class Search(RanaModule):
    """Search for POI"""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self.local_search_results = None # GLS results from onlineServices
        self.list = None # processed results: (distance from pos, result, absolute index)
        self.where = 'position'
        self.filters = {}

    def load_filters(self):
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