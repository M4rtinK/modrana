import os
from tiledata import GetOsmTileData
from OsmMerge import OsmMerge


def test(z,x,y):
  filenames = []
  for i in (0,1):
    for j in (0,1):
      lx = x * 2 + i
      ly = y * 2 + j
      lz = z + 1
      #print "Downloading subtile %d,%d at %d" % (x,y,z)
      # download (or otherwise obtain) each subtile
      filenames.append(GetOsmTileData(lz,lx,ly))
  # merge them together
  OsmMerge("merged.osm", z, filenames)

if(__name__ == "__main__"):
  #test(14,8009,5443) # swansea
  test(13,4070,2682) # leicester
  