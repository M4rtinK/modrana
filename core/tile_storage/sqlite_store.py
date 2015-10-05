# A tile store that is using SQLite as a storage backend
#
# This has a number of benefits:
# * all the tiles are stored in just a couple files
# - usually just 2 (1 one lookup and 1 storage database)
# - additional storage database is added for every 3.7 GB of tiles by default
# * improves performance on filesystems that fail to handle many small file efficiently (FAT32)
# * makes occupied space checking instant
#   (it can take a lot of time to compute size of tile stored as files in folders)
# * hides the tiles from stupid multimedia indexers
#
# How does it work ?
# The tiles are stored in a sqlite database as blobs. There are two types of database files,
# lookup.sqlite and store.sqlite.
# The lookup file has the name of the storage database where the requested tile data is stored.
# The store file has the actual tile data.
# Multiple stores should be numbered in ascending order, starting from 0:
#
# store.sqlite.0
# store.sqlite.1
# store.sqlite.2
# etc.
#
# The storage database looks schema like this:
#
# table tiles (z integer, x integer, y integer, store_filename string, extension varchar(10), unix_epoch_timestamp integer, primary key (z, x, y, extension))
#
# The storage databases schema look like this:
#
# table tiles (z integer, x integer, y integer, tile blob, extension varchar(10), unix_epoch_timestamp integer, primary key (z, x, y, extension))
#
# The only difference in the structure is that the lookup databases only stores the name of the store
# for given coordinates and the store database stores the actual blob.
# Both also have a table called version which has an integer column called v.
# There is a single 1 inserted, which indicates the current version of the table.
#
# When looking for a tile in the database, the lookup database is checked first and if the coordinates
# are found the corresponding storage database is queried for the actual data.

from __future__ import with_statement

import os
import sqlite3
import glob
import time
from threading import RLock

import logging
log = logging.getLogger("tile_storage.sqlite_store")

from .base import BaseTileStore
from .constants import GIBI_BYTE
from . import utils

# the storage database files can be only this big to avoid
# maximum file size limitations on FAT32 and possibly elsewhere
MAX_STORAGE_DB_FILE_SIZE = 3.7  # in Gibi Bytes
SQLITE_QUEUE_SIZE = 50
SQLITE_TILE_STORAGE_FORMAT_VERSION = 1
LOOKUP_DB_NAME = "lookup.sqlite"
STORE_DB_NAME_PREFIX = "store.sqlite."

def connect_to_db(path_to_database):
    """Setting check_same_thread to False fixes a Sqlite exception
    that happens when a thread tries to access a database read connection
    that was created in a different thread. All write connections are "owned"
    by the storage thread so they don't have these issues.
    According to shreds of information available on the Internet &
    GitHub search revealing massive usage of check_same_thread=False,
    we are also using this flag to fix the issues.
    Possible alternative solutions:
    * per thread connections read connections
    * replacing the connection if it was created in a different thread
    * having a thread own the connection and handling read operations
      asynchronously
    In case that check_same_thread does not work somewhere or that is
    found that it has some serious disadvantages, some of these alternative
    solutions could be used.

    :param str path_to_database: path to the database
    :returns: Sqlite database connection
    """
    return sqlite3.connect(path_to_database, check_same_thread=False)

class SqliteTileStore(BaseTileStore):

    @staticmethod
    def is_store(path):
        """We consider the path to be a sqlite tile store if it:
           - if a folder
           - contains the lookup database and at least one storage database

        :param str path: path to test
        :returns: True if the path leads to sqlite tile store, else False
        :rtype: bool
        """
        is_store = False
        if os.path.isdir(path):
            lookup_db_path = os.path.join(path, LOOKUP_DB_NAME)
            store_db_glob = os.path.join(path, STORE_DB_NAME_PREFIX + "*")
            if os.path.isfile(lookup_db_path) and glob.glob(store_db_glob):
                # we have found the lookup database and at least one store,
                # so this is most probably a sqlite tile database
                is_store = True
        return is_store

    def __init__(self, store_path, prevent_media_indexing = False):
        BaseTileStore.__init__(self, store_path, prevent_media_indexing=prevent_media_indexing)

        # SQLite tends to blow up with the infamous "sqlite3.OperationalError: database is locked"
        # if the database is accessed from multiple threads an/or processes at the same time.
        # Interestingly this can happen if only reading is going on - if the RO transaction
        # is taking too long, attempts of writing will start getting the "database is locked"
        # error. And of course a single write transaction is enough to basically block the
        # database indefinitely.
        #
        # tl;dr: serialize W & RO access to the database to prevent random lockups
        #
        # We should try to compensate for this by batching read and write requests,
        # which should ot be that difficult as for example modRana often needs to fetch a full
        # screen of tiles and we can quite easily cache write requests and submit them in batch.
        self._db_lock = RLock()
        # to avoid possible race conditions we needs to mutually exclude operations concerning
        # storage database free space checking and the related adding of new stores
        self._storage_db_management_lock = RLock()

        # make sure the folder containing the sqlite tile databases exists
        utils.check_folder(self.store_path, prevent_media_indexing=prevent_media_indexing)

        # there is always only one lookup database per store that stores only tile coordinates
        # and name of the storage database holding the tile data
        # (hitting the 4 GB file size limit while storing only tile coordinates
        #  should hopefully never happen)
        self._lookup_db_path = os.path.join(self.store_path, LOOKUP_DB_NAME)
        self._lookup_db_connection = self._get_lookup_db_connection()
        # there is always one or more storage databases that hold the actual tile data
        # - once a storage database hits the max file size limit (actually se to 3.7 GB just in case)
        #   a new storage database file is added
        self._storage_databases = self._get_storage_db_connections()

        # these two variables point to a storage database that currently has enough free space
        # for storing of new tiles, once the storage database hits the max file size limit,
        # we try to find one that has enough free space or add a new one if all existing
        # storage databases are full
        # - we just connect the storage with the lowest number at startup and let the usable
        #   storage database finding logic do its job in case  it is too full
        sorted_store_names = list(sorted(self._storage_databases.keys()))
        store_name = sorted_store_names[0]
        store_connection = self._storage_databases[store_name]
        self._new_tiles_store_name = store_name
        self._new_tiles_store_connection = store_connection

    def __str__(self):
        return "sqlite store @ %s" % self.store_path

    def __repr__(self):
        return str(self)

    def _get_lookup_db_connection(self):
        """Initialize the lookup database
           If the database already exist just connect to it, otherwise create it and
           in both cases return the database connection.
        """
        log.debug("initializing lookup db: %s" % self._lookup_db_path)
        if os.path.exists(self._lookup_db_path): #does the lookup db exist ?
            connection = connect_to_db(self._lookup_db_path) # connect to the lookup db
        else:  # create new lookup database
            with self._db_lock:
                connection = connect_to_db(self._lookup_db_path)
                cursor = connection.cursor()
                log.info("sqlite tiles: creating lookup table")
                cursor.execute(
                    "create table tiles (z integer, x integer, y integer, store_filename string, extension varchar(10), unix_epoch_timestamp integer, primary key (z, x, y, extension))")
                cursor.execute("create table version (v integer)")
                cursor.execute("insert into version values (?)", (SQLITE_TILE_STORAGE_FORMAT_VERSION,))
                connection.commit()
        return connection

    def _get_storage_db_connections(self):
        """Connect to all existing storage databases and return a dictionary of the resulting connections
           - if no storage databases exist, create the first (store.sqlite.0) storage database
        """
        connections = {}
        existing_stores = self._list_store_files()
        if existing_stores:
            for store_path in existing_stores:
                store_name = os.path.basename(store_path)
                connections[store_name] = connect_to_db(store_path)
        else:  # no stores yet, create the first one
            store_name, store_connection = self._add_store()
            connections = {store_name : store_connection}
        return connections

    def _add_store(self):
        """Add a new store
           - find an ascending numbered name and create the db file with the corresponding tables
        """
        new_highest_number = 0
        storeList = self._list_store_files()
        if storeList:
            number_candidate_list = map(lambda x: x.split('store.sqlite.')[1], storeList)
            integer_list = []
            for number_candidate in number_candidate_list:
                try:
                    integer_list.append(int(number_candidate))
                except ValueError:
                    # there was probably something like store.sqlite.abc,
                    # eq. something that fails to parse to an integer
                    pass
            if integer_list:
                highest_number = sorted(number_candidate_list)[-1]
                new_highest_number = highest_number + 1

        store_name = "store.sqlite.%d" % new_highest_number
        return store_name, self._create_new_store(os.path.join(self.store_path, store_name))

    def _create_new_store(self, path):
        """Create a new store database at the given file path

        :param str path: path to the file path where the database should be created
        """
        log.debug("creating a new storage database in %s" % path)
        connection = connect_to_db(path)
        cursor = connection.cursor()
        cursor.execute(
            "create table tiles (z integer, x integer, y integer, tile blob, extension varchar(10), unix_epoch_timestamp integer, primary key (z, x, y, extension))")
        cursor.execute("create table version (v integer)")
        cursor.execute("insert into version values (?)", (SQLITE_TILE_STORAGE_FORMAT_VERSION,))
        connection.commit()
        return connection

    def _get_name_connection_to_available_store(self, data_size):
        """Return a path to a store that can be used to store a tile specified by its size"""
        with self._storage_db_management_lock:
            # first check if the last-known-good storage database has enough space to satisfy the request
            if self._will_it_fit_in(self._new_tiles_store_name, data_size):
                return self._new_tiles_store_name, self._new_tiles_store_connection
            else:  # try if the request will fit to some other store we are already connected to
                for store_name, store_connection in self._storage_databases.items():
                    if self._will_it_fit_in(store_name, data_size):
                        # this store can handle the given storage request, so set it as able to
                        # handle further tile storage requests
                        self._new_tiles_store_name = store_name
                        self._new_tiles_store_connection = store_connection
                        # and return the connection to caller
                        return store_name, store_connection

                # if we got there it means we have not found space for the request in any existing
                # storage database file, so we need to create a new one
                new_store_name, new_store_connection = self._add_store()
                # again cache the connection to the store
                self._new_tiles_store_name = new_store_name
                self._new_tiles_store_connection = new_store_connection
                return new_store_name, new_store_connection

    def _list_store_files(self):
        """Return a list of available storage database files

        :returns: list of found storage database paths
        :rtype: list of strings
        """
        return glob.glob(os.path.join(self.store_path, "%s*" % STORE_DB_NAME_PREFIX))

    def _will_it_fit_in(self, storage_database_name, size_in_bytes):
        """Report if the given amount of data in bytes will still fit into the currently used
           storage database
           True  = probably fits in the database
           False = would not fit in
           NOTE: there is some database overhead, so this is not 100% reliable
                 always set the limit with a slight margin

        :param str storage_database_name: path to a storage database to check
        :param int size_in_bytes: the size to check
        :returns: True if size will fit, False if not
        :rtype: bool
        """
        maximum_size_in_bytes = MAX_STORAGE_DB_FILE_SIZE * GIBI_BYTE
        storage_database_path = os.path.join(self.store_path, storage_database_name)
        store_size_in_bytes = os.path.getsize(storage_database_path)
        if (store_size_in_bytes + size_in_bytes) <= maximum_size_in_bytes:
            return True  # the database will (probably) still smaller than the limit
        else:
            return False  # the database will be larger

    def store_tile_data(self, lzxy, tile_data):
        with self._db_lock:
            layer, z, x, y = lzxy
            extension = layer.type
            lookup_connection = self._lookup_db_connection
            lookup_cursor = lookup_connection.cursor()
            data_size = len(tile_data)
            integer_timestamp = int(time.time())
            tile_exists = lookup_cursor.execute(
                "select store_filename from tiles where z=? and x=? and y=?",
                (z, x, y)).fetchone()
            if tile_exists:  # tile is already in the database, update it
                # check if the new tile will fit to the storage database where the tile currently is
                # (we count as we would add the tile to the database, not replace it du to
                # database file size uncertainties caused by metadata updates, etc.)
                store_name = tile_exists[0]
                if self._will_it_fit_in(store_name, data_size):
                    # update the tile data and its timestamp in place
                    store_connection = self._storage_databases[store_name]
                    store_cursor = store_connection.cursor()
                    # update the storage database
                    su_query = "insert or replace into tiles (z, x, y, tile, extension, unix_epoch_timestamp) values (?, ?, ?, ?, ?, ?)"
                    # use "insert or replace" in case that the storage database is missing the tile for some reason
                    # - this should never happen as long as the database is properly managed, but better be safe than sorry
                    store_cursor.execute(su_query, [z, x, y, sqlite3.Binary(tile_data), extension, integer_timestamp])
                    store_connection.commit()
                    # update the extension and timestamp in the lookup database
                    lu_query = "update tiles set extension=?, unix_epoch_timestamp=? where z=? and x=? and y=?"
                    lookup_cursor.execute(lu_query, [extension, integer_timestamp, z, x, y])
                    lookup_connection.commit()
                else:
                    # remove the tile from the current storage database file
                    old_store_connection = self._storage_databases[store_name]
                    old_store_cursor = old_store_connection.cursor()
                    old_store_cursor.execute("delete from tiles where z=? and x=? and y=?", (z, x, y))
                    old_store_connection.commit()
                    # find a suitable storage database file
                    new_store_name, new_store_connection = self._get_name_connection_to_available_store(data_size)
                    # store the tile to it
                    store_query = "insert or replace into tiles (z, x, y, tile, extension, unix_epoch_timestamp) values (?, ?, ?, ?, ?, ?)"
                    # we use "insert or replace" in case there already is an unexpected leftover tile in the store for the coordinates
                    # - this should never happen as long as the database is properly managed, but better be safe than sorry
                    store_cursor = new_store_connection.cursor()
                    store_cursor.execute(store_query, [z, x, y, sqlite3.Binary(tile_data), extension, integer_timestamp])
                    new_store_connection.commit()
                    # update the store path, extension and timestamp in the lookup database
                    lu_query = "update tiles set store_filename=?, extension=?, unix_epoch_timestamp=? where where z=? and x=? and y=?"
                    lookup_cursor.execute(lu_query, [new_store_name, extension, integer_timestamp, z, x, y])
                    lookup_connection.commit()

            else:   # tile is not yet in the database, so just store it
                # get a store that can store this tile
                store_name, store_connection = self._get_name_connection_to_available_store(data_size)
                # write in the lookup db
                lookup_query = "insert into tiles (z, x, y, store_filename, extension, unix_epoch_timestamp) values (?, ?, ?, ?, ?, ?)"
                lookup_cursor = lookup_connection.cursor()
                lookup_cursor.execute(lookup_query, [z, x, y, store_name, extension, integer_timestamp])
                lookup_connection.commit()
                # write in the store
                store_query = "insert into tiles (z, x, y, tile, extension, unix_epoch_timestamp) values (?, ?, ?, ?, ?, ?)"
                store_cursor = store_connection.cursor()
                store_cursor.execute(store_query, [z, x, y, sqlite3.Binary(tile_data), extension, integer_timestamp])
                store_connection.commit()

    def get_tile(self, lzxy):
        """Get tile data and timestamp corresponding to the given coordinate tuple from the database.
           The timestamp correspond to the time the tile has been last modified.

        :param tuple lzxy: layer, z, x, y coordinate tuple describing a single tile
                           (layer is actually not used and can be None)
        :returns: (tile data, timestamp) or None if tile is not found in the database
        :rtype: a (bytes, int) tuple or None
        """
        _layer, z, x, y = lzxy
        with self._db_lock:
            lookup_connection = self._lookup_db_connection
            lookup_cursor = lookup_connection.cursor()
            lookup_result = lookup_cursor.execute(
                "select store_filename, unix_epoch_timestamp from tiles where z=? and x=? and y=?",
                (z, x, y)).fetchone()
            if lookup_result:  # the tile was found in the lookup db
                # now search for in the specified store
                store_name = lookup_result[0]
                store_connection = self._storage_databases.get(store_name)
                if store_connection is None:
                    log.warning("store %s/%s is mentioned in lookup db for %s/%s/%s but does not exist",
                                self.store_path, store_name, z, x, y)
                    return None
                store_cursor = store_connection.cursor()
                # as the x,y & z are used as the primary key, all rows need to have a unique
                # x, y & z combination and thus there can be only one result for a select
                # over x, y & z
                result = store_cursor.execute(
                    "select tile, unix_epoch_timestamp from tiles where z=? and x=? and y=?",
                    (z, x, y)).fetchone()
                if result:
                    if not utils.is_an_image(result[0]):
                        log.warning("%s,%s,%s in %s/%s is probably not an image", x, y, z, self.store_path, store_name)
                    return result
                else:
                    log.warning("%s,%s,%s is mentioned in lookup db but missing from store %s/%s", x, y, z, self.store_path, store_name)
            else:  # the tile was not found in the lookup database
                return None

    def delete_tile(self, lzxy):
        """Try to delete tile corresponding to the lzxy coordinate tuple from the database

        :param tuple lzxy: layer, z, x, y coordinate tuple describing a single tile
                           (layer is actually not used and can be None)
        """
        with self._db_lock:
            _layer, z, x, y = lzxy
            lookup_connection = self._lookup_db_connection
            lookup_cursor = lookup_connection.cursor()
            store_name = lookup_cursor.execute(
                "select store_filename from tiles where z=? and x=? and y=?", (z, x, y)
            ).fetchone()[0]
            if store_name:
                store_connection = self._storage_databases[store_name]
                store_cursor = store_connection.cursor()
                store_cursor.execute("delete from tiles where z=? and x=? and y=?", (z, x, y))
                store_connection.commit()
            lookup_cursor.execute("delete from tiles where z=? and x=? and y=?", (z, x, y))
            lookup_connection.commit()

    def tile_is_stored(self, lzxy):
        """Report if a tile specified by the lzxy tuple is stored in the database

        NOTE: We only check in the lookup database, not in the storage databases and we also
              don't verify if the tile extension is the same one as specified by the layer object
              of the lzxy tuple.

        :param tuple lzxy: layer, z, x, y coordinate tuple describing a single tile
                           (layer is actually not used and can be None)
        :returns: True if tile is stored in the database, else False
        :rtype: bool
        """
        _layer, z, x, y = lzxy
        lookup_connection = self._lookup_db_connection
        lookup_cursor = lookup_connection.cursor()
        query = "select store_filename, unix_epoch_timestamp from tiles where z=? and x=? and y=?"
        lookupResult = lookup_cursor.execute(query, (z, x, y)).fetchone()
        if lookupResult:
            return True, lookupResult[1]  # the tile is in the database
        else:
            return False # the tile is not in the database

    def close(self):
        """Close all database connections"""
        with self._db_lock:
            self._lookup_db_connection.close()
            for connection in self._storage_databases.values():
                connection.close()

    def clear(self):
        """Delete all database files belonging to this SQLite store"""
        with self._db_lock:
            # make sure the connections are closed before we remove
            # the data bases under them
            self.close()
            with self._storage_db_management_lock:
                # delete the lookup database
                os.remove(self._lookup_db_path)
                self._lookup_db_path = None
                self._lookup_db_connection = None
                # delete the storage databases
                for db_name in self._storage_databases.keys():
                    os.remove(os.path.join(self.store_path, db_name))
                self._storage_databases = {}
                # TODO: the database should be able to handle writes after clear
