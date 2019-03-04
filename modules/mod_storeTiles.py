from __future__ import with_statement # for python 2.5
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Store tiles in a single file.
# This is done to avoid the fs cluster issues.
# Initially, sqlite will be used for storage.
#----------------------------------------------------------------------------
# Copyright 2007, Oliver White
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

import logging
log = logging.getLogger("mod.storeTiles")

try:
    import sqlite3
except Exception:
    log.exception("sqlite import failed")

import os
import time
from collections import defaultdict
from threading import RLock

try:  # Python 2.7+
    from collections import OrderedDict as OrderedDict
except ImportError:
    from core.backports.odict import odict as OrderedDict  # Python <2.7

from core import constants
from core import utils
from core.tile_storage.files_store import FileBasedTileStore
from core.tile_storage.sqlite_store import SqliteTileStore

def getModule(*args, **kwargs):
    return StoreTiles(*args, **kwargs)

class FlexibleDefaultDict(defaultdict):
    def __init__(self, factory):
        defaultdict.__init__(self)
        self.factory = factory
    def __missing__(self, key):
        self[key] = self.factory(key)
        return self[key]


class StoreTiles(RanaModule):
    """Single-file-fs tile storage"""
    #TODO: maybe run this in separate thread ?

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)

        self._tile_storage_management_lock = RLock()
        # this variable holds the currently selected primary store type
        # - this store type will be used to store all downloaded tiles
        # - this store type will be tried first when looking for tiles
        #   in local storage, before checking other store types if the
        #   tile is not found
        # - we have a watch on the store type key, so this variable will
        #   be automatically updated if store type changes at runtime
        self._primary_tile_storage_type = constants.DEFAULT_TILE_STORAGE_TYPE
        self._stores = FlexibleDefaultDict(factory=self._get_existing_stores_for_layer)

        self._prevent_media_indexing = self.dmod.device_id == "android"

        # the tile loading debug log function is no-op by default, but can be
        # redirected to the normal debug log by setting the "tileLoadingDebug"
        # key to True
        self._llog = self._no_op
        self.modrana.watch('tileLoadingDebug', self._tile_loading_debug_changed_cb, runNow=True)
        self.modrana.watch('tileStorageType', self._primary_tile_storage_type_changed_cb, runNow=True)
        # device modules are loaded and initialized and configs are parsed before "normal"
        # modRana modules are initialized, so we can cache the map folder path in init

    def _get_existing_stores_for_layer(self, layer):
        """Check for any existing stores for the given layer in persistent storage
           and return a dictionary with the found stores under file storage type keys.
        """
        start = time.clock()
        self._llog("looking for existing stores for layer %s" % layer)
        layer_folder_path = os.path.join(self.modrana.paths.map_folder_path, layer.folder_name)
        store_tuples = []
        # check if the path contains a file based tile store
        if FileBasedTileStore.is_store(layer_folder_path):
            self._llog("file based store has been found for layer %s" % layer)
            # we need to prevent tiles from being indexed to the gallery
            # - this basically dumps a .nomedia file to the root of the
            #   file based tile store folder
            store_tuple = (constants.TILE_STORAGE_FILES, FileBasedTileStore(
                layer_folder_path, prevent_media_indexing=self._prevent_media_indexing
            ))
            store_tuples.append(store_tuple)
        # check if the path contains a sqlite tile store
        if SqliteTileStore.is_store(layer_folder_path):
            self._llog("sqlite tile store has been found for layer %s" % layer)
            store_tuple = (constants.TILE_STORAGE_SQLITE, SqliteTileStore(layer_folder_path))
            store_tuples.append(store_tuple)

        self._llog("%d existing stores have been found for layer %s" % (len(store_tuples), layer), start)
        # sort the tuples so that the primary tile storage type (if any) is first
        store_tuples.sort(key=self._sort_store_tuples)
        return OrderedDict(store_tuples)

    def _get_stores_for_reading(self, layer):
        """Get an iterable of stores for the given layer
           - store corresponding to primary storage type is always first (if any)
           - there might not by any stores (eq. no tiles) for the given layer
        """
        with self._tile_storage_management_lock:
            return self._stores[layer].values()

    def _get_store_for_writing(self, layer):
        """Get a store for writing tiles corresponding to the given layer
           and current primary tile storage type.
        """
        with self._tile_storage_management_lock:
            store = self._stores[layer].get(self._primary_tile_storage_type)
            if store is None:
                start = time.clock()
                self._llog("store type %s not found for layer %s" % (self._primary_tile_storage_type, layer))
                layer_folder_path = os.path.join(self.modrana.paths.map_folder_path, layer.folder_name)
                if self._primary_tile_storage_type == constants.TILE_STORAGE_FILES:
                    store_type = constants.TILE_STORAGE_FILES
                    store = FileBasedTileStore(
                        layer_folder_path, prevent_media_indexing=self._prevent_media_indexing
                    )
                    self._llog("adding file based store for layer %s" % layer)
                else:  # sqlite tile store
                    store_type = constants.TILE_STORAGE_SQLITE
                    store = SqliteTileStore(layer_folder_path)
                    self._llog("adding file based store for layer %s" % layer)
                # add the store to the stores dict while keeping the primary-storage-type first ordering
                self._add_store_for_layer(layer, (store_type, store))
                self._llog("added store type %s for layer %s" % (self._primary_tile_storage_type, layer), start)
            return store

    def _sort_store_tuples(self, key):
        # stores corresponding to the current primary stile storage type should go first
        if key[0] == self._primary_tile_storage_type:
            return 0
        else:
            return 1

    def _sort_layer_odict(self, layer):
        """Sort the ordered dict for the given layer according to
           current primary tile storage type.
        """
        with self._tile_storage_management_lock:
            store_tuples = list(self._stores[layer].items())
            store_tuples.sort(key=self._sort_store_tuples)
            self._stores[layer] = OrderedDict(store_tuples)

    def _add_store_for_layer(self, layer, store_tuple):
        """Add a store for the given layer while keeping the ordering
           according to the current primary tile storage type."""
        with self._tile_storage_management_lock:
            store_tuples = list(self._stores[layer].items())
            store_tuples.append(store_tuple)
            store_tuples.sort(key=self._sort_store_tuples)
            self._stores[layer] = OrderedDict(store_tuples)

    def _primary_tile_storage_type_changed_cb(self, key, oldValue, newValue):
        start = time.clock()
        # primary tile storage type has been changed, update internal variables accordingly
        with self._tile_storage_management_lock:
            self._llog("primary tile storage type changed to: %s" % newValue)
            if newValue not in constants.TILE_STORAGE_TYPES:
                log.error("invalid tile storage type was requested and will be ignored: %s", newValue)
                return
            self._primary_tile_storage_type = newValue
            # reorder the ordered dicts storing already initialized tile stores
            # so that the primary tile storage method is first
            self._llog("resorting ordered dicts for the new primary storage type")
            for layer in self._stores.keys():
                self._sort_layer_odict(layer)
            self._llog("ordered dicts resorted", start)

    def _tile_loading_debug_changed_cb(self, key, oldValue, newValue):
        if newValue:
            self.log.debug("tile loading debug messages state: enabled")
            self._llog = self._tile_loading_log
        else:
            self.log.debug("tile loading debug messages state: disabled")
            self._llog = self._no_op

    def _tile_loading_log(self, message, start_timestamp=None):
        if start_timestamp is not None:
            message = "%s (%s)" % (message, utils.get_elapsed_time_string(start_timestamp))
        self.log.debug(message)

    def _no_op(self, *args):
        pass

    def get_tile_data(self, lzxy):
        start = time.clock()
        layer = lzxy[0]
        self._llog("tile requested: %s" % str(lzxy))
        with self._tile_storage_management_lock:
            stores = self._get_stores_for_reading(layer)
            self._llog("tile %s got stores: %s" % (str(lzxy), list(stores)))

        for store in stores:
            tile_tuple = store.get_tile(lzxy)
            if tile_tuple is not None:
                self._llog("tile %s found in %s" % (str(lzxy), store))
                tile_data, timestamp = tile_tuple
                if layer.timeout is not None:
                    # layer.timeout is in hours, convert to seconds
                    layer_timeout = layer.timeout*60*60
                    dt = time.time() - layer_timeout
                    self._llog("timeout set for layer %s: %fs (expired at %d), "
                               "tile timestamp: %d" % (layer.label,
                                                       layer_timeout,
                                                       dt,
                                                       timestamp))
                    if timestamp < dt:
                        self.log.debug("not loading timed-out tile: %s" % str(lzxy))
                        return None # pretend the tile is not stored
                    else:  # still fresh enough
                        self._llog("tile is still fresh enough: %s" % str(lzxy), start)
                        return tile_data
                else:  # the tile is always fresh
                    self._llog("returning tile data for: %s" % str(lzxy), start)
                    return tile_data
        # nothing found in any store (or no stores)
        self._llog("tile not found: %s" % str(lzxy), start)
        return None

    def tile_is_stored(self, lzxy):
        start = time.clock()
        self._llog("do we have tile: %s ?" % str(lzxy))
        layer = lzxy[0]
        with self._tile_storage_management_lock:
            stores = self._get_stores_for_reading(layer)
        for store in stores:
            tile_tuple = store.tile_is_stored(lzxy)
            if tile_tuple is not False:
                self._llog("we have tile %s in %s" % (str(lzxy), store))
                _true, timestamp = tile_tuple
                self._llog("we have tile: %s with timestamp %s" % (str(lzxy), timestamp))
                if layer.timeout is not None:
                    # stored timeout is in hours, convert to seconds
                    layer_timeout = layer.timeout*60*60
                    dt = time.time() - layer_timeout
                    self._llog("timeout set for layer %s: %fs (expired at %d), "
                               "tile timestamp: %d" % (layer.label,
                                                       layer_timeout,
                                                       dt,
                                                       timestamp))
                    if timestamp < dt:
                        self.log.debug("reporting we don't have timed-out tile: %s" % str(lzxy), start)
                        return False # pretend the tile is not stored
                    else:  # still fresh enough
                        self._llog("tile is still fresh enough to report as stored: %s" % str(lzxy), start)
                        return True
                else:  # the tile is always fresh
                    self._llog("we have tile: %s" % str(lzxy), start)
                    return True
        # nothing found in any store (or no stores)
        self._llog("we have not found tile: %s" % str(lzxy), start)
        return False

    def store_tile_data(self, lzxy, tile_data):
        start = time.clock()
        self._llog("store tile data for: %s" % str(lzxy))
        store = self._get_store_for_writing(lzxy[0])
        self._llog("store tile data for: %s into %s" % (str(lzxy), store))
        store.store_tile_data(lzxy, tile_data)
        self._llog("stored tile data for: %s" % str(lzxy), start)

    def shutdown(self):
        start = time.clock()
        # close all stores
        self.log.debug("closing tile stores")
        layer_count = 0
        store_count = 0
        with self._tile_storage_management_lock:
            for store_odicts in self._stores.values():
                for store in store_odicts.values():
                    store.close()
                    store_count+=1
            layer_count+=1
        self.log.debug("closed all tile stores (for %d layers, %d stores in total in %s)"
                       % (layer_count, store_count, utils.get_elapsed_time_string(start)))
