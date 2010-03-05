#!/usr/bin/python
#----------------------------------------------------------------
# routeAsCSV - routes with OSM data, and generates a
# CSV file containing the result
#
#------------------------------------------------------
#------------------------------------------------------
# Copyright 2007-2008, Oliver White
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
#------------------------------------------------------
from route import *

def routeToCSV(lat1,lon1,lat2,lon2, transport):
  """Format a route (as list of nodes)"""
  data = LoadOsm(transport)

  node1 = data.findNode(lat1,lon1)
  node2 = data.findNode(lat2,lon2)

  router = Router(data)
  result, route = router.doRoute(node1, node2)
  if result != 'success':
    return("Fail")

  output = ''
  for i in route:
    node = data.rnodes[i]
    output = output + "%d,%f,%f\n" % ( \
      i,
      node[0],
      node[1])
  return(output)

def routeToCSVFile(lat1,lon1,lat2,lon2, transport, filename):
  f = open(filename,'w')
  f.write(routeToCSV(lat1,lon1,lat2,lon2, transport))
  f.close()


if __name__ == "__main__":
  print routeToCSV(
    52.2181,
    0.1162,
    52.2184,
    0.1427,
    "cycle")
