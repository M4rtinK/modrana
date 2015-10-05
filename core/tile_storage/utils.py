"""Various tile handling utility functions"""
import six
from six import b
import sys
import os
import logging

from .tile_types import ID_TO_CLASS_MAP

log = logging.getLogger("tile_storage.utils")

PYTHON3 = sys.version_info[0] > 2

def is_an_image(tile_data):
    """test if the string contains an image
    by reading its magic number"""

    if PYTHON3: # in Python 3 we directly get bytes
        h = tile_data
    else: # in Python <3 we get a string
        # create a file-like object
        f = six.moves.StringIO(tile_data)
        # read the header from it
        h = f.read(32)
        # cleanup
        f.close()

    # NOTE: magic numbers taken from imghdr source code

    # as most tiles are PNGs, check for PNG first
    if h[:8] == b("\211PNG\r\n\032\n"):
        return "png"
    elif h[6:10] in (b('JFIF'), b('Exif')): # JPEG in JFIF or Exif format
        return "jpg"
    elif h[:6] in (b('GIF87a'), b('GIF89a')): # GIF ('87 and '89 variants)
        return "gif"
    elif h[:2] in (b('MM'), b('II'), b('BM')): # tiff or BMP
        return "bmp"
    else: # probably not an image file
        return False

def get_tile_data_type(tile_data):
    return ID_TO_CLASS_MAP.get(is_an_image(tile_data), None)

def check_folder(folder_path, prevent_media_indexing=False):
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

    if prevent_media_indexing:
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
