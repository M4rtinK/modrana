"""Tile type definitions"""

class AbstractTileType(object):
    id = ""
    extension = ""

class PNGTile(AbstractTileType):
    id = "png"
    extension = "png"

class JPEGTile(AbstractTileType):
    id = "jpg"
    extension = "jpg"

class GifTile(AbstractTileType):
    id = "gif"
    extension = "gif"

class BMPTile(AbstractTileType):
    id = "bmp"
    extension = "bmp"

class OSMDataTile(AbstractTileType):
    id = "osm_data"
    extension = "osm_data"

ID_TO_CLASS_MAP = {
    "png" : PNGTile,
    "jpg" : JPEGTile,
    "gif" : GifTile,
    "bmp" : BMPTile,
    "osm_data" : OSMDataTile
}
