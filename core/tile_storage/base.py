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

    def _check_folder(self, folder_path):
        """ Check if the top level map folder for the store exists and create it if it doesn't.
        Also does platform specific tweaks like creating a .nomedia file in the
        map folder on Android to prevent tile images from being indexed into the
        Android gallery.
        """

        if os.path.exists(folder_path):
            if not os.path.isdir(folder_path):
                # path exists but is not a directory
                log.critical("can't create tile storage folder: path exists but is not a directory: %s", folder_path)
        else:  # path does not exist, create it
            try:
                log.info("creating tile storage folder in: %s", folder_path)
                os.makedirs(folder_path)
            except Exception:
                log.exception("tile storage folder creation failed for path: %s", folder_path)

        if self._prevent_media_indexing:
            nomedia_file_path = os.path.join(folder_path, ".nomedia")
            if os.path.exists(nomedia_file_path):
                if not os.path.isfile(nomedia_file_path):
                    log.warning(".nomedia in the map data folder is not a file %s", nomedia_file_path)
            # create the .nomedia file to prevent indexing of tile images
            # - this should work at least on Android
            else :
                log.info("creating a .nomedia file in: %s", folder_path)
                try:
                    open(nomedia_file_path, "w").close()
                except Exception:
                    log.exception(".nomedia file creation failed in: %s", nomedia_file_path)