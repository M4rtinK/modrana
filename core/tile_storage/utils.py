"""Various tile handling utility functions"""
import six
from six import b
import sys
from .tile_types import ID_TO_CLASS_MAP

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
