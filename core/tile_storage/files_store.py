from __future__ import with_statement
import os
import glob
import shutil
import re

from .base import BaseTileStore
from . import utils

import logging
log = logging.getLogger("tile_storage.files_store")

PARTIAL_TILE_FILE_SUFFIX = ".part"

def _get_toplevel_tile_folder_list(path):
    """Return a list of toplevel tile folders
       The toplevel tile folders correspond to the zoom level number.

    :param str path: path where to check for top level tile folders
    :returns: a list of top level tile folders
    :rtype: list
    """
    tile_folders = [folder for folder in os.listdir(path) if re.match("[0-9]+", folder)]
    return [folder for folder in tile_folders if os.path.isdir(os.path.join(path, folder))]


class FileBasedTileStore(BaseTileStore):

    @staticmethod
    def is_store(path):
        """We consider the path to be a files tile store if it is a folder
           that contains at least one top level tile folder.
           This basically means that at least one tile needs to be stored in it.

        :param str path: path to test
        :returns: True if the path leads to an existing folder, else False
        :rtype: bool
        """
        is_files_store = False
        if os.path.isdir(path):
            is_files_store = bool(_get_toplevel_tile_folder_list(path))
        return is_files_store

    def __init__(self, store_path, prevent_media_indexing = False):
        BaseTileStore.__init__(self, store_path, prevent_media_indexing=prevent_media_indexing)

        # make sure the folder for the file based tile store exists and is in a correct state,
        # such as that it contains a file that disables media indexing on platforms where this is needed
        utils.check_folder(self.store_path, prevent_media_indexing=prevent_media_indexing)

    def __str__(self):
        return "file based store @ %s" % self.store_path

    def __repr__(self):
        return str(self)

    def store_tile_data(self, lzxy, tile_data):
        """Store the given tile to a file"""
        # get the folder path
        file_path = self._get_tile_file_path(lzxy)
        partial_file_path = file_path + PARTIAL_TILE_FILE_SUFFIX
        (folder_path, tail) = os.path.split(file_path)
        if not os.path.exists(folder_path): # does it exist ?
            try:
                os.makedirs(folder_path) # create the folder
            except Exception:
                import sys
                e = sys.exc_info()[1]
                # errno 17 - folder already exists
                # this is most probably cased by another thread creating the folder between
                # the check & our os.makedirs() call
                # -> we can safely ignore it (as the the only thing we are now interested in,
                # is having a folder to store the tile in)
                if e.errno != 17:
                    log.exception("can't create folder %s for %s", folder_path, file_path)
        try:
            with open(partial_file_path, 'wb') as f:
                f.write(tile_data)
            os.rename(partial_file_path, file_path)
            # TODO: fsync the file (optionally ?)?
        except:
            log.exception("saving tile to file %s failed", file_path)
            try:
                if os.path.exists(partial_file_path):
                    os.remove(partial_file_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                log.exception("failed storage operation cleanup failed for %s", file_path)

    def get_tile(self, lzxy, fuzzy_matching=True):
        """Get tile data and timestamp corresponding to the given coordinate tuple from
           this file based tile store. The timestamp correspond to the time the tile has
           been last modified.

        :param tuple lzxy: layer, z, x, y coordinate tuple describing a single tile
                           (layer is actually not used and can be None)
        :param bool fuzzy_matching: if fuzzy tile matching should be used
        Fuzzy tile matching looks for any image files on the given coordinates
        in case an image file with extension given by the layer.type property is
        not found in the store.
        :returns: (tile data, timestamp) or None if tile is not found in the database
        :rtype: a (bytes, int) tuple or None
        """
        if fuzzy_matching:
            file_path = self._fuzzy_find_tile(lzxy)
        else:
            file_path = self._get_tile_file_path(lzxy)

        if file_path and os.path.isfile(file_path):
            try:
                tile_mtime = os.path.getmtime(file_path)
                with open(file_path, "rb") as f:
                    return f.read(), tile_mtime
            except:
                log.exception("tile file reading failed for: %s", file_path)
                return  None
        else:
            return None

    def tile_is_stored(self, lzxy, fuzzy_matching=True):
        """Report if the tile specified by the lzxy tuple is present
           in this file based tile store

        :param tuple lzxy: layer, z, x, y coordinate tuple describing a single tile
        :param bool fuzzy_matching: if fuzzy tile matching should be used
        Fuzzy tile matching looks for any image files on the given coordinates
        in case an image file with extension given by the layer.type property is
        not found in the store.
        :returns: True if tile is present in the store, else False
        :rtype: bool
        """
        if fuzzy_matching:
            file_path = self._fuzzy_find_tile(lzxy)
        else:
            file_path = self._get_tile_file_path(lzxy)
        if file_path and os.path.isfile(file_path):
            return True, os.path.getmtime(file_path)
        else:
            return False

    def _delete_empty_folders(self, z, x):
        # x-level folder
        x_path = os.path.join(self.store_path, z, x)
        if not os.listdir(x_path):
            try:
                try:
                    os.rmdir(x_path)
                except OSError:
                    # most probably caused by something being created in the folder
                    # since the check
                    pass
                # z-level folder
                z_path = os.path.join(self.store_path, z)
                if os.listdir(z_path):
                    try:
                        os.rmdir(z_path)
                    except OSError:
                        # most probably caused by something being created in the folder
                        # since the check
                        pass
            except:
                log.exception("empty folder cleanup failed for: %s", x_path)

    def delete_tile(self, lzxy):
        # TODO: delete empty folders ?
        tile_path = self._get_tile_file_path(lzxy)
        try:
            if os.path.isfile(tile_path):
                os.remove(tile_path)
                # remove any empty folders that might have been
                # left after the deleted tile file
                self._delete_empty_folders(lzxy[1], lzxy[2])
            else:
                log.error("can't delete file - path is not a file: %s", tile_path)
        except:
            log.exception("removing of tile at %s failed", tile_path)

    def clear(self):
        """Delete the tile folders and files corresponding to this store from permanent storage
        This basically means we delete all folders that have just number in name
        (1, 2, 23, 1337 but not aa1, b23, .git, etc.) as they are the the toplevel (z coordinates)
        tile storage folders.
        We don't just remove the toplevel folder as for example in modRana a single folder
        is used to store both tiles and sqlite tile storage database and we would
        also remove any databases if we just removed the toplevel folder.
        """
        try:
            for folder in _get_toplevel_tile_folder_list(self.store_path):
                folder_path = os.path.join(self.store_path, folder)
                shutil.rmtree(folder_path)
        except:
            log.exception("clearing of files tile store at path %s failed", self.store_path)

    def _get_tile_file_path(self, lzxy):
        """Return full filesystem path to the tile file corresponding to the coordinates
         given by the lzxy tuple.

         :param tuple lzxy: tile coordinates
         :returns: full filesystem path to the tile
         :rtype: str
         """
        return os.path.join(
            self.store_path,
            str(lzxy[1]),
            str(lzxy[2]),
            "%d.%s" % (lzxy[3], lzxy[0].type)
        )

    def _fuzzy_find_tile(self, lzxy):
        """Try to find a tile image file for the given coordinates

        :returns: path to a suitable tile or None if no can be found
        :rtype: str or None
        """
        # first check if the primary tile path exists
        tile_path = self._get_tile_file_path(lzxy)
        # check if the primary file path exists and also if it actually
        # is an image file
        if os.path.exists(tile_path):
            try:
                with open(tile_path, "rb") as f:
                    if utils.is_an_image(f.read(32)):
                        return tile_path
                    else:
                        log.warning("%s is not an image", tile_path)
            except Exception:
                log.exception("checking if primary tile file is an image failed for %s", lzxy)

        # look also for other supported image formats
        alternative_tile_path = None
        # TODO: might be good to investigate the performance impact,
        #       just to be sure :P

        # replace the extension with a * so that the path can be used
        # as wildcard in glob
        wildcard_tile_path = "%s.*" % os.path.splitext(tile_path)[0]
        # iterate over potential paths returned by the glob iterator
        for path in glob.iglob(wildcard_tile_path):
            # go over the paths and check if they point to an image files
            with open(path, "rb") as f:
                if utils.is_an_image(f.read(32)):
                    # once an image file is found, break & returns its path
                    alternative_tile_path = path
                    break
                else:
                    log.warning("%s is not an image", tile_path)
        return alternative_tile_path