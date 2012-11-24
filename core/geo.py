# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Geographic calculations
#---------------------------------------------------------------------------
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
#---------------------------------------------------------------------------
from math import *
import time

EARTH_RADIUS = 6371.0

def distanceOld(lat1, lon1, lat2, lon2):
  """Distance between two points in km
  DEPRECIATED: the Marble distance algorithm was found to be just as precise
  while being 20% faster"""
  dLat = radians(lat2 - lat1)
  dLon = radians(lon2 - lon1)
  a = sin(dLat / 2.0) * sin(dLat / 2.0) +\
      cos(radians(lat1)) * cos(radians(lat2)) *\
      sin(dLon / 2.0) * sin(dLon / 2.0)
  return 2 * atan2(sqrt(a), sqrt(1.0 - a)) * EARTH_RADIUS


def simplePythagoreanDistance(x1, y1, x2, y2):
  dx = x2 - x1
  dy = y2 - y1
  return sqrt(dx ** 2 + dy ** 2)


def combinedDistance(pointList):
  """return combined distance for a list of ordered points
  NOTE: not tested yet !!"""
  combinedDistance = 0
  (lat1, lon1) = pointList[0]
  for point in pointList[1:]:
    (lat2, lon2) = point
    combinedDistance += distance(lat1, lon1, lat2, lon2)
    (lat1, lon1) = (lat2, lon2)
  return combinedDistance


def bearing(lat1, lon1, lat2, lon2):
  """Bearing from one point to another in degrees (0-360)"""
  dLat = lat2 - lat1
  dLon = lon2 - lon1
  y = sin(radians(dLon)) * cos(radians(lat2))
  x = cos(radians(lat1)) * sin(radians(lat2)) -\
      sin(radians(lat1)) * cos(radians(lat2)) * cos(radians(dLon))
  bearing = degrees(atan2(y, x))
  if bearing < 0.0:
    bearing += 360.0
  return bearing


def simpleDistancePointToLine(x, y, x1, y1, x2, y2):
  """distance from point to line in the plane"""
  # source: http://www.allegro.cc/forums/thread/589720
  A = x - x1
  B = y - y1
  C = x2 - x1
  D = y2 - y1

  dot = A * C + B * D
  len_sq = C * C + D * D
  if len_sq == 0:
    dist = A * A + B * B
    return dist

  param = dot / len_sq

  if param < 0:
    xx = x1
    yy = y1
  elif param > 1:
    xx = x2
    yy = y2
  else:
    xx = x1 + param * C
    yy = y1 + param * D

  dx = x - xx
  dy = y - yy
  dist = dx * dx + dy * dy
  return dist


def distancePointToLine(pLat, pLon, aLat, aLon, bLat, bLon):
  distancePointToLineRadians(radians(pLat), radians(pLon),
    radians(aLat), radians(aLon),
    radians(bLat), radians(bLon))


def distancePointToLineRadians(pLat, pLon, aLat, aLon, bLat, bLon):
  """compute distance between a point and a line on Earth
  -> based on C++ code from Marble"""
  y0 = pLat
  x0 = pLon
  y1 = aLat
  x1 = aLon
  y2 = bLat
  x2 = bLon
  y01 = x0 - x1
  x01 = y0 - y1
  y10 = x1 - x0
  x10 = y1 - y0
  y21 = x2 - x1
  x21 = y2 - y1
  len = (x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2)
  # handle zero-length lines
  if len == 0:
    return distanceApproxRadians(pLat, pLon, aLat, aLon)
    # for correct float division, one of the arguments needs to be a float
  t = (x01 * x21 + y01 * y21) / float(len)

  # NOTE: a version without the approximate distance might be needed in the future,
  # the 7 digit precision should be enough for now though
  if t < 0.0:
    return  distanceApproxRadians(pLat, pLon, aLat, aLon)
  elif t > 1.0:
    return  distanceApproxRadians(pLat, pLon, bLat, bLon)
  else:
    nom = abs(x21 * y10 - x10 * y21)
    den = sqrt(x21 * x21 + y21 * y21)
    return EARTH_RADIUS * ( nom / float(den) )


def distance(lat1, lon1, lat2, lon2):
  """computes geographic distance
  -> based on C++ code from Marble"""
  lat1 = radians(lat1)
  lon1 = radians(lon1)
  lat2 = radians(lat2)
  lon2 = radians(lon2)
  h1 = sin(0.5 * ( lat2 - lat1 ))
  h2 = sin(0.5 * ( lon2 - lon1 ))
  d = h1 * h1 + cos(lat1) * cos(lat2) * h2 * h2
  return 2.0 * atan2(sqrt(d), sqrt(1.0 - d)) * EARTH_RADIUS


def distanceApprox(lat1, lon1, lat2, lon2):
  """This method roughly calculates the shortest distance between two points on a sphere.
      It's probably faster than distanceSphere(...) but for 7 significant digits only has
      accuracy of about 1 arcminute
      -> based on C++ code from Marble"""
  lat1 = radians(lat1)
  lon1 = radians(lon1)
  lat2 = radians(lat2)
  lon2 = radians(lon2)
  return acos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon1 - lon2)) * EARTH_RADIUS


def distanceRadians(lat1, lon1, lat2, lon2):
  """computes geographic distance
  -> based on C++ code from Marble"""
  h1 = sin(0.5 * ( lat2 - lat1 ))
  h2 = sin(0.5 * ( lon2 - lon1 ))
  d = h1 * h1 + cos(lat1) * cos(lat2) * h2 * h2
  return 2.0 * atan2(sqrt(d), sqrt(1.0 - d)) * EARTH_RADIUS


def distanceApproxRadians(lat1, lon1, lat2, lon2):
  """This method roughly calculates the shortest distance between two points on a sphere.
      It's probably faster than distanceSphere(...) but for 7 significant digits only has
      accuracy of about 1 arcminute
      -> based on C++ code from Marble"""
  return acos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon1 - lon2)) * EARTH_RADIUS


def ll2radians(lat, lon):
  """convert lat and lon in degrees to radians"""
  return radians(lat), radians(lon)


def lle2radians(lat, lon, elevation):
  """convert lat and lon in degrees to radians - convenience function for LLE tuples"""
  return radians(lat), radians(lon), elevation


def lleTuples2radians(lleTuples, discardElevation=False):
  """converts (lat, lon, elevation) tuples from degrees to radians"""
  if discardElevation:
    return map(lambda x: (radians(x[0]), radians(x[1])), lleTuples)
  else:
    return map(lambda x: (radians(x[0]), radians(x[1]), x[2]), lleTuples)


def timestampUTC():
  return time.strftime("%Y-%m-%dT%H:%M:%S")


def turnAngle(first, middle, last):
  x1 = middle[0] - first[0] # a = (x1,y1)
  y1 = middle[1] - first[1]
  x2 = last[0] - middle[0] # b = (x2, y2 )
  y2 = last[1] - middle[1]
  direction = 0
  # Counterclockwise angle
  angle = ( atan2( y1, x1 ) - atan2( y2, x2 ) ) * 180 / pi + 720
  angle %= 360
  return angle

#def turnAngle(first, middle, last):
#  """
#  compute turn angle for a turn described by three points
#  -> an alternative methods that unfortunately seems not to work
#  """
##  print("INPUT")
##  print(first)
##  print(middle)
##  print(last)
#
#  lat_x, lon_x = radians(first[0]), radians(first[1])
#  lat_y, lon_y = radians(middle[0]), radians(middle[1])
#  lat_z, lon_z = radians(last[0]), radians(last[1])
#
#  #  input: 3 points X, Y, Z defined by (lat, lon) tupples ( in the usual <0..180 range)
#  #  1) plane conversion - cartesian coordinates with the pole in the middle:
#  X_x = EARTH_RADIUS * cos(lat_x) * cos(lon_x)
#  X_y = EARTH_RADIUS * cos(lat_x) * sin(lon_x)
#
#  Y_x = EARTH_RADIUS * cos(lat_y) * cos(lon_y)
#  Y_y = EARTH_RADIUS * cos(lat_y) * sin(lon_y)
#
#  Z_x = EARTH_RADIUS * cos(lat_z) * cos(lon_z)
#  Z_y = EARTH_RADIUS * cos(lat_z) * sin(lon_z)
#  #  2) determine the XYZ angle (=alpha):
#  #  first for clarity the u, v vector (u cerrsponds the XY segment, v the YZ segment)
#  u_x, u_y = (Y_x - X_x, Y_y - X_y)
#  v_x, v_y = (Z_x - Y_x, Z_y - Y_y)
#
#  alpha = acos((u_x * v_x + u_y * v_y) / sqrt((u_x - v_x) ** 2 + (u_y - v_y) ** 2))
#  alpha = degrees(alpha)
#
#  #  3) and finaly we determine the oreintation of the turn - left or right:
#  test = u_x * v_y - v_x * u_y
#
#  #  test=0 - not really a turn - all three points would make a line
#  #  test<0 - right turn
#  #  test>0 - left turn
#
#  # Final turn angle:
#  #
#  # 135 180 225
#  #    \ | /
#  # 90 ----- 270
#  #    / | \
#  #  45  0 360
#  #
#  # initial direction direction of travel = 0 degrees
#
#  if test > 0:
#    return alpha
#  else:
#    return alpha  + 180

# found on:
# http://www.quanative.com/2010/01/01/server-side-marker-clustering-for-google-maps-with-python/
def clusterTrackpoints(trackpointsList, cluster_distance):
  """
  Groups points that are less than cluster_distance pixels apart at
  a given zoom level into a cluster.
  """
  clusters = []
  if trackpointsList:
    points = [{'latitude': point.latitude, 'longitude': point.longitude} for point in trackpointsList[0]]
    while len(points) > 0:
      point1 = points.pop()
      cluster = []
      for point2 in points[:]:
        pixel_distance = distance(point1['latitude'],
          point1['longitude'],
          point2['latitude'],
          point2['longitude'])

        if pixel_distance < cluster_distance:
          points.remove(point2)
          cluster.append(point2)

      # add the first point to the cluster
      if len(cluster) > 0:
        cluster.append(point1)
        clusters.append(cluster)
      else:
        clusters.append([point1])

  return clusters


def old_clusterTrackpoints(trackpointsList, cluster_distance):
  """
  Groups points that are less than cluster_distance pixels apart at
  a given zoom level into a cluster.
  """
  points = [{'latitude': point.latitude, 'longitude': point.longitude} for point in trackpointsList[0]]
  clusters = []
  while len(points) > 0:
    point1 = points.pop()
    cluster = []
    for point2 in points[:]:
      pixel_distance = distance(point1['latitude'],
        point1['longitude'],
        point2['latitude'],
        point2['longitude'])

      if pixel_distance < cluster_distance:
        points.remove(point2)
        cluster.append(point2)

    # add the first point to the cluster
    if len(cluster) > 0:
      cluster.append(point1)
      clusters.append(cluster)
    else:
      clusters.append([point1])

  return clusters


def circleAroundPointCluster(cluster):
  """Find a circle around a given point cluster and return its centre and radius"""

  """we get the most north, west, south, east points as a heuristics for the preliminary circle"""
  maxLat = max(cluster, key=lambda x: x['latitude'])
  minLat = min(cluster, key=lambda x: x['latitude'])
  maxLon = max(cluster, key=lambda x: x['longitude'])
  minLon = min(cluster, key=lambda x: x['longitude'])
  # extremes = [maxLat, minLat, maxLon, minLon]
  """now we find the north-south and west-east distances using the points above"""
  latDist = distance(maxLat['latitude'], maxLat['longitude'], minLat['latitude'], minLat['longitude'])
  lonDist = distance(maxLon['latitude'], maxLon['longitude'], minLon['latitude'], minLon['longitude'])
  if latDist >= lonDist: #the horizontal distance is the longest
    centreX = (maxLat['latitude'] + minLat['latitude']) / 2.0
    centreY = (maxLat['longitude'] + minLat['longitude']) / 2.0
    pointX = maxLat['latitude']
    pointY = maxLat['longitude']
    radius = distance(centreX, centreY, pointX, pointY)
  else: #the vertical distance is the longest
    centreX = (maxLon['latitude'] + minLon['latitude']) / 2.0
    centreY = (maxLon['longitude'] + minLon['longitude']) / 2.0
    pointX = maxLon['latitude']
    pointY = maxLon['longitude']
    radius = distance(centreX, centreY, pointX, pointY)
  """now we check if all points are inside the circle and adjust it if not"""
  for point in cluster:
    currentX = point['latitude']
    currentY = point['longitude']
    distanceFromPointToCentre = distance(centreX, centreY, currentX, currentY)
    if distanceFromPointToCentre > radius:
      radius = distanceFromPointToCentre

  return centreX, centreY, radius


def perElevList(trackpointsList, numPoints=200):
  """determine elevation in regular interval, numPoints gives the number of intervals"""
  points = [{'lat': point.latitude, 'lon': point.longitude, 'elev': point.elevation} for point in trackpointsList[0]]

  # create a list, where we have (cumulative distance from starting point, elevation)
  distanceList = [(0, points[0]['elev'], points[0]['lat'], points[0]['lon'])]
  prevIndex = 0
  totalDist = 0
  for point in points[1:]:
    prevPoint = points[prevIndex]
    (pLat, pLon) = (prevPoint['lat'], prevPoint['lon'])
    (lat, lon, elev) = (point['lat'], point['lon'], point['elev'])
    dist = distance(pLat, pLon, lat, lon)
    prevIndex += 1
    totalDist += dist
    distanceList.append((totalDist, elev, point['lat'], point['lon']))

  trackLength = distanceList[-1][0]
  delta = trackLength / numPoints
  for i in range(1, numPoints): # like this, we should always be between two points with known elevation
    currentDistance = i * delta
    distanceList.append((currentDistance, None)) # we add the new points in regular intervals

  distanceList.sort() # now we sort the list by distance

  periodicElevationList = [distanceList[0]]
  index = 0
  #  print("length: %d" % len(distanceList))

  """when we find a point with unknown elevation, we:
     * find the first points with known elevation to the "left" and "right"
     * elevation of these points create a virtual right triangle,
       where the opposite side is the elevation difference
     * using trigonometric calculations, we find the interpolated elevation of the current periodic point

     then we store the point in our new list and that's it

     we are doing this, to get carts with uniform x axis distribution,
     even when the points in the tracklog are no uniformly distributed (e.g. routing results)
  """
  for point in distanceList:
    if point[1] is None:
      prevIndex = index - 1
      while distanceList[prevIndex][1] is None:
        prevIndex -= 1
      prevPoint = distanceList[prevIndex]

      nextIndex = index + 1
      while distanceList[nextIndex][1] is None:
        nextIndex += 1
      nextPoint = distanceList[nextIndex]

      #      print prevPoint
      #      print point
      #      print nextPoint

      prevElev = prevPoint[1]
      nextElev = nextPoint[1]

      newElev = None
      if prevElev == nextElev:
        newElev = prevElev

      elif prevElev > nextElev:
        opposite = abs(prevPoint[1] - nextPoint[1])
        adjacent = abs(prevPoint[0] - nextPoint[0])
        beta = atan(opposite / adjacent)
        alpha = pi - beta - pi / 2
        adjacentPart = nextPoint[0] - point[0]
        dElev = adjacentPart / tan(alpha)
        newElev = nextElev + dElev

      elif prevElev < nextElev:
        opposite = abs(prevPoint[1] - nextPoint[1])
        adjacent = abs(prevPoint[0] - nextPoint[0])
        beta = atan(opposite / adjacent)
        alpha = pi - beta - pi / 2
        adjacentPart = point[0] - prevPoint[0]
        dElev = adjacentPart / tan(alpha)
        newElev = prevElev + dElev

      # add coordinates to periodic points
      (lat1, lon1) = prevPoint[2:4]
      (lat2, lon2) = nextPoint[2:4]
      #      (lat,lon) = point[2:4]
      d = distance(lat1, lon1, lat2, lon2) # distance between the two known points
      dPart = point[0] - prevPoint[0] # distance to the periodic point

      actual = dPart / d # the actual distance fraction
      rest = 1 - actual # how much remains

      # get the periodic point coordinates, depending on its distance from known points
      lat = (rest * lat1) + (actual * lat2)
      lon = (rest * lon1) + (actual * lon2)

      #      print (d,dPart)
      #      print (actual,rest)

      periodicElevationList.append((point[0], newElev, lat, lon))

    index += 1

  periodicElevationList.append(distanceList[-1]) # add the last point of the track

  return periodicElevationList


def distanceBenchmark(LLE, sampleSize=None):
  """geographic distance measurement method benchmark"""

  lat, lon = 49.2, 16.616667 # Brno
  print("#Geographic distance algorithm benchmark start #")
  print("%d points" % len(LLE))

  # first test on classic lat, lon, elevation tuples with coordinates in degrees

  # Classic modRana method
  start1 = time.clock()
  l = map(lambda x: distanceOld(lat, lon, x[0], x[1]), LLE)
  print("%1.9f ms Classic modRana method" % (1000 * (time.clock() - start1)))
  if sampleSize:
    print l[0:sampleSize - 1]

  # Marble method
  start1 = time.clock()
  l = map(lambda x: distance(lat, lon, x[0], x[1]), LLE)
  print("%1.9f ms Marble method" % (1000 * (time.clock() - start1)))
  if sampleSize:
    print l[0:sampleSize - 1]

  # Marble approximate
  start1 = time.clock()
  l = map(lambda x: distanceApprox(lat, lon, x[0], x[1]), LLE)
  print("%1.9f ms Marble approximate method" % (1000 * (time.clock() - start1)))
  if sampleSize:
    print l[0:sampleSize - 1]

  # lets check on precomputed coordinates in radians
  LLERadians = map(lambda x: (radians(x[0]), radians(x[1]), x[2]), LLE)
  lat = radians(lat)
  lon = radians(lon)
  # Marble method on radians
  start1 = time.clock()
  l = map(lambda x: distanceRadians(lat, lon, x[0], x[1]), LLERadians)
  print("%1.9f ms Marble method on radians" % (1000 * (time.clock() - start1)))
  if sampleSize:
    print l[0:sampleSize - 1]

  # Marble approximate method on radians
  start1 = time.clock()
  l = map(lambda x: distanceApproxRadians(lat, lon, x[0], x[1]), LLERadians)
  print("%1.9f ms Marble approximate method on radians" % (1000 * (time.clock() - start1)))
  if sampleSize:
    print l[0:sampleSize - 1]

  # done
  print("# benchmark finished #")

## RESULTS ##
# (a route from prague to Sevastopol was used)
#  * N900 example (varies a bit) *
#
# #Geographic distance algorithm benchmark start #
# 6456 points
# 510.000000000 ms Classic modRana method
# 400.000000000 ms Marble method
# 370.000000000 ms Marble approximate method
# 340.000000000 ms Marble method on radians
# 290.000000000 ms Marble approximate method on radians
# # benchmark finished #
#
# * Core i5 Notebook *
#
# #Geographic distance algorithm benchmark start #
# 6456 points
# 30.000000000 ms Classic modRana method
# 20.000000000 ms Marble method
# 10.000000000 ms Marble approximate method
# 20.000000000 ms Marble method on radians
# 10.000000000 ms Marble approximate method on radians
# # benchmark finished #
