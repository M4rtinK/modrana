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

def getModule(m,d):
  return(search(m,d))

class search(ranaModule):
  """Search for POI"""
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
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
  def firstTime(self):
    m = self.m.get("menu", None)
    if(m):
      m.clearMenu("search", 'set:menu:main')
      #m.addItem('search', 'centre', 'centre', 'set:menu:search_')
      for category, items in self.filters.items():
        m.clearMenu("search_"+category, 'set:menu:search')
        m.addItem('search', category, category.lower(), 'set:menu:search_'+category)
        for name,filter in items.items():
          m.addItem('search_'+category, name, name.lower(), "search:"+filter)
        