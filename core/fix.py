# -*- coding: utf-8 -*-
# A fix encapsulating class, based on the AGTL Fix class
from datetime import datetime


class Fix():
    BEARING_HOLD_EPD = 90 # arbitrary, yet non-random value
    last_bearing = 0
    # tracking the minimum difference between a received fix time and
    # our current internal time.
    min_timediff = datetime.utcnow() - datetime.utcfromtimestamp(0)

    def __init__(self,
                 position=None,
                 altitude=None,
                 bearing=None,
                 speed=None,
                 climb=None,
                 magnetic_variation=None,
                 sats=None,
                 sats_in_use=None,
                 dgps=False,
                 mode=0,
                 error=0,
                 error_bearing=0,
                 horizontal_accuracy=None,
                 vertical_accuracy=None, # in meters
                 speed_accuracy=None, # in meters/sec
                 climb_accuracy=None, # in meters/sec
                 bearing_accuracy=None, # in degrees
                 time_accuracy=None, # in seconds
                 gps_time=None,
                 timestamp=None):
        self.position = position
        # debug - Brno
        # self.position = 49.2, 16.616667
        self.altitude = altitude
        self.bearing = bearing
        self.speed = speed
        self.climb = climb
        self.magnetic_variation = magnetic_variation
        self.sats = sats
        self.sats_in_use = sats_in_use
        self.dgps = dgps
        self.mode = mode
        self.error = error
        self.error_bearing = error_bearing
        self.horizontal_accuracy = horizontal_accuracy
        self.vertical_accuracy = vertical_accuracy
        self.speed_accuracy = speed_accuracy
        self.climb_accuracy = climb_accuracy
        self.bearing_accuracy = bearing_accuracy
        self.time_accuracy = time_accuracy
        self.gps_time = gps_time
        if timestamp is None:
            self.timestamp = datetime.utcnow()
        else:
            self.timestamp = timestamp

    def __str__(self):
        return 'mode:' + self.mode + 'lat,lon:' + self.position + 'elev:' + self.altitude