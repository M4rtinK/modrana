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

def old_clusterTrackpoints(trackpointsList , cluster_distance):
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


def perElevList(trackpointsList, numPoints=200):
  """determine elevation in regual interval, numPoints gives the number of intervals"""
  points = [{'lat': point.latitude,'lon': point.longitude, 'elev': point.elevation} for point in trackpointsList[0]]
  firstPoint = (points[0])
  fLat = firstPoint['lat']
  fLon = firstPoint['lon']
  # create a list, where we have have (distance from starting point, elevation)
  distanceList = map(lambda x: (distance(fLat, fLon, x['lat'], x['lon']),x['elev']) , points)
  trackLength = distanceList[-1][0]
  delta = trackLength / numPoints
  for i in range(1,numPoints): # like this, we should always be between two points with known elevation
    currentDistance = i * delta
    distanceList.append((currentDistance, None)) # we add the new

  distanceList.sort()

  periodicElevationList = []
  periodicElevationList.append(distanceList[0]) # add the first point of the track
  index = 0
#  print "length: %d" % len(distanceList)
  for point in distanceList:
    if point[1] == None:
      prevIndex = index-1
      while distanceList[prevIndex][1] == None:
        prevIndex = prevIndex - 1
      prevPoint = distanceList[prevIndex]

      nextIndex = index+1
      while distanceList[nextIndex][1] == None:
        nextIndex = nextIndex + 1
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
        oposite = abs(prevPoint[1]-nextPoint[1])
        adjecent = abs(prevPoint[0]-nextPoint[0])
        beta = atan(oposite/adjecent)
        alpha = pi - beta - pi/2
        adjecentPart = nextPoint[0] - point[0]
        dElev =  adjecentPart / tan(alpha)
        newElev = nextElev + dElev

      elif prevElev < nextElev:
        oposite = abs(prevPoint[1]-nextPoint[1])
        adjecent = abs(prevPoint[0]-nextPoint[0])
        beta = atan(oposite/adjecent)
        alpha = pi - beta - pi/2
        adjecentPart = point[0] - prevPoint[0]
        dElev = adjecentPart / tan(alpha)
        newElev = prevElev + dElev

      periodicElevationList.append((point[0],newElev))

    index = index + 1



#  print distanceList
#  print periodicElevationList
  periodicElevationList.append(distanceList[-1]) # add the last point of the track
  return(periodicElevationList)



#  print distanceList





if(__name__ == "__main__"):
  print distance(51,-1,52,1)
  print bearing(51,-1,52,1)
