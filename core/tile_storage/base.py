# Base classes for the Tile Storage module

import os

import logging
log = logging.getLogger("tile_storage.base")

class BaseTileStore(object):
    """An abstract class defining the tile store API"""

    @staticmethod
    def is_store(path):
        """Report if given path is a tile store

        :param str path: path to test
        :returns: True if the path leads to a tile store, else False
        :rtype: bool
        """
        pass

    def __init__(self, store_path, prevent_media_indexing = False):
        self._prevent_media_indexing = prevent_media_indexing
        self._store_path = store_path

    @property
    def store_path(self):
        return self._store_path

    def store_tile_data(self, lzxy, tile_data):
        pass

    def get_tile(self, lzxy):
        pass

    def tile_is_stored(self, lzxy):
        pass

    def delete_tile(self, lzxy):
        pass

    def clear(self):
        """Clear the store from permanent storage"""
        pass

    def flush(self):
        """Flush any data "in flight" (if any) to permanent storage"""
        pass

    def close(self):
        """Close the tile store to any further writing and reading"""