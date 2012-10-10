#!/usr/bin/env python
EARTH_RADIUS = 6371.0
from math import *

def turnAngle(first, middle, last):
  """
  compute turn angle for a turn described by three points
  """
  lat_x, lon_x = radians(first[0]), radians(first[1])
  lat_y, lon_y = radians(middle[0]), radians(middle[1])
  lat_z, lon_z = radians(last[0]), radians(last[1])
  #  input: 3 points X, Y, Z defined by (lat, lon) tupples ( in the usual <0..180 range)
  #  1) plane conversion - cartesian coordinates with the pole in the middle:
  X_x = EARTH_RADIUS * cos(lon_x) * cos(lat_x)
  X_y = EARTH_RADIUS * cos(lon_y) * sin(lat_x)

  Y_x = EARTH_RADIUS * cos(lon_y) * cos(lat_y)
  Y_y = EARTH_RADIUS * cos(lon_y) * sin(lat_y)

  Z_x = EARTH_RADIUS * cos(lon_z) * cos(lat_z)
  Z_y = EARTH_RADIUS * cos(lon_z) * sin(lat_z)

  #  2) determine the XYZ angle (=alpha):
  #  first for clarity the u, v vector (u cerrsponds the XY segment, v the YZ segment)
  u_x, u_y = (Y_x - X_x, Y_y - X_y)
  v_x, v_y = (Z_x - Y_x, Z_y - Y_y)
  alpha = acos((u_x * v_x + u_y * v_y) / sqrt((u_x - v_x) ** 2 + (u_y - v_y) ** 2))

  #  3) and finaly we determine the oreintation of the turn - left or right:
  test = u_x * v_y - v_x * u_y

  #  test=0 - not really a turn - all three points would make a line
  #  test<0 - right turn
  #  test>0 - left turn

  if test < 0:
    return alpha
  else:
    return 180 + alpha

    # Final turn angle:
    #
    # 135 180 225
    #    \ | /
    # 90 ----- 270
    #    / | \
    #  45  0 360
    #
    # initial direction direction of travel = 0 degrees


first = (48.979680284717986, 16.524889916181564)
middle = (48.9798695279217, 16.524889916181564)
last = (48.98003082417812, 16.524889916181564)

print("computing turn angle")
angle = turnAngle(first, middle, last)
print(angle)
