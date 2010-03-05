#
# vim: set sw=4 sts=4 et tw=80 fileencoding=utf-8:
#
"""nmea - Imports GPS NMEA-formatted data files"""
# Copyright (C) 2007-2008  James Rowe
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
#

import datetime
import logging

from operator import xor

from upoints import (point, utils)

def calc_checksum(sentence):
    """
    Calculate a NMEA 0183 checksum for the given sentence

    NMEA checksums are a simple XOR of all the characters in the sentence
    between the leading "$" symbol, and the "*" checksum separator.

    >>> calc_checksum("$GPGGA,142058,5308.6414,N,00300.9257,W,1,04,5.6,1374.6,M,34.5,M,,*6B")
    107
    >>> calc_checksum("GPGGA,142058,5308.6414,N,00300.9257,W,1,04,5.6,1374.6,M,34.5,M,,*6B")
    107
    >>> calc_checksum("$GPGGA,142058,5308.6414,N,00300.9257,W,1,04,5.6,1374.6,M,34.5,M,,")
    107
    >>> calc_checksum("GPGGA,142058,5308.6414,N,00300.9257,W,1,04,5.6,1374.6,M,34.5,M,,")
    107

    :Parameters:
        sentence : `str`
            NMEA 0183 formatted sentence
    """
    if sentence.startswith("$"):
        sentence = sentence[1:]
    if "*" in sentence:
        sentence = sentence.split("*")[0]
    return reduce(xor, map(ord, sentence))

def nmea_latitude(latitude):
    """
    Generate a NMEA-formatted latitude pair

    >>> nmea_latitude(53.144023333333337)
    ('5308.6414', 'N')

    :Parameters:
        latitude : `float` or coercible to `float`
            Latitude to convert
    :rtype: `tuple`
    :return: NMEA-formatted latitude values
    """
    return ("%02i%07.4f" % utils.to_dms(abs(latitude), "dm"),
            "N" if latitude >= 0 else "S")

def nmea_longitude(longitude):
    """
    Generate a NMEA-formatted longitude pair

    >>> nmea_longitude(-3.0154283333333334)
    ('00300.9257', 'W')

    :Parameters:
        longitude : `float` or coercible to `float`
            Longitude to convert
    :rtype: `tuple`
    :return: NMEA-formatted longitude values
    """
    return ("%03i%07.4f" % utils.to_dms(abs(longitude), "dm"),
            "E" if longitude >= 0 else "W")

def parse_latitude(latitude, hemisphere):
    """
    Parse a NMEA-formatted latitude pair

    >>> parse_latitude("5308.6414", "N")
    53.144023333333337

    :Parameters:
        latitude : `str`
            Latitude in DDMM.MMMM
        hemisphere : `str`
            North or South
    :rtype: `float`
    :return: Decimal representation of latitude
    """
    latitude = int(latitude[:2]) + float(latitude[2:]) / 60
    if hemisphere == "S":
        latitude = -latitude
    elif not hemisphere == "N":
        raise ValueError("Incorrect North/South value `%s'" % hemisphere)
    return latitude

def parse_longitude(longitude, hemisphere):
    """
    Parse a NMEA-formatted longitude pair

    >>> parse_longitude("00300.9257", "W")
    -3.0154283333333334

    :Parameters:
        longitude : `str`
            Longitude in DDDMM.MMMM
        hemisphere : `str`
            East or West
    :rtype: `float`
    :return: Decimal representation of longitude
    """
    longitude = int(longitude[:3]) + float(longitude[3:]) / 60
    if hemisphere == "W":
        longitude = -longitude
    elif not hemisphere == "E":
        raise ValueError("Incorrect North/South value `%s'" % hemisphere)
    return longitude

MODE_INDICATOR = {
    "A": "Autonomous",
    "D": "Differential",
    "E": "Estimated",
    "M": "Manual",
    "S": "Simulated",
    "N": "Invalid",
} #: NMEA's mapping of code to reading type

class LoranPosition(point.Point):
    """
    Class for representing a GPS NMEA-formatted Loran-C position

    :since: 0.8.0

    :Ivariables:
        latitude
            Unit's latitude
        longitude
            Unit's longitude
        time
            Time the position was taken
        status
            GPS status
        mode
            Type of reading
    """

    __slots__ = ('time', 'status', 'mode')

    def __init__(self, latitude, longitude, time, status, mode=None):
        """
        Initialise a new `LoranPosition` object

        >>> LoranPosition(53.1440233333, -3.01542833333,
        ...               datetime.time(14, 20, 58, 14), True, None)
        LoranPosition(53.1440233333, -3.01542833333,
                      datetime.time(14, 20, 58, 14), True, None)
        >>> LoranPosition(53.1440233333, -3.01542833333,
        ...               datetime.time(14, 20, 58, 14), True, "A")
        LoranPosition(53.1440233333, -3.01542833333,
                      datetime.time(14, 20, 58, 14), True, 'A')

        :Parameters:
            latitude : `float` or coercible to `float`
                Fix's latitude
            longitude : `float` or coercible to `float`
                Fix's longitude
            time : ``datetime.time``
                Time the fix was taken
            status : `bool`
                Whether the data is active
            mode : `str`
                Type of reading
        """
        super(LoranPosition, self).__init__(latitude, longitude)
        self.time = time
        self.status = status
        self.mode = mode

    def __str__(self, talker="GP"):
        """
        Pretty printed position string

        >>> print(LoranPosition(53.1440233333, -3.01542833333,
        ...                     datetime.time(14, 20, 58), True, None))
        $GPGLL,5308.6414,N,00300.9257,W,142058.00,A*1F
        >>> print(LoranPosition(53.1440233333, -3.01542833333,
        ...                     datetime.time(14, 20, 58), True, "A"))
        $GPGLL,5308.6414,N,00300.9257,W,142058.00,A,A*72

        :Parameters:
            talker : `str`
                Talker ID
        :rtype: `str`
        :return: Human readable string representation of `Position` object
        """
        if not len(talker) == 2:
            raise ValueError("Talker ID must be two characters `%s'" % talker)
        data = ["%sGLL" % talker]
        data.extend(nmea_latitude(self.latitude))
        data.extend(nmea_longitude(self.longitude))
        data.append("%s.%02i" % (self.time.strftime("%H%M%S"),
                                self.time.microsecond/1000000))
        data.append("A" if self.status else "V")
        if self.mode:
            data.append(self.mode)
        data = ",".join(data)
        return "$%s*%X\r" % (data, calc_checksum(data))

    def mode_string(self):
        """
        Return a string version of the reading mode information

        >>> position = LoranPosition(53.1440233333, -3.01542833333,
        ...                          datetime.time(14, 20, 58), True, None)
        >>> print(position.mode_string())
        Unknown
        >>> position.mode = "A"
        >>> print(position.mode_string())
        Autonomous

        :rtype: `str`
        :return: Quality information as string
        """
        return MODE_INDICATOR.get(self.mode, "Unknown")

    @staticmethod
    def parse_elements(elements):
        """
        Parse position data elements

        >>> LoranPosition.parse_elements(["52.32144", "N", "00300.9257", "W",
        ...                               "14205914", "A"])
        LoranPosition(52.0053573333, -3.01542833333, datetime.time(14, 20, 59, 140000), True, None)

        :Parameters:
            elements : `list`
                Data values for fix
        :rtype: `Fix`
        :return: Fix object representing data
        """
        if not len(elements) in (6, 7):
            raise ValueError("Invalid GLL position data")
        # Latitude and longitude are checked for validity during Fix
        # instantiation
        latitude = parse_latitude(elements[0], elements[1])
        longitude = parse_longitude(elements[2], elements[3])
        hour, minute, second = [int(elements[4][i:i+2]) for i in range(0, 6, 2)]
        usecond = int(elements[4][6:8]) * 10000
        time = datetime.time(hour, minute, second, usecond)
        active = True if elements[5] == "A" else False
        mode = elements[6] if len(elements) == 7 else None
        return LoranPosition(latitude, longitude, time, active, mode)


class Position(point.Point):
    """
    Class for representing a GPS NMEA-formatted position

    :since: 0.8.0

    :Ivariables:
        time
            Time the position was taken
        status
            GPS status
        latitude
            Unit's latitude
        longitude
            Unit's longitude
        speed
            Unit's speed in knots
        track
            Track angle
        date
            Date when position was taken
        variation
            Magnetic variation
        mode
            Type of reading
    """

    __slots__ = ('time', 'status', 'speed', 'track', 'date', 'variation',
                 'mode')

    def __init__(self, time, status, latitude, longitude, speed, track, date,
                 variation, mode=None):
        """
        Initialise a new `Position` object

        >>> Position(datetime.time(14, 20, 58), True, 53.1440233333, -3.01542833333,
        ...          109394.7, 202.9, datetime.date(2007, 11, 19), 5.0)
        Position(datetime.time(14, 20, 58), True, 53.1440233333, -3.01542833333,
                 109394.7, 202.9, datetime.date(2007, 11, 19), 5.0, None)

        :Parameters:
            time : ``datetime.time``
                Time the fix was taken
            status : `bool`
                Whether the data is active
            latitude : `float` or coercible to `float`
                Fix's latitude
            longitude : `float` or coercible to `float`
                Fix's longitude
            speed : `float` or coercible to `float`
                Ground speed
            track : `float` or coercible to `float`
                Track angle
            date : ``datetime.date``
                Date when position was taken
            variation : `float` or coercible to `float`
                Magnetic variation
            mode : `str`
                Type of reading
        """
        super(Position, self).__init__(latitude, longitude)
        self.time = time
        self.status = status
        self.speed = speed
        self.track = track
        self.date = date
        self.variation = variation
        self.mode = mode

    def __str__(self):
        """
        Pretty printed position string

        >>> print(Position(datetime.time(14, 20, 58), True, 53.1440233333,
        ...                -3.01542833333, 109394.7, 202.9,
        ...                datetime.date(2007, 11, 19), 5.0))
        $GPRMC,142058,A,5308.6414,N,00300.9257,W,109394.7,202.9,191107,5,E*41

        :rtype: `str`
        :return: Human readable string representation of `Position` object
        """
        data = ["GPRMC"]
        data.append(self.time.strftime("%H%M%S"))
        data.append("A" if self.status else "V")
        data.extend(nmea_latitude(self.latitude))
        data.extend(nmea_longitude(self.longitude))
        data.append("%.1f" % self.speed)
        data.append("%.1f" % self.track)
        data.append(self.date.strftime("%d%m%y"))
        if self.variation == int(self.variation):
            data.append("%i" % abs(self.variation))
        else:
            data.append("%.1f" % abs(self.variation))
        data.append("E" if self.variation >= 0 else "W")
        if self.mode:
            data.append(self.mode)
        data = ",".join(data)
        return "$%s*%X\r" % (data, calc_checksum(data))

    def mode_string(self):
        """
        Return a string version of the reading mode information

        >>> position = Position(datetime.time(14, 20, 58), True, 53.1440233333,
        ...                     -3.01542833333, 109394.7, 202.9,
        ...                     datetime.date(2007, 11, 19), 5.0)
        >>> print(position.mode_string())
        Unknown
        >>> position.mode = "A"
        >>> print(position.mode_string())
        Autonomous

        :rtype: `str`
        :return: Quality information as string
        """
        return MODE_INDICATOR.get(self.mode, "Unknown")

    @staticmethod
    def parse_elements(elements):
        """
        Parse position data elements

        >>> Position.parse_elements(["142058", "A", "5308.6414", "N",
        ...                          "00300.9257", "W", "109394.7", "202.9",
        ...                          "191107", "5", "E", "A"])
        Position(datetime.time(14, 20, 58), True, 53.1440233333, -3.01542833333,
                 109394.7, 202.9, datetime.date(2007, 11, 19), 5.0, 'A')
        >>> Position.parse_elements(["142100", "A", "5200.9000", "N",
        ...                          "00316.6600", "W", "123142.7", "188.1",
        ...                          "191107", "5", "E", "A"])
        Position(datetime.time(14, 21), True, 52.015, -3.27766666667, 123142.7,
                 188.1, datetime.date(2007, 11, 19), 5.0, 'A')

        :Parameters:
            elements : `list`
                Data values for fix
        :rtype: `Fix`
        :return: Fix object representing data
        """
        if not len(elements) in (11, 12):
            raise ValueError("Invalid RMC position data")
        time = datetime.time(*[int(elements[0][i:i+2]) for i in range(0, 6, 2)])
        active = True if elements[1] == "A" else False
        # Latitude and longitude are checked for validity during Fix
        # instantiation
        latitude = parse_latitude(elements[2], elements[3])
        longitude = parse_longitude(elements[4], elements[5])
        speed = float(elements[6])
        track = float(elements[7])
        date = datetime.date(2000+int(elements[8][4:6]), int(elements[8][2:4]),
                             int(elements[8][:2]))
        variation = float(elements[9]) if not elements[9] == "" else None
        if elements[10] == "W":
            variation = -variation
        elif variation and not elements[10] == "E":
            raise ValueError("Incorrect variation value `%s'"
                             % elements[10])
        mode = elements[11] if len(elements) == 12 else None
        return Position(time, active, latitude, longitude, speed, track, date,
                        variation, mode)


class Fix(point.Point):
    """
    Class for representing a GPS NMEA-formatted system fix

    :since: 0.8.0

    :Ivariables:
        time
            Time the fix was taken
        latitude
            Fix's latitude
        longitude
            Fix's longitude
        quality
            Mode under which the fix was taken
        satellites
            Number of tracked satellites
        dilution
            Horizontal dilution at reported position
        altitude
            Altitude above MSL
        geoid_delta
            Height of geoid's MSL above WGS84 ellipsoid
        dgps_delta
            Number of seconds since last DGPS sync
        dgps_station
            Identifier of the last synced DGPS station
        mode
            Type of reading
    :Ivariables:
        fix_quality
            List of fix quality integer to string representations
    """

    __slots__ = ('time', 'quality', 'satellites', 'dilution', 'altitude',
                 'geoid_delta', 'dgps_delta', 'dgps_station', 'mode')

    fix_quality = [
        "Invalid",
        "GPS",
        "DGPS",
        "PPS",
        "Real Time Kinematic"
        "Float RTK",
        "Estimated",
        "Manual",
        "Simulation",
    ]

    def __init__(self, time, latitude, longitude, quality, satellites, dilution,
                 altitude, geoid_delta, dgps_delta=None, dgps_station=None,
                 mode=None):
        """
        Initialise a new `Fix` object

        >>> Fix(datetime.time(14, 20, 27), 52.1380333333, -2.56861166667, 1, 4,
        ...     5.6, 1052.3, 34.5)
        Fix(datetime.time(14, 20, 27), 52.1380333333, -2.56861166667, 1, 4, 5.6,
            1052.3, 34.5, None, None, None)
        >>> Fix(datetime.time(14, 20, 27), 52.1380333333, -2.56861166667, 1, 4,
        ...     5.6, 1052.3, 34.5, 12, 4, None)
        Fix(datetime.time(14, 20, 27), 52.1380333333, -2.56861166667, 1, 4,
            5.6, 1052.3, 34.5, 12, 4, None)

        :Parameters:
            time : ``datetime.time``
                Time the fix was taken
            latitude : `float` or coercible to `float`
                Fix's latitude
            longitude : `float` or coercible to `float`
                Fix's longitude
            quality : `int`
                Mode under which the fix was taken
            satellites : `int`
                Number of tracked satellites
            dilution : `float`
                Horizontal dilution at reported position
            altitude : `float` or coercible to `float`
                Altitude above MSL
            geoid_delta : `float` or coercible to `float`
                Height of geoid's MSL above WGS84 ellipsoid
            dgps_delta : `float` or coercible to `float`
                Number of seconds since last DGPS sync
            dgps_station : `int`
                Identifier of the last synced DGPS station
            mode : `str`
                Type of reading
        """
        super(Fix, self).__init__(latitude, longitude)
        self.time = time
        self.quality = quality
        self.satellites = satellites
        self.dilution = dilution
        self.altitude = altitude
        self.geoid_delta = geoid_delta
        self.dgps_delta = dgps_delta
        self.dgps_station = dgps_station
        self.mode = mode

    def __str__(self):
        """
        Pretty printed location string

        >>> print(Fix(datetime.time(14, 20, 27), 52.1380333333, -2.56861166667,
        ...           1, 4, 5.6, 1052.3, 34.5))
        $GPGGA,142027,5208.2820,N,00234.1167,W,1,04,5.6,1052.3,M,34.5,M,,*61
        >>> print(Fix(datetime.time(14, 20, 27), 52.1380333333, -2.56861166667,
        ...           1, 4, 5.6, 1052.3, 34.5, 12, 4))
        $GPGGA,142027,5208.2820,N,00234.1167,W,1,04,5.6,1052.3,M,34.5,M,12.0,0004*78

        :rtype: `str`
        :return: Human readable string representation of `Fix` object
        """
        data = ["GPGGA"]
        data.append(self.time.strftime("%H%M%S"))
        data.extend(nmea_latitude(self.latitude))
        data.extend(nmea_longitude(self.longitude))
        data.append(str(self.quality))
        data.append("%02i" % self.satellites)
        data.append("%.1f" % self.dilution)
        data.append("%.1f" % self.altitude)
        data.append("M")
        data.append("-" if not self.geoid_delta else "%.1f" % self.geoid_delta)
        data.append("M")
        data.append("%.1f" % self.dgps_delta if self.dgps_delta else "")
        data.append("%04i" % self.dgps_station if self.dgps_station else "")
        data = ",".join(data)
        return "$%s*%X\r" % (data, calc_checksum(data))

    def quality_string(self):
        """
        Return a string version of the quality information

        >>> fix = Fix(datetime.time(14, 20, 58), 53.1440233333, -3.01542833333,
        ...           1, 4, 5.6, 1374.6, 34.5, None, None)
        >>> print(fix.quality_string())
        GPS

        :rtype: `str`
        :return: Quality information as string
        """
        return self.fix_quality[self.quality]

    @staticmethod
    def parse_elements(elements):
        """
        Parse essential fix's data elements

        >>> Fix.parse_elements(["142058", "5308.6414", "N", "00300.9257", "W", "1",
        ...                     "04", "5.6", "1374.6", "M", "34.5", "M", "", ""])
        Fix(datetime.time(14, 20, 58), 53.1440233333, -3.01542833333, 1, 4, 5.6,
            1374.6, 34.5, None, None, None)
        >>> Fix.parse_elements(["142100", "5200.9000", "N", "00316.6600", "W", "1",
        ...                     "04", "5.6", "1000.0", "M", "34.5", "M", "", ""])
        Fix(datetime.time(14, 21), 52.015, -3.27766666667, 1, 4, 5.6, 1000.0, 34.5,
            None, None, None)

        :Parameters:
            elements : `list`
                Data values for fix
        :rtype: `Fix`
        :return: Fix object representing data
        """
        if not len(elements) in (14, 15):
            raise ValueError("Invalid GGA fix data")
        time = datetime.time(*[int(elements[0][i:i+2]) for i in range(0, 6, 2)])
        # Latitude and longitude are checked for validity during Fix
        # instantiation
        latitude = parse_latitude(elements[1], elements[2])
        longitude = parse_longitude(elements[3], elements[4])
        quality = int(elements[5])
        if not 0 <= quality <= 9:
            raise ValueError("Invalid quality value `%i'" % quality)
        satellites = int(elements[6])
        if not 0 <= satellites <= 12:
            raise ValueError("Invalid number of satellites `%i'"
                             % satellites)
        dilution = float(elements[7])
        altitude = float(elements[8])
        if elements[9] == "F":
            altitude = altitude * 3.2808399
        elif not elements[9] == "M":
            raise ValueError("Unknown altitude unit `%s'" % elements[9])
        if elements[10] in ("-", ""):
            geoid_delta = False
            logging.warning("Altitude data could be incorrect, as the geoid "
                            "difference has not been provided")
        else:
            geoid_delta = float(elements[10])
        if elements[11] == "F":
            geoid_delta = geoid_delta * 3.2808399
        elif geoid_delta and not elements[11] == "M":
            raise ValueError("Unknown geoid delta unit `%s'" % elements[11])
        dgps_delta = float(elements[12]) if elements[12] else None
        dgps_station = int(elements[13]) if elements[13] else None
        mode = elements[14] if len(elements) == 15 else None
        return Fix(time, latitude, longitude, quality, satellites, dilution,
                   altitude, geoid_delta, dgps_delta, dgps_station, mode)


class Waypoint(point.Point):
    """
    Class for representing a NMEA-formatted waypoint

    :since: 0.8.0

    :Ivariables:
        latitude
            Waypoint's latitude
        longitude
            Waypoint's longitude
        name
            Waypoint's name
    """

    __slots__ = ('name', )

    def __init__(self, latitude, longitude, name):
        """
        Initialise a new `Waypoint` object

        >>> Waypoint(52.015, -0.221, "Home")
        Waypoint(52.015, -0.221, 'HOME')

        :Parameters:
            latitude : `float` or coercible to `float`
                Waypoint's latitude
            longitude : `float` or coercible to `float`
                Waypoint's longitude
            name : `str`
                Comment for waypoint
        """
        super(Waypoint, self).__init__(latitude, longitude)
        self.name = name.upper()

    def __str__(self):
        """
        Pretty printed location string

        >>> print(Waypoint(52.015, -0.221, "Home"))
        $GPWPL,5200.9000,N,00013.2600,W,HOME*5E

        :rtype: `str`
        :return: Human readable string representation of `Waypoint` object
        """
        data = ["GPWPL"]
        data.extend(nmea_latitude(self.latitude))
        data.extend(nmea_longitude(self.longitude))
        data.append(self.name)
        data = ",".join(data)
        text = "$%s*%X\r" % (data, calc_checksum(data))
        if len(text) > 81:
            raise ValueError("All NMEA sentences must be less than 82 bytes "
                             "including line endings")
        return text

    @staticmethod
    def parse_elements(elements):
        """
        Parse waypoint data elements

        >>> Waypoint.parse_elements(["5200.9000", "N", "00013.2600", "W",
        ...                          "HOME"])
        Waypoint(52.015, -0.221, 'HOME')

        :Parameters:
            elements : `list`
                Data values for fix
        :rtype: `Fix`
        :return: Fix object representing data
        """
        if not len(elements) == 5:
            raise ValueError("Invalid WPL waypoint data")
        # Latitude and longitude are checked for validity during Fix
        # instantiation
        latitude = parse_latitude(elements[0], elements[1])
        longitude = parse_longitude(elements[2], elements[3])
        name = elements[4]
        return Waypoint(latitude, longitude, name)


class Locations(point.Points):
    """
    Class for representing a group of GPS location objects

    :since: 0.8.0
    """

    def __init__(self, gpsdata_file=None):
        """
        Initialise a new `Locations` object
        """
        super(Locations, self).__init__()
        if gpsdata_file:
            self.import_locations(gpsdata_file)

    def import_locations(self, gpsdata_file, checksum=True):
        """
        Import GPS NMEA-formatted data files

        `import_locations()` returns a list of `Fix` objects representing
        the fix sentences found in the GPS data.

        It expects data files in NMEA 0183 format, as specified in `the
        official documentation <http://www.nmea.org/pub/0183/>`__, which is
        ASCII text such as::

            $GPGSV,6,6,21,32,65,170,35*48
            $GPGGA,142058,5308.6414,N,00300.9257,W,1,04,5.6,1374.6,M,34.5,M,,*6B
            $GPRMC,142058,A,5308.6414,N,00300.9257,W,109394.7,202.9,191107,5,E,A*2C
            $GPGSV,6,1,21,02,76,044,43,03,84,156,49,06,89,116,51,08,60,184,30*7C
            $GPGSV,6,2,21,09,87,321,50,10,77,243,44,11,85,016,49,12,89,100,52*7A
            $GPGSV,6,3,21,13,70,319,39,14,90,094,52,16,85,130,49,17,88,136,51*7E
            $GPGSV,6,4,21,18,57,052,27,24,65,007,34,25,62,142,32,26,88,031,51*73
            $GPGSV,6,5,21,27,64,343,33,28,45,231,16,30,84,198,49,31,90,015,52*7C
            $GPGSV,6,6,21,32,65,170,34*49
            $GPWPL,5200.9000,N,00013.2600,W,HOME*5E
            $GPGGA,142100,5200.9000,N,00316.6600,W,1,04,5.6,1000.0,M,34.5,M,,*68
            $GPRMC,142100,A,5200.9000,N,00316.6600,W,123142.7,188.1,191107,5,E,A*21

        The reader only imports the GGA, or GPS fix, sentences currently but
        future versions will probably support tracks and waypoints.  Other than
        that the data is out of scope for ``upoints``.

        The above file when processed by `import_locations()` will return
        the following `list` object::

            [Fix(datetime.time(14, 20, 58), 53.1440233333, -3.01542833333, 1, 4,
                 5.6, 1374.6, 34.5, None, None),
             Position(datetime.time(14, 20, 58), True, 53.1440233333,
                      -3.01542833333, 109394.7, 202.9,
                      datetime.date(2007, 11, 19), 5.0, 'A'),
             Waypoint(52.015, -0.221, 'Home'),
             Fix(datetime.time(14, 21), 52.015, -3.27766666667, 1, 4, 5.6,
                 1000.0, 34.5, None, None),
             Position(datetime.time(14, 21), True, 52.015, -3.27766666667,
                      123142.7, 188.1, datetime.date(2007, 11, 19), 5.0, 'A')]

        >>> locations = Locations(open("gpsdata"))
        >>> for value in locations:
        ...     print(value)
        $GPGGA,142058,5308.6414,N,00300.9257,W,1,04,5.6,1374.6,M,34.5,M,,*6B
        $GPRMC,142058,A,5308.6414,N,00300.9257,W,109394.7,202.9,191107,5,E,A*2C
        $GPWPL,5200.9000,N,00013.2600,W,HOME*5E
        $GPGGA,142100,5200.9000,N,00316.6600,W,1,04,5.6,1000.0,M,34.5,M,,*68
        $GPRMC,142100,A,5200.9000,N,00316.6600,W,123142.7,188.1,191107,5,E,A*21

        :note: The standard is quite specific in that sentences *must* be less
               than 82 bytes, while it would be nice to add yet another validity
               check it isn't all that uncommon for devices to break this
               requirement in their "extensions" to the standard.
        :todo: Add optional check for message length, on by default

        :Parameters:
            gpsdata_file : `file`, `list` or `str`
                NMEA data to read
            checksum : `bool`
                Whether checksums should be tested
        :rtype: `list`
        :return: Series of locations taken from the data
        """
        data = utils.prepare_read(gpsdata_file)

        parsers = {
            "GPGGA": Fix,
            "GPRMC": Position,
            "GPWPL": Waypoint,
            "GPGLL": LoranPosition,
            "LCGLL": LoranPosition,
        }

        if not checksum:
            logging.warning("Disabling the checksum tests should only be used"
                           "when the device is incapable of emitting the "
                           "correct values!")
        for line in data:
            # The standard tells us lines should end in \r\n even though some
            # devices break this, but Python's standard file object solves this
            # for us anyway.  However, be careful if you implement your own
            # opener.
            if not line[1:6] in parsers:
                continue
            if checksum:
                values, checksum = line[1:].split("*")
                if not calc_checksum(values) == int(checksum, 16):
                    raise ValueError("Sentence has invalid checksum")
            else:
                values = line[1:].split("*")[0]
            elements = values.split(",")
            parser = getattr(parsers[elements[0]], "parse_elements")
            self.append(parser(elements[1:]))

