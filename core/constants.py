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
TILE_DOWNLOAD_TIMEOUT = 10 # in seconds

ONLINE = True
OFFLINE = False
CONNECTIVITY_UNKNOWN = None

# tile storage
DEFAULT_TILE_STORAGE_TYPE = "files"
TILE_STORAGE_FILES = "files"
TILE_STORAGE_SQLITE = "sqlite"
TILE_STORAGE_TYPES = [TILE_STORAGE_FILES, TILE_STORAGE_SQLITE]

# GTK GUI
PANGO_ON = '<span color="green">ON</span>'
PANGO_OFF = '<span color="red">OFF</span>'

# threads

# search
THREAD_POI_SEARCH = "modRanaPOISearch"
THREAD_ADDRESS_SEARCH = "modRanaAddressSearch"
THREAD_WIKIPEDIA_SEARCH_NOMINATIM = "modRanaWikipediaSearchNominatim"
THREAD_REVERSE_GEOCODING = "modRanaReverseGeocoding"
THREAD_LOCAL_SEARCH_GOOGLE = "modRanaLocalSearchGoogle"
THREAD_LOCAL_SEARCH_OSM_SCOUT = "modRanaLocalSearchOSMScoutServer"
# routing
THREAD_ROUTING_ONLINE_GOOGLE = "modRanaRoutingOnlineGoogle"
THREAD_ROUTING_OFFLINE_MONAV = "modRanaRoutingOfflineMonav"
THREAD_ROUTING_OFFLINE_OSM_SCOUT_SERVER = "modRanaRoutingOfflineOSMScoutServer"
# turn-by-turn navigation
THREAD_TBT_WORKER = "modRanaTurnByTurnWorker"
# location
THREAD_GPSD_CONSUMER = "modRanaGPSDConsumer"
# tile down-/loading
THREAD_TILE_DOWNLOAD_MANAGER = "modRanaTileDownloadManager"
THREAD_TILE_DOWNLOAD_WORKER = "modRanaTileDownloadWorker"
THREAD_TILE_STORAGE_LOADER = "modRanaTileStorageLoader"
# resource checking
THREAD_CONNECTIVITY_CHECK = "modRanaConnectivityCheck"
THREAD_LOCATION_CHECK = "modRanaCurrentPositionCheck"
# testing
THREAD_TESTING_PROVIDER = "modRanaTestingProvider"
# voice/TTS
THREAD_VOICE_WORKER = "modRanaVoiceWorker"

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
DEFAULT_AUTOMATIC_TILE_DOWNLOAD_QUEUE_SIZE = 100

# in-memory tile cache size
# * this controls how many tiles modRana keeps in memory
#   after downloading them of loading them from storage
# * the tiles are cached so they can be quickly used if
#   requested again, which is often needed by the GTK GUI
#   and should also help the Qt 5 GUI
DEFAULT_MEMORY_TILE_CACHE_SIZE = 150
# how many tiles to remove from cache when it gets full
DEFAULT_MEMORY_TILE_CACHE_TRIM_SIZE = 30

# sqlite tile database commit interval
# * lower interval - lower amount of tiles in flight and this
#   lower memory usage but more & less efficient IO (less batching)
# * longer interval - more tiles in flight, more memory usage but
#   IO happens less often in longer hopefully more efficient bursts
DEFAULT_SQLITE_TILE_DATABASE_COMMIT_INTERVAL = 5 # seconds

# device types
DEVICE_TYPE_DESKTOP = 1
DEVICE_TYPE_SMARTPHONE = 2
DEVICE_TYPE_TABLET = 3

# providers
ROUTING_PROVIDER_GOOGLE = "GoogleDirections"
ROUTING_PROVIDER_MONAV_SERVER = "MonavServer"
ROUTING_PROVIDER_MONAV_LIGHT = "MonavLight"
ROUTING_PROVIDER_ROUTINO = "Routino"
ROUTING_PROVIDER_OSM_SCOUT = "OSMScoutServer"

ROUTING_PROVIDER_NAMES = {
    ROUTING_PROVIDER_GOOGLE : "Google Directions",
    ROUTING_PROVIDER_MONAV_SERVER : "Monav server",
    ROUTING_PROVIDER_MONAV_LIGHT : "Monav Light",
    ROUTING_PROVIDER_ROUTINO : "Routino",
    ROUTING_PROVIDER_OSM_SCOUT : "OSM Scout Server"
}

# online routing providers
ONLINE_ROUTING_PROVIDERS = [
    ROUTING_PROVIDER_GOOGLE
]

# offline routing providers
OFFLINE_ROUTING_PROVIDERS = [
    ROUTING_PROVIDER_MONAV_SERVER,
    ROUTING_PROVIDER_MONAV_LIGHT,
    ROUTING_PROVIDER_ROUTINO,
    ROUTING_PROVIDER_OSM_SCOUT
]

# routing
ROUTE_DEFAULT_LANGUAGE = "en"
DEFAULT_ROUTING_PROVIDER = ROUTING_PROVIDER_GOOGLE

# Monav routing return codes
ROUTING_SUCCESS = 0
ROUTING_NO_DATA = 1 # failed to load routing data
ROUTING_LOAD_FAILED = 2 # failed to load routing data
ROUTING_LOOKUP_FAILED = 3 # failed to locate nearest way/edge
ROUTING_SOURCE_LOOKUP_FAILED = 4 # start or destination address not found
ROUTING_TARGET_LOOKUP_FAILED = 5 # start or destination address not found
ROUTING_WAYPOINT_LOOKUP_FAILED = 6 # start or destination address not found
ROUTING_ROUTE_FAILED = 7 # failed to compute route
ROUTING_ADDRESS_NOT_FOUND = 8 # start or destination address not found

ROUTING_FAILURE_MESSAGES = {
    ROUTING_NO_DATA : "No usable offline routing data found.",
    ROUTING_LOAD_FAILED : "Routing data could not be loaded.",
    ROUTING_LOOKUP_FAILED : "No way near start or destination.",
    ROUTING_SOURCE_LOOKUP_FAILED : "No way near route start.",
    ROUTING_TARGET_LOOKUP_FAILED : "No way near route destination.",
    ROUTING_WAYPOINT_LOOKUP_FAILED : "No way near one of the waypoints.",
    ROUTING_ADDRESS_NOT_FOUND : "Couldn't find start or destination address."
}

# route types
ROUTE_PEDESTRIAN = 1
ROUTE_BIKE = 2
ROUTE_CAR = 3

# navigation
DEFAULT_NAVIGATION_STEP_ICON = "flag"

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
