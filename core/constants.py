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
DEFAULT_THEME_NAME = "Default"

LOCATION_TIMEOUT = 30 # in seconds
INTERNET_CONNECTIVITY_TIMEOUT = 30 # in seconds

ONLINE = True
OFFLINE = False
CONNECTIVITY_UNKNOWN = None

# tile storage
DEFAULT_TILE_STORAGE_TYPE = "files"
TILE_STORAGE_FILES = "files"
TILE_STORAGE_SQLITE = "sqlite"

# GTK GUI
PANGO_ON = '<span color="green">ON</span>'
PANGO_OFF = '<span color="red">OFF</span>'

# threads
THREAD_POI_SEARCH = "modRanaPOISearch"
THREAD_ADDRESS_SEARCH = "modRanaAddressSearch"
THREAD_WIKIPEDIA_SEARCH_NOMINATIM = "modRanaWikipediaSearchNominatim"
THREAD_REVERSE_GEOCODING = "modRanaReverseGeocoding"
THREAD_LOCAL_SEARCH_GOOGLE = "modRanaLocalSearchGoogle"
THREAD_ROUTING_ONLINE_GOOGLE = "modRanaRoutingOnlineGoogle"
THREAD_ROUTING_OFFLINE_MONAV = "modRanaRoutingOfflineMonav"
THREAD_GPSD_CONSUMER = "modRanaGPSDConsumer"
# tile down-/loading
THREAD_TILE_DOWNLOAD_MANAGER = "modRanaTileDownloadManager"
THREAD_TILE_DOWNLOAD_WORKER = "modRanaTileDownloadWorker"
THREAD_TILE_STORAGE_LOADER = "modRanaTileStorageLoader"

THREAD_CONNECTIVITY_CHECK = "modRanaConnectivityCheck"
THREAD_LOCATION_CHECK = "modRanaCurrentPositionCheck"

THREAD_TESTING_PROVIDER = "modRanaTestingProvider"

# thread pools
THREAD_POOL_AUTOMATIC_TILE_DOWNLOAD = "automaticTileDownload"
THREAD_POOL_BATCH_DOWNLOAD = "batchTileDownload"
THREAD_POOL_BATCH_SIZE_CHECK = "batchTileSizeCheck"

# default thread counts for pools
DEFAULT_THREAD_COUNT_AUTOMATIC_TILE_DOWNLOAD = 10
# Default number of threads for bach tile download, even a value of 10
# can lead to 3000+ open sockets on a fast Internet connection
# handle with care :)
# UPDATE: modRana now reuses open sockets so it might not be that bad any more
DEFAULT_THREAD_COUNT_BATCH_DOWNLOAD = 5
# Default number of batch size estimation threads - this sets the number of threads
# used for determining the size of the batch download (from http headers)
# NOTE: even though we are downloading only the headers, for a few thousand tiles this can be an
#       un-trivial amount of data (so use this with caution on metered connections)
DEFAULT_THREAD_COUNT_BATCH_SIZE_CHECK = 20

# tile download request queue default size
# * up to 100 download tasks can be stored in the request queue
# * up to DEFAULT_THREAD_COUNT_AUTOMATIC_TILE_DOWNLOAD tasks can be in progress
# * if a 101th request comes, it replaces the oldest not in progress task
DEFAULT_AUTOMATIC_TILE_DOWNLOAD_TASK_QUEUE_SIZE = 100

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

# local search
DEFAULT_LOCAL_SEARCH_RADIUS=10000  # in meters

# API access
GOOGLE_API_KEY = 'ABQIAAAAv84YYgTIjdezewgb8xl5_xTKlax5G-CAZlpGqFgXfh-jq3S0yRS6XLrXE9CkHPS6KDCig4gHvHK3lw'
GOOGLE_PLACES_API_KEY = 'AIzaSyAUbkZEu97uzwbl9IA4DNEMLlPg_gPlNTw'
GEONAMES_USERNAME = "modrana"

# tile download status codes
TILE_DOWNLOAD_SUCCESS = 0
TILE_DOWNLOAD_ERROR = 1
TILE_DOWNLOAD_TEMPORARY_ERROR = 2
TILE_DOWNLOAD_QUEUE_FULL = 3
