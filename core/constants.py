# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# ModRana constants
#----------------------------------------------------------------------------
# Copyright 2013, Martin Kolman
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

DEFAULT_COORDINATES = 49.2, 16.616667  # Brno
#(49.233056, 17.666944) is Zlin

DEFAULT_THEME_ID = "default"

# GTK GUI
PANGO_ON = '<span color="green">ON</span>'
PANGO_OFF = '<span color="red">OFF</span>'

# threads
THREAD_POI_SEARCH = "modRanaPOISearch"
THREAD_ADDRESS_SEARCH = "modRanaAddressSearch"
THREAD_TESTING_PROVIDER = "modRanaTestingProvider"
THREAD_ROUTING_ONLINE_GOOGLE = "modRanaRoutingOnlineGoogle"
THREAD_ROUTING_OFFLINE_MONAV = "modRanaRoutingOfflineMonav"

# device types
DEVICE_TYPE_DESKTOP = 1
DEVICE_TYPE_SMARTPHONE = 2
DEVICE_TYPE_TABLET = 3

# routing
ROUTE_DEFAULT_LANGUAGE = "en"

# Monav routing return codes
ROUTING_SUCCESS = 0
ROUTING_NO_DATA = 1 # failed to load routing data
ROUTING_LOAD_FAILED = 2 # failed to load routing data
ROUTING_LOOKUP_FAILED = 3 # failed to locate nearest way/edge
ROUTING_ROUTE_FAILED = 4 # failed to compute route
ROUTING_ADDRESS_NOT_FOUND = 5 # start or destination address not found

# route types
ROUTE_PEDESTRIAN = 1
ROUTE_BIKE = 2
ROUTE_CAR = 3

# API access
GOOGLE_API_KEY = 'ABQIAAAAv84YYgTIjdezewgb8xl5_xTKlax5G-CAZlpGqFgXfh-jq3S0yRS6XLrXE9CkHPS6KDCig4gHvHK3lw'
