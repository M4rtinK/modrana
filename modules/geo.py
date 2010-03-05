#!/usr/bin/python
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

def distance(lat1,lon1,lat2,lon2):
  """Distance between two points in km"""
  R = 6371.0
  dLat = radians(lat2-lat1)
  dLon = radians(lon2-lon1)
  a = sin(dLat/2.0) * sin(dLat/2.0) + \
          cos(radians(lat1)) * cos(radians(lat2)) * \
          sin(dLon/2.0) * sin(dLon/2.0)
  c = 2 * atan2(sqrt(a), sqrt(1.0-a))
  return(R * c)

def simplePythagoreanDistance(x1, y1, x2, y2):
  dx = x2 - x1
  dy = y2 - y1
  return sqrt(dx**2 + dy**2)

def bearing(lat1,lon1,lat2,lon2):
  """Bearing from one point to another in degrees (0-360)"""
  dLat = lat2-lat1
  dLon = lon2-lon1
  y = sin(radians(dLon)) * cos(radians(lat2))
  x = cos(radians(lat1)) * sin(radians(lat2)) - \
          sin(radians(lat1)) * cos(radians(lat2)) * cos(radians(dLon))
  bearing = degrees(atan2(y, x))
  if(bearing < 0.0):
    bearing += 360.0
  return(bearing)

  # found on:
  # http://www.quanative.com/2010/01/01/server-side-marker-clustering-for-google-maps-with-python/
def clusterTrackpoints(trackpointsList , cluster_distance):
  """
  Groups points that are less than cluster_distance pixels apart at
  a given zoom level into a cluster.
  """
  points = [{'latitude': point.latitude,'longitude': point.longitude} for point in trackpointsList[0]]
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
  """Find a cricle around a given point cluster and return its centre and radius"""

  """we get the most nort,west,south,east points as a heristics for the preliminary circle"""
  maxLat = max(cluster, key=lambda x: x['latitude'])
  minLat = min(cluster, key=lambda x: x['latitude'])
  maxLon = max(cluster, key=lambda x: x['longitude'])
  minLon = min(cluster, key=lambda x: x['longitude'])
  # extremes = [maxLat, minLat, maxLon, minLon]
  """now we find the nort-south and west-east distances using the points above"""
  latDist = distance(maxLat['latitude'],maxLat['longitude'],minLat['latitude'],minLat['longitude'])
  lonDist = distance(maxLon['latitude'],maxLon['longitude'],minLon['latitude'],minLon['longitude'])
  if latDist >= lonDist: #the horizonatal distance is the longest
    centreX = (maxLat['latitude'] + minLat['latitude'])/2.0
    centreY = (maxLat['longitude'] + minLat['longitude'])/2.0
    pointX = maxLat['latitude']
    pointY = maxLat['longitude']
    radius = distance(centreX, centreY, pointX, pointY)
  else: #the vertical distance is the longest
    centreX = (maxLon['latitude'] + minLon['latitude'])/2.0
    centreY = (maxLon['longitude'] + minLon['longitude'])/2.0
    pointX = maxLon['latitude']
    pointY = maxLon['longitude']
    radius = distance(centreX, centreY, pointX, pointY)
  """now we check if all points are inside the circle and adjut it if not"""
  for point in cluster:
    currentX = point['latitude']
    currentY = point['longitude']
    distanceFromPointToCentre = distance(centreX,centreY,currentX,currentY)
    if distanceFromPointToCentre > radius:
      radius = distanceFromPointToCentre

  return(centreX, centreY, radius)







if(__name__ == "__main__"):
  print distance(51,-1,52,1)
  print bearing(51,-1,52,1)
