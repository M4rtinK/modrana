#
# vim: set sw=4 sts=4 et tw=80 fileencoding=utf-8:
#
"""utils - Support code for upoints"""
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

from __future__ import division

__bug_report__ = "James Rowe <jnrowe@ukfsn.org>" #: Address for use in messages

import csv
import datetime
import inspect
import logging
import math
import re

from xml.etree import ElementTree
try:
    from xml.etree import cElementTree as ET
except ImportError:
    try:
        from lxml import etree as ET
    except ImportError:
        ET = ElementTree
        logging.info("cElementTree is unavailable XML processing will be much"
                     "slower with ElementTree")

from operator import add

BODIES = {
    # Body radii in kilometres
    'Sun': 696000,

    # Terrestrial inner planets
    'Mercury': 2440,
    'Venus': 6052,
    'Earth': 6367,
    'Mars': 3390,

    # Gas giant outer planets
    'Jupiter': 69911,
    'Saturn': 58232,
    'Uranus': 25362,
    'Neptune': 24622,

    # only satellite to be added
    'Moon': 1738,

    # dwarf planets may be added
    'Pluto': 1153,
    'Ceres': 475,
    'Eris': 1200,
} #: Body radii of various solar system objects

BODY_RADIUS = BODIES['Earth'] #: Default body radius to use for calculations
NAUTICAL_MILE = 1.852 #: Number of kilometres per nautical mile
STATUTE_MILE = 1.609 #: Number of kilometres per statute mile

# Maidenhead locator constants
LONGITUDE_FIELD = 20 #: Longitude field 1 multiplier
LATITUDE_FIELD = 10 #: Latitude field 1 multiplier
LONGITUDE_SQUARE = LONGITUDE_FIELD / 10 #: Longitude field 2 multiplier
LATITUDE_SQUARE = LATITUDE_FIELD / 10 #: Latitude field 2 multiplier
LONGITUDE_SUBSQUARE = LONGITUDE_SQUARE / 24 #: Longitude field 3 multiplier
LATITUDE_SUBSQUARE = LATITUDE_SQUARE / 24 #: Latitude field 3 multiplier
LONGITUDE_EXTSQUARE = LONGITUDE_SUBSQUARE / 10 #: Longitude field 4 multiplier
LATITUDE_EXTSQUARE = LATITUDE_SUBSQUARE / 10 #: Latitude field 4 multiplier

class FileFormatError(ValueError):
    """Error object for data parsing error

    >>> raise FileFormatError
    Traceback (most recent call last):
        ...
    FileFormatError: Unsupported data format.
    >>> raise FileFormatError("test site")
    Traceback (most recent call last):
        ...
    FileFormatError: Incorrect data format, if you're using a file downloaded
    from test site please report this to James Rowe <jnrowe@ukfsn.org>

    :since: 0.3.0

    :Ivariables:
        site
            Remote site name to display in error message

    """
    def __init__(self, site=None):
        """Initialise a new `FileFormatError` object

        :Parameters:
            site : `str`
                Remote site name to display in error message

        """
        super(FileFormatError, self).__init__()
        self.site = site

    def __str__(self):
        """Pretty printed error string

        :rtype: `str`
        :return: Human readable error string

        """
        if self.site:
            return ("Incorrect data format, if you're using a file downloaded "
                    "from %s please report this to %s" % (self.site,
                                                          __bug_report__))
        else:
            return "Unsupported data format."

#{ Implementation utilities

def value_or_empty(value):
    """Return an empty string for display when value is `None`

    >>> value_or_empty(None)
    ''
    >>> value_or_empty("test")
    'test'

    :Parameters:
        value : `None`, `str` or coercible to `str`
            Value to prepare for display
    :rtype: `str`
    :return: String representation of `value`

    """
    return value if value else ""

def repr_assist(obj, remap=None):
    """Helper function to simplify `__repr__` methods

    :Parameters:
        obj : Any
            Object to pull arg values for
        remap : `dict`
            Arg pairs to remap before output

    """
    if not remap:
        remap = {}
    data = []
    for arg in inspect.getargspec(getattr(obj.__class__, '__init__'))[0]:
        if arg == "self":
            continue
        elif arg in remap:
            value = remap[arg]
        else:
            try:
                value = getattr(obj, arg)
            except AttributeError:
                value = getattr(obj, "_%s" % arg)
        if isinstance(value, (type(None), list, basestring, datetime.date,
                              datetime.time)):
            data.append(repr(value))
        else:
            data.append(str(value))
    return obj.__class__.__name__ + '(' + ", ".join(data) + ')'

def prepare_read(data):
    """Prepare various input types for parsing

    >>> prepare_read(open("real_file"))
    ['This is a test file-type object\\n']
    >>> test_list = ['This is a test list-type object', 'with two elements']
    >>> prepare_read(test_list)
    ['This is a test list-type object', 'with two elements']    

    :Parameters:
        data : `file` like object, `list`, `str`
            Data to read
    :rtype: `list`
    :return: List suitable for parsing
    :raise TypeError: Invalid value for data

    """
    if hasattr(data, "readlines"):
        data = data.readlines()
    elif isinstance(data, list):
        pass
    elif isinstance(data, basestring):
        data = open(data).readlines()
    else:
        raise TypeError("Unable to handle data of type `%s`" % type(data))
    return data

def prepare_csv_read(data, field_names, *args, **kwargs):
    """Prepare various input types for CSV parsing

    >>> list(prepare_csv_read(open("real_file.csv"),
    ...                       ("type", "bool", "string")))
    [{'bool': 'true', 'type': 'file', 'string': 'test'}]
    >>> test_list = ['James,Rowe', 'ell,caro']
    >>> list(prepare_csv_read(test_list, ("first", "last")))
    [{'last': 'Rowe', 'first': 'James'}, {'last': 'caro', 'first': 'ell'}]

    :Parameters:
        data : `file` like object, `list`, `str`
            Data to read
        field_names : `tuple` of `str`
            Ordered names to assign to fields
    :rtype: `csv.DictReader`
    :return: CSV reader suitable for parsing
    :raise TypeError: Invalid value for data

    """
    if hasattr(data, "readlines") or isinstance(data, list):
        pass
    elif isinstance(data, basestring):
        data = open(data)
    else:
        raise TypeError("Unable to handle data of type `%s'" % type(data))
    return csv.DictReader(data, field_names, *args, **kwargs)

def prepare_xml_read(data):
    """Prepare various input types for XML parsing

    >>> prepare_xml_read(open("real_file.xml")).find("tag").text
    'This is a test file-type object'
    >>> test_list = ['<xml>', '<tag>This is a test list</tag>', '</xml>']
    >>> prepare_xml_read(test_list).find("tag").text
    'This is a test list'

    :Parameters:
        data : `file` like object, `list`, `str`
            Data to read
    :rtype: `ET.ElementTree`
    :return: Tree suitable for parsing
    :raise TypeError: Invalid value for data

    """
    if hasattr(data, "readlines"):
        data = ET.parse(data)
    elif isinstance(data, list):
        data = ET.fromstring("".join(data))
    elif isinstance(data, basestring):
        data = ET.parse(open(data))
    else:
        raise TypeError("Unable to handle data of type `%s`"
                        % type(data))
    return data

#}

#{ Angle conversion utilities

def to_dms(angle, style="dms"):
    """Convert decimal angle to degrees, minutes and possibly seconds

    >>> to_dms(52.015)
    (52, 0, 54.0)
    >>> to_dms(-0.221)
    (0, -13, -15.600000000000023)
    >>> to_dms(-0.221, style="dm")
    (0, -13.26)
    >>> to_dms(-0.221, style=None)
    Traceback (most recent call last):
        ...
    ValueError: Unknown style type `None'

    :Parameters:
        angle : `float` or coercible to `float`
            Angle to convert
        style : `str`
            Return fractional or whole minutes values
    :rtype: `tuple` of `int` objects for values
    :return: Angle converted to degrees, minutes and possibly seconds
    :raise ValueError: Unknown value for `style`

    """
    sign = 1 if angle >= 0 else -1
    angle = abs(angle) * 3600
    minutes, seconds = divmod(angle, 60)
    degrees, minutes = divmod(minutes, 60)
    if style == "dms":
        return tuple([sign * abs(i) for i in int(degrees), int(minutes),
                                             seconds])
    elif style == "dm":
        return tuple([sign * abs(i) for i in int(degrees),
                                             (minutes + seconds / 60)])
    else:
        raise ValueError("Unknown style type `%s'" % style)

def to_dd(degrees, minutes, seconds=0):
    """Convert degrees, minutes and optionally seconds to decimal angle

    >>> "%.3f" % to_dd(52, 0, 54)
    '52.015'
    >>> "%.3f" % to_dd(0, -13, -15)
    '-0.221'
    >>> "%.3f" % to_dd(0, -13.25)
    '-0.221'

    :Parameters:
        degrees : `float` or coercible to `float`
            Number of degrees
        minutes : `float` or coercible to `float`
            Number of minutes
        seconds : `float` or coercible to `float`
            Number of seconds
    :rtype: `float`
    :return: Angle converted to decimal degrees

    """
    sign = -1 if any([i < 0 for i in degrees, minutes, seconds]) else 1
    return sign * (abs(degrees) + abs(minutes) / 60 + abs(seconds) / 3600)

def __chunk(segment):
    """Generate a tuple of compass direction names

    :Parameters:
        segment : `int`
            Compass segment to generate names for
    :rtype: `tuple`
    :return: Direction names for compass segment

    """
    names = ("north", "east", "south", "west", "north")
    if segment % 2 == 0:
        return (names[segment].capitalize(),
                "%s-%s-%s" % (names[segment].capitalize(), names[segment],
                              names[segment+1]),
                "%s-%s" % (names[segment].capitalize(), names[segment+1]),
                "%s-%s-%s" % (names[segment+1].capitalize(), names[segment],
                              names[segment+1]))
    else:
        return (names[segment].capitalize(),
                "%s-%s-%s" % (names[segment].capitalize(), names[segment+1],
                              names[segment]),
                "%s-%s" % (names[segment+1].capitalize(), names[segment]),
                "%s-%s-%s" % (names[segment+1].capitalize(), names[segment+1],
                              names[segment]))
COMPASS_NAMES = reduce(add, map(__chunk, range(4)))

def angle_to_name(angle, segments=8, abbr=False):
    """Convert angle in to direction name

    >>> angle_to_name(0)
    'North'
    >>> angle_to_name(360)
    'North'
    >>> angle_to_name(45)
    'North-east'
    >>> angle_to_name(292)
    'West'
    >>> angle_to_name(293)
    'North-west'
    >>> angle_to_name(0, 4)
    'North'
    >>> angle_to_name(360, 16)
    'North'
    >>> angle_to_name(45, 4, True)
    'NE'
    >>> angle_to_name(292, 16, True)
    'WNW'

    :Parameters:
        angle : `float` or coercible to `float`
            Angle in degrees to convert to direction name
        segments : `int`
            Number of segments to split compass in to
        abbr : `bool`
            Whether to return abbreviated direction string
    :rtype: `str`
    :return: Direction name for `angle`

    """
    if segments == 4:
        string = COMPASS_NAMES[int((angle + 45) / 90) % 4 * 2]
    elif segments == 8:
        string = COMPASS_NAMES[int((angle + 22.5) / 45) % 8 * 2]
    elif segments == 16:
        string = COMPASS_NAMES[int((angle + 11.25) / 22.5) % 16]
    else:
        raise ValueError("Segments parameter must be 4, 8 or 16 not `%s'"
                         % segments)
    if abbr:
        return "".join(i[0].capitalize() for i in string.split("-"))
    else:
        return string

#}

#{ Coordinate conversion utilities

def from_iso6709(coordinates):
    """Parse ISO 6709 coordinate strings

    This function will parse ISO 6709-1983(E) "Standard representation of
    latitude, longitude and altitude for geographic point locations" elements.
    Unfortunately, the standard is rather convoluted and this implementation is
    incomplete, but it does support most of the common formats in the wild.

    The W3C has a simplified profile for ISO 6709 in `Latitude, Longitude and
    Altitude format for geospatial information
    <http://www.w3.org/2005/Incubator/geo/Wiki/LatitudeLongitudeAltitude>`__.
    It unfortunately hasn't received widespread support as yet, but hopefully it
    will grow just as the `simplified ISO 8601 profile
    <http://www.w3.org/2005/Incubator/geo/Wiki/LatitudeLongitudeAltitude>`__
    has.

    :see: `to_iso6709`

    The following tests are from the examples contained in the `wikipedia
    ISO 6709 page <http://en.wikipedia.org/wiki/ISO_6709>`__.

    >>> from_iso6709("+00-025/") # Atlantic Ocean
    (0.0, -25.0, None)
    >>> from_iso6709("+46+002/") # France
    (46.0, 2.0, None)
    >>> from_iso6709("+4852+00220/") # Paris
    (48.866666666666667, 2.3333333333333335, None)
    >>> from_iso6709("+48.8577+002.295/") # Eiffel Tower
    (48.857700000000001, 2.2949999999999999, None)
    >>> from_iso6709("+27.5916+086.5640+8850/") # Mount Everest
    (27.5916, 86.563999999999993, 8850.0)
    >>> from_iso6709("+90+000/") # North Pole
    (90.0, 0.0, None)
    >>> from_iso6709("+00-160/") # Pacific Ocean
    (0.0, -160.0, None)
    >>> from_iso6709("-90+000+2800/") # South Pole
    (-90.0, 0.0, 2800.0)
    >>> from_iso6709("+38-097/") # United States
    (38.0, -97.0, None)
    >>> from_iso6709("+40.75-074.00/") # New York City
    (40.75, -74.0, None)
    >>> from_iso6709("+40.6894-074.0447/") # Statue of Liberty
    (40.689399999999999, -74.044700000000006, None)

    The following tests are from the `Latitude, Longitude and Altitude format
    for geospatial information
    <http://www.w3.org/2005/Incubator/geo/Wiki/LatitudeLongitudeAltitude>`__
    page.

    >>> from_iso6709("+27.5916+086.5640+8850/") # Mount Everest
    (27.5916, 86.563999999999993, 8850.0)
    >>> from_iso6709("-90+000+2800/") # South Pole
    (-90.0, 0.0, 2800.0)
    >>> from_iso6709("+40.75-074.00/") # New York City
    (40.75, -74.0, None)
    >>> from_iso6709("+352139+1384339+3776/") # Mount Fuji
    (35.360833333333332, 138.72749999999999, 3776.0)
    >>> from_iso6709("+35.658632+139.745411/") # Tokyo Tower
    (35.658631999999997, 139.74541099999999, None)
    >>> from_iso6709("+35.658632+1/") # Broken
    Traceback (most recent call last):
        ...
    ValueError: Incorrect format for longitude `+1'

    :Parameters:
        coordinates : `str`
            ISO 6709 coordinates string
    :rtype: `tuple`
    :return: A tuple consisting of latitude and longitude in degrees, along with
        the elevation in metres
    :raise ValueError: Input string is not ISO 6709 compliant
    :raise ValueError: Invalid value for latitude
    :raise ValueError: Invalid value for longitude

"""
    matches = re.match(r'^([-+][\d\.]+)([-+][\d\.]+)([+-][\d\.]+)?/$',
                       coordinates)
    try:
        latitude, longitude, altitude = matches.groups()
    except:
        raise ValueError("Incorrect format for string")
    sign = 1 if latitude[0] == "+" else -1
    latitude_head = len(latitude.split(".")[0])
    if latitude_head == 3: # ±DD(.D{1,4})?
        latitude = float(latitude)
    elif latitude_head == 5: # ±DDMM(.M{1,4})?
        latitude = float(latitude[:3]) + (sign * (float(latitude[3:]) / 60))
    elif latitude_head == 7: # ±DDMMSS(.S{1,4})?
        latitude = float(latitude[:3]) + (sign * (float(latitude[3:5]) / 60)) \
                   + (sign * (float(latitude[5:]) / 3600))
    else:
        raise ValueError("Incorrect format for latitude `%s'" % latitude)
    sign = 1 if longitude[0] == "+" else -1
    longitude_head = len(longitude.split(".")[0])
    if longitude_head == 4: # ±DDD(.D{1,4})?
        longitude = float(longitude)
    elif longitude_head == 6: # ±DDDMM(.M{1,4})?
        longitude = float(longitude[:4]) + (sign * (float(longitude[4:]) / 60))
    elif longitude_head == 8: # ±DDDMMSS(.S{1,4})?
        longitude = float(longitude[:4]) \
                    + (sign * (float(longitude[4:6]) / 60)) \
                    + (sign * (float(longitude[6:]) / 3600))
    else:
        raise ValueError("Incorrect format for longitude `%s'" % longitude)
    if altitude:
        altitude = float(altitude)
    return latitude, longitude, altitude

def to_iso6709(latitude, longitude, altitude=None, format="dd", precision=4):
    """Produce ISO 6709 coordinate strings

    This function will produce ISO 6709-1983(E) "Standard representation of
    latitude, longitude and altitude for geographic point locations" elements.

    :see: `from_iso6709`

    The following tests are from the examples contained in the `wikipedia ISO
    6709 page <http://en.wikipedia.org/wiki/ISO_6709>`__.

    >>> to_iso6709(0.0, -25.0, None, "d") # Atlantic Ocean
    '+00-025/'
    >>> to_iso6709(46.0, 2.0, None, "d") # France
    '+46+002/'
    >>> to_iso6709(48.866666666666667, 2.3333333333333335, None, "dm") # Paris
    '+4852+00220/'
    >>> # The following test is skipped, because the example from wikipedia uses
    >>> # differing precision widths for latitude and longitude. Also, that
    >>> # degree of formatting flexibility is not seen anywhere else and adds
    >>> # very little.
    >>> to_iso6709(48.857700000000001, 2.2949999999999999, None) # Eiffel Tower # doctest: +SKIP
    '+48.8577+002.295/'
    >>> to_iso6709(27.5916, 86.563999999999993, 8850.0) # Mount Everest
    '+27.5916+086.5640+8850/'
    >>> to_iso6709(90.0, 0.0, None, "d") # North Pole
    '+90+000/'
    >>> to_iso6709(0.0, -160.0, None, "d") # Pacific Ocean
    '+00-160/'
    >>> to_iso6709(-90.0, 0.0, 2800.0, "d") # South Pole
    '-90+000+2800/'
    >>> to_iso6709(38.0, -97.0, None, "d") # United States
    '+38-097/'
    >>> to_iso6709(40.75, -74.0, None, precision=2) # New York City
    '+40.75-074.00/'
    >>> to_iso6709(40.689399999999999, -74.044700000000006, None) # Statue of Liberty
    '+40.6894-074.0447/'

    The following tests are from the `Latitude, Longitude and Altitude format
    for geospatial information
    <http://www.w3.org/2005/Incubator/geo/Wiki/LatitudeLongitudeAltitude>`__
    page.

    >>> to_iso6709(27.5916, 86.563999999999993, 8850.0) # Mount Everest
    '+27.5916+086.5640+8850/'
    >>> to_iso6709(-90.0, 0.0, 2800.0, "d") # South Pole
    '-90+000+2800/'
    >>> to_iso6709(40.75, -74.0, None, precision=2) # New York City
    '+40.75-074.00/'
    >>> to_iso6709(35.360833333333332, 138.72749999999999, 3776.0, "dms") # Mount Fuji
    '+352139+1384339+3776/'
    >>> to_iso6709(35.658631999999997, 139.74541099999999, None, precision=6) # Tokyo Tower
    '+35.658632+139.745411/'

    :Parameters:
        latitude : `float` or coercible to `float`
            Location's latitude
        longitude : `float` or coercible to `float`
            Location's longitude
        altitude : `float` or coercible to `float`
            Location's altitude
        format : `str`
            Format type for string
        precision : `int`
            Latitude/longitude precision
    :rtype: `str`
    :return: ISO 6709 coordinates string
    :raise ValueError: Unknown value for `format`

    """
    text = []
    if format == "d":
        text.append("%+03i%+04i" % (latitude, longitude))
    elif format == "dd":
        text.append("%+0*.*f%+0*.*f" % (precision + 4, precision, latitude,
                                        precision + 5, precision, longitude))
    elif format in ("dm", "dms"):
        if format == "dm":
            latitude_dms = to_dms(latitude, "dm")
            longitude_dms = to_dms(longitude, "dm")
        elif format == "dms":
            latitude_dms = to_dms(latitude)
            longitude_dms = to_dms(longitude)
        latitude_sign = "-" if any([i < 0 for i in latitude_dms]) else "+"
        latitude_dms = tuple([abs(i) for i in latitude_dms])
        longitude_sign = "-" if any([i < 0 for i in longitude_dms]) else "+"
        longitude_dms = tuple([abs(i) for i in longitude_dms])
        if format == "dm":
            text.append("%s%02i%02i" % ((latitude_sign, ) + latitude_dms))
            text.append("%s%03i%02i" % ((longitude_sign, ) + longitude_dms))
        elif format == "dms":
            text.append("%s%02i%02i%02i" % ((latitude_sign, ) + latitude_dms))
            text.append("%s%03i%02i%02i" % ((longitude_sign, ) + longitude_dms))
    else:
        raise ValueError("Unknown format type `%s'" % format)
    if altitude and int(altitude) == altitude:
        text.append("%+i" % altitude)
    elif altitude:
        text.append("%+.3f" % altitude)
    text.append("/")
    return "".join(text)

def angle_to_distance(angle, units="metric"):
    """Convert angle in to distance along a great circle

    >>> "%.3f" % angle_to_distance(1)
    '111.125'
    >>> "%i" % angle_to_distance(360, "imperial")
    '24863'
    >>> "%i" % angle_to_distance(1.0/60, "nautical")
    '1'
    >>> "%i" % angle_to_distance(10, "baseless")
    Traceback (most recent call last):
        ...
    ValueError: Unknown units type `baseless'

    :Parameters:
        angle : `float` or coercible to `float`
            Angle in degrees to convert to distance
        units : `str`
            Unit type to be used for distances
    :rtype: `float`
    :return: Distance in `units`
    :raise ValueError: Unknown value for `units`

    """
    distance = math.radians(angle) * BODY_RADIUS

    if units in ("km", "metric"):
        return distance
    elif units in ("sm", "imperial", "US customary"):
        return distance / STATUTE_MILE
    elif units in ("nm", "nautical"):
        return distance / NAUTICAL_MILE
    else:
        raise ValueError("Unknown units type `%s'" % units)

def distance_to_angle(distance, units="metric"):
    """Convert a distance in to an angle along a great circle

    >>> "%.3f" % round(distance_to_angle(111.212))
    '1.000'
    >>> "%i" % round(distance_to_angle(24882, "imperial"))
    '360'
    >>> "%i" % round(distance_to_angle(60, "nautical"))
    '1'

    :Parameters:
        distance : `float` or coercible to `float`
            Distance to convert to degrees
        units : `str`
            Unit type to be used for distances
    :rtype: `float`
    :return: Angle in degrees
    :raise ValueError: Unknown value for `units`

    """
    if units in ("km", "metric"):
        pass
    elif units in ("sm", "imperial", "US customary"):
        distance *= STATUTE_MILE
    elif units in ("nm", "nautical"):
        distance *= NAUTICAL_MILE
    else:
        raise ValueError("Unknown units type `%s'" % units)

    return math.degrees(distance / BODY_RADIUS)

def from_grid_locator(locator):
    """Calculate geodesic latitude/longitude from Maidenhead locator

    >>> "%.3f, %.3f" % from_grid_locator("BL11bh16")
    '21.319, -157.904'
    >>> "%.3f, %.3f" % from_grid_locator("IO92va")
    '52.021, -0.208'
    >>> "%.3f, %.3f" % from_grid_locator("IO92")
    '52.021, -1.958'

    :Parameters:
        locator : `str`
            Maidenhead locator string
    :rtype: `tuple` of `float` objects
    :return: Geodesic latitude and longitude values
    :raise ValueError: Incorrect grid locator length
    :raise ValueError: Invalid values in locator string

    """
    if not len(locator) in (4, 6, 8):
        raise ValueError("Locator must be 4, 6 or 8 characters long `%s'"
                         % locator)

    # Convert the locator string to a list, because we need it to be mutable to
    # munge the values
    locator = list(locator)

    # Convert characters to numeric value, fields are always uppercase
    locator[0] = ord(locator[0]) - 65
    locator[1] = ord(locator[1]) - 65

    # Values for square are always integers
    locator[2] = int(locator[2])
    locator[3] = int(locator[3])

    if len(locator) >= 6:
        # Some people use uppercase for the subsquare data, in spite of
        # lowercase being the accepted style, so handle that too.
        locator[4] = ord(locator[4].lower()) - 97
        locator[5] = ord(locator[5].lower()) - 97

    if len(locator) == 8:
        # Extended square values are always integers
        locator[6] = int(locator[6])
        locator[7] = int(locator[7])

    # Check field values within 'A'(0) to 'R'(17), and square values are within
    # 0 to 9
    if not 0 <= locator[0] <= 17 \
       or not 0 <= locator[1] <= 17 \
       or not 0 <= locator[2] <= 9 \
       or not 0 <= locator[3] <= 9:
        raise ValueError("Invalid values in locator `%s'" % locator)

    # Check subsquare values are within 'a'(0) to 'x'(23)
    if len(locator) >= 6:
        if not 0 <= locator[4] <= 23 \
           or not 0 <= locator[5] <= 23:
            raise ValueError("Invalid values in locator `%s'" % locator)

    # Extended square values must be within 0 to 9
    if len(locator) == 8:
        if not 0 <= locator[6] <= 9 \
           or not 0 <= locator[7] <= 9:
            raise ValueError("Invalid values in locator `%s'" % locator)

    longitude = LONGITUDE_FIELD * locator[0] \
                + LONGITUDE_SQUARE * locator[2]
    latitude = LATITUDE_FIELD * locator[1] \
               + LATITUDE_SQUARE * locator[3]

    if len(locator) >= 6:
        longitude += LONGITUDE_SUBSQUARE * locator[4]
        latitude += LATITUDE_SUBSQUARE * locator[5]

    if len(locator) == 8:
        longitude += LONGITUDE_EXTSQUARE * locator[6] + LONGITUDE_EXTSQUARE / 2
        latitude  += LATITUDE_EXTSQUARE * locator[7] + LATITUDE_EXTSQUARE / 2
    else:
        longitude += LONGITUDE_EXTSQUARE * 5
        latitude  += LATITUDE_EXTSQUARE * 5

    # Rebase longitude and latitude to normal geodesic
    longitude -= 180
    latitude -= 90

    return latitude, longitude

def to_grid_locator(latitude, longitude, precision="square"):
    """Calculate Maidenhead locator from latitude and longitude

    >>> to_grid_locator(21.319, -157.904, "extsquare")
    'BL11bh16'
    >>> to_grid_locator(52.021, -0.208, "subsquare")
    'IO92va'
    >>> to_grid_locator(52.021, -1.958)
    'IO92'

    :Parameters:
        latitude : `float`
            Position's latitude
        longitude : `float`
            Position's longitude
        precision : `str`
            Precision with which generate locator string
    :rtype: `str`
    :return: Maidenhead locator for latitude and longitude
    :raise ValueError: Invalid precision identifier
    :raise ValueError: Invalid latitude or longitude value

    """
    if not precision in ("square", "subsquare", "extsquare"):
        raise ValueError("Unsupported precision value `%s'" % precision)

    if not -90 <= latitude <= 90:
        raise ValueError("Invalid latitude value `%f'" % latitude)
    if not -180 <= longitude <= 180:
        raise ValueError("Invalid longitude value `%f'" % longitude)

    latitude  += 90.0
    longitude += 180.0

    locator = []

    field = int(longitude / LONGITUDE_FIELD)
    locator.append(chr(field + 65))
    longitude -= field * LONGITUDE_FIELD

    field = int(latitude / LATITUDE_FIELD)
    locator.append(chr(field + 65))
    latitude -= field * LATITUDE_FIELD

    square = int(longitude / LONGITUDE_SQUARE)
    locator.append(str(square))
    longitude -= square * LONGITUDE_SQUARE

    square = int(latitude / LATITUDE_SQUARE)
    locator.append(str(square))
    latitude -= square * LATITUDE_SQUARE

    if precision in ("subsquare", "extsquare"):
        subsquare = int(longitude / LONGITUDE_SUBSQUARE)
        locator.append(chr(subsquare + 97))
        longitude -= subsquare * LONGITUDE_SUBSQUARE

        subsquare = int(latitude / LATITUDE_SUBSQUARE)
        locator.append(chr(subsquare + 97))
        latitude -= subsquare * LATITUDE_SUBSQUARE

    if precision == "extsquare":
        extsquare = int(longitude / LONGITUDE_EXTSQUARE)
        locator.append(str(extsquare))

        extsquare = int(latitude / LATITUDE_EXTSQUARE)
        locator.append(str(extsquare))

    return "".join(locator)

def parse_location(location):
    """Parse latitude and longitude from string location

    >>> "%.3f;%.3f" % parse_location("52.015;-0.221")
    '52.015;-0.221'
    >>> "%.3f;%.3f" % parse_location("52.015,-0.221")
    '52.015;-0.221'
    >>> "%.3f;%.3f" % parse_location("52.015 -0.221")
    '52.015;-0.221'
    >>> "%.3f;%.3f" % parse_location("52.015N 0.221W")
    '52.015;-0.221'
    >>> "%.3f;%.3f" % parse_location("52.015 N 0.221 W")
    '52.015;-0.221'
    >>> "%.3f;%.3f" % parse_location("52d00m54s N 0d13m15s W")
    '52.015;-0.221'
    >>> "%.3f;%.3f" % parse_location("52d0m54s N 000d13m15s W")
    '52.015;-0.221'
    >>> "%.3f;%.3f" % parse_location('''52d0'54" N 000d13'15" W''')
    '52.015;-0.221'

    :Parameters:
        location : `str`
            String to parse
    :rtype: `tuple` of `float` objects
    :return: Latitude and longitude of location

    """

    def split_dms(text, hemisphere):
        """Split degrees, minutes and seconds string

        :Parameters:
            text : `str`
                Text to split
        :rtype: `float`
        :return: Decimal degrees

        """
        out = []
        sect = []
        for i in text:
            if i.isdigit():
                sect.append(i)
            else:
                out.append(sect)
                sect = []
        degrees, minutes, seconds = [float("".join(i)) for i in out]
        if hemisphere in "SW":
            degrees, minutes, seconds = map(lambda x: -1 * x,
                                            (degrees, minutes, seconds))
        return to_dd(degrees, minutes, seconds)

    for sep in ";, ":
        chunks = location.split(sep)
        if len(chunks) == 2:
            if chunks[0].endswith("N"):
                latitude = float(chunks[0][:-1])
            elif chunks[0].endswith("S"):
                latitude = -1 * float(chunks[0][:-1])
            else:
                latitude = float(chunks[0])
            if chunks[1].endswith("E"):
                longitude = float(chunks[1][:-1])
            elif chunks[1].endswith("W"):
                longitude = -1 * float(chunks[1][:-1])
            else:
                longitude = float(chunks[1])
            return latitude, longitude
        elif len(chunks) == 4:
            if chunks[0].endswith(("s", '"')):
                latitude = split_dms(chunks[0], chunks[1])
            else:
                latitude = float(chunks[0])
                if chunks[1] == "S":
                    latitude = -1 * latitude
            if chunks[2].endswith(("s", '"')):
                longitude = split_dms(chunks[2], chunks[3])
            else:
                longitude = float(chunks[2])
                if chunks[3] == "W":
                    longitude = -1 * longitude
            return latitude, longitude
#}

#{ Solar event utilities

ZENITH = {
    # All values are specified in degrees!

    # Sunrise/sunset is defined as the moment the upper limb becomes visible,
    # taking in to account atmospheric refraction.  That is 34' for atmospheric
    # refraction and 16' for angle between the Sun's centre and it's upper limb,
    # resulting in a combined 50' below the horizon.
    #
    # We're totally ignoring how temperature and pressure change the amount of
    # atmospheric refraction, because their effects are drowned out by rounding
    # errors in the equation.
    None: -50/60,

    # Twilight definitions specify the angle in degrees of the Sun below the
    # horizon
    "civil": -6,
    "nautical": -12,
    "astronomical": -18,
} #: Sunrise/-set mappings from name to angle

def sun_rise_set(latitude, longitude, date, mode="rise", timezone=0,
                 zenith=None):
    """Calculate sunrise or sunset for a specific location

    This function calculates the time sunrise or sunset, or optionally the
    beginning or end of a specified twilight period.

    Source::

        Almanac for Computers, 1990
        published by Nautical Almanac Office
        United States Naval Observatory
        Washington, DC 20392

    >>> sun_rise_set(52.015, -0.221, datetime.date(2007, 6, 15))
    datetime.time(3, 40)
    >>> sun_rise_set(52.015, -0.221, datetime.date(2007, 6, 15), "set")
    datetime.time(20, 23)
    >>> sun_rise_set(52.015, -0.221, datetime.date(2007, 6, 15), timezone=60)
    datetime.time(4, 40)
    >>> sun_rise_set(52.015, -0.221, datetime.date(2007, 6, 15), "set", 60)
    datetime.time(21, 23)
    >>> sun_rise_set(52.015, -0.221, datetime.date(1993, 12, 11))
    datetime.time(7, 58)
    >>> sun_rise_set(52.015, -0.221, datetime.date(1993, 12, 11), "set")
    datetime.time(15, 50)
    >>> sun_rise_set(89, 0, datetime.date(2007, 12, 21))
    >>> sun_rise_set(52.015, -0.221, datetime.date(2007, 2, 21))
    datetime.time(7, 4)
    >>> sun_rise_set(52.015, -0.221, datetime.date(2007, 1, 21))
    datetime.time(7, 56)

    :Parameters:
        latitude : `float` or coercible to `float`
            Location's latitude
        longitude : `float` or coercible to `float`
            Location's longitude
        date : ``datetime.date``
            Calculate rise or set for given date
        mode : `str`
            Which time to calculate
        timezone : `int`
            Offset from UTC in minutes
        zenith : `None` or `str`
            Calculate rise/set events, or twilight times
    :rtype: ``datetime.time`` or `None`
    :return: The time for the given event in the specified timezone, or
        `None` if the event doesn't occur on the given date
    :raise ValueError: Unknown value for `mode`

    """
    if not date:
        date = datetime.date.today()

    zenith = ZENITH[zenith]

    # First calculate the day of the year
    # Thanks, datetime this would have been ugly without you!!!
    n = (date - datetime.date(date.year-1, 12, 31)).days

    # Convert the longitude to hour value and calculate an approximate time
    lngHour = longitude / 15

    if mode == "rise":
        t = n + ((6 - lngHour) / 24)
    elif mode == "set":
        t = n + ((18 - lngHour) / 24)
    else:
        raise ValueError("Unknown mode value `%s'" % mode)

    # Calculate the Sun's mean anomaly
    m = (0.9856 * t) - 3.289

    # Calculate the Sun's true longitude
    l = m + 1.916 * math.sin(math.radians(m)) + 0.020 \
        * math.sin(2 * math.radians(m)) + 282.634
    l = abs(l) % 360

    # Calculate the Sun's right ascension
    ra = math.degrees(math.atan(0.91764 * math.tan(math.radians(l))))

    # Right ascension value needs to be in the same quadrant as L
    lQuandrant = (math.floor(l / 90)) * 90
    raQuandrant = (math.floor(ra / 90)) * 90
    ra = ra + (lQuandrant - raQuandrant)

    # Right ascension value needs to be converted into hours
    ra = ra / 15

    # Calculate the Sun's declination
    sinDec = 0.39782 * math.sin(math.radians(l))
    cosDec = math.cos(math.asin(sinDec))

    # Calculate the Sun's local hour angle
    cosH = (math.radians(zenith) -
            (sinDec * math.sin(math.radians(latitude)))) \
           / (cosDec * math.cos(math.radians(latitude)))

    if cosH > 1:
        # The sun never rises on this location (on the specified date)
        return None
    if cosH < -1:
        # The sun never sets on this location (on the specified date)
        return None

    # Finish calculating H and convert into hours
    if mode == "rise":
        h = 360 - math.degrees(math.acos(cosH))
    else:
        h = math.degrees(math.acos(cosH))
    h = h / 15

    # Calculate local mean time of rising/setting
    T = h + ra - (0.06571 * t) - 6.622

    # Adjust back to UTC
    UT = T - lngHour

    # Convert UT value to local time zone of latitude/longitude
    localT = UT + timezone/60

    hour = int(localT)
    if hour == 0:
        minute = int(60 * localT)
    else:
        minute = int(60 * (localT % hour))
    if hour < 0:
        hour += 23
    elif hour > 23:
        hour = hour % 24
    if minute < 0:
        minute += 60
    return datetime.time(hour, minute)

def sun_events(latitude, longitude, date, timezone=0, zenith=None):
    """Convenience function for calculating sunrise and sunset

    >>> sun_events(52.015, -0.221, datetime.date(2007, 6, 15))
    (datetime.time(3, 40), datetime.time(20, 23))
    >>> sun_events(52.015, -0.221, datetime.date(2007, 6, 15), 60)
    (datetime.time(4, 40), datetime.time(21, 23))
    >>> sun_events(52.015, -0.221, datetime.date(1993, 12, 11))
    (datetime.time(7, 58), datetime.time(15, 50))
    >>> sun_events(52.015, -0.221, datetime.date(2007, 6, 15))
    (datetime.time(3, 40), datetime.time(20, 23))
    >>> sun_events(40.638611, -73.762222, datetime.date(2007, 6, 15)) # JFK
    (datetime.time(9, 23), datetime.time(0, 27))
    >>> sun_events(49.016666, -2.5333333, datetime.date(2007, 6, 15)) # CDG
    (datetime.time(4, 5), datetime.time(20, 16))
    >>> sun_events(35.549999, 139.78333333, datetime.date(2007, 6, 15)) # TIA
    (datetime.time(19, 25), datetime.time(9, 58))

    Civil twilight starts/ends when the Sun's center is 6 degrees below
    the horizon.

    >>> sun_events(52.015, -0.221, datetime.date(2007, 6, 15), zenith="civil")
    (datetime.time(2, 51), datetime.time(21, 12))
    >>> sun_events(40.638611, -73.762222, datetime.date(2007, 6, 15),
    ...            zenith="civil") # JFK
    (datetime.time(8, 50), datetime.time(1, 0))
    >>> sun_events(49.016666, -2.5333333, datetime.date(2007, 6, 15),
    ...            zenith="civil") # CDG
    (datetime.time(3, 22), datetime.time(20, 59))
    >>> sun_events(35.549999, 139.78333333, datetime.date(2007, 6, 15),
    ...            zenith="civil") # TIA
    (datetime.time(18, 55), datetime.time(10, 28))

    Nautical twilight starts/ends when the Sun's center is 12 degrees
    below the horizon.

    >>> sun_events(52.015, -0.221, datetime.date(2007, 6, 15),
    ...            zenith="nautical")
    (datetime.time(1, 32), datetime.time(22, 31))
    >>> sun_events(40.638611, -73.762222, datetime.date(2007, 6, 15),
    ...            zenith="nautical") # JFK
    (datetime.time(8, 7), datetime.time(1, 44))
    >>> sun_events(49.016666, -2.5333333, datetime.date(2007, 6, 15),
    ...            zenith="nautical") # CDG
    (datetime.time(2, 20), datetime.time(22, 1))
    >>> sun_events(35.549999, 139.78333333, datetime.date(2007, 6, 15),
    ...            zenith="nautical") # TIA
    (datetime.time(18, 18), datetime.time(11, 6))

    Astronomical twilight starts/ends when the Sun's centre is 18 degrees below
    the horizon.

    >>> sun_events(52.015, -0.221, datetime.date(2007, 6, 15),
    ...            zenith="astronomical")
    (None, None)
    >>> sun_events(40.638611, -73.762222, datetime.date(2007, 6, 15),
    ...            zenith="astronomical") # JFK
    (datetime.time(7, 14), datetime.time(2, 36))
    >>> sun_events(49.016666, -2.5333333, datetime.date(2007, 6, 15),
    ...            zenith="astronomical") # CDG
    (None, None)
    >>> sun_events(35.549999, 139.78333333, datetime.date(2007, 6, 15),
    ...            zenith="astronomical") # TIA
    (datetime.time(17, 35), datetime.time(11, 49))

    :Parameters:
        latitude : `float` or coercible to `float`
            Location's latitude
        longitude : `float` or coercible to `float`
            Location's longitude
        date : ``datetime.date``
            Calculate rise or set for given date
        timezone : `int`
            Offset from UTC in minutes
        zenith : `None` or `str`
            Calculate rise/set events, or twilight times
    :rtype: `tuple` of ``datetime.time``
    :return: The time for the given events in the specified timezone

    """
    return (sun_rise_set(latitude, longitude, date, "rise", timezone, zenith),
            sun_rise_set(latitude, longitude, date, "set", timezone, zenith))

#}

def dump_xearth_markers(markers, name="identifier"):
    """Generate an Xearth compatible marker file

    `dump_xearth_markers()` writes a simple `Xearth
    <http://www.cs.colorado.edu/~tuna/xearth/>`__ marker file from a dictionary
    of `trigpoints.Trigpoint` objects.

    It expects a dictionary in one of the following formats. For support of
    `Trigpoint` that is::

        {500936: Trigpoint(52.066035, -0.281449, 37.0, "Broom Farm"),
         501097: Trigpoint(52.010585, -0.173443, 97.0, "Bygrave"),
         505392: Trigpoint(51.910886, -0.186462, 136.0, "Sish Lane")}

    And generates output of the form::

        52.066035 -0.281449 "500936" # Broom Farm, alt 37m
        52.010585 -0.173443 "501097" # Bygrave, alt 97m
        51.910886 -0.186462 "205392" # Sish Lane, alt 136m

    Or similar to the following if the `name` parameter is set to `name`::

        52.066035 -0.281449 "Broom Farm" # 500936 alt 37m
        52.010585 -0.173443 "Bygrave" # 501097 alt 97m
        51.910886 -0.186462 "Sish Lane" # 205392 alt 136m

    Point objects should be provided in the following format::

        {"Broom Farm": Point(52.066035, -0.281449),
         "Bygrave": Point(52.010585, -0.173443),
         "Sish Lane": Point(51.910886, -0.186462)}

    And generates output of the form::

        52.066035 -0.281449 "Broom Farm"
        52.010585 -0.173443 "Bygrave"
        51.910886 -0.186462 "Sish Lane"

    :note: `xplanet <http://xplanet.sourceforge.net/>`__ also supports xearth
        marker files, and as such can use the output from this function.

    >>> from upoints.trigpoints import Trigpoint
    >>> markers = {
    ...     500936: Trigpoint(52.066035, -0.281449, 37.000000, "Broom Farm"),
    ...     501097: Trigpoint(52.010585, -0.173443, 97.000000, "Bygrave"),
    ...     505392: Trigpoint(51.910886, -0.186462, 136.000000, "Sish Lane")
    ... }
    >>> print("\\n".join(dump_xearth_markers(markers)))
    52.066035 -0.281449 "500936" # Broom Farm, alt 37m
    52.010585 -0.173443 "501097" # Bygrave, alt 97m
    51.910886 -0.186462 "505392" # Sish Lane, alt 136m
    >>> print("\\n".join(dump_xearth_markers(markers, "name")))
    52.066035 -0.281449 "Broom Farm" # 500936, alt 37m
    52.010585 -0.173443 "Bygrave" # 501097, alt 97m
    51.910886 -0.186462 "Sish Lane" # 505392, alt 136m
    >>> print("\\n".join(dump_xearth_markers(markers, "falseKey")))
    Traceback (most recent call last):
        ...
    ValueError: Unknown name type `falseKey'

    >>> from upoints.point import Point
    >>> points = {
    ...     "Broom Farm": Point(52.066035, -0.281449),
    ...     "Bygrave": Point(52.010585, -0.173443),
    ...     "Sish Lane": Point(51.910886, -0.186462)
    ... }
    >>> print("\\n".join(dump_xearth_markers(points)))
    52.066035 -0.281449 "Broom Farm"
    52.010585 -0.173443 "Bygrave"
    51.910886 -0.186462 "Sish Lane"

    :see: `upoints.xearth.Xearths.import_locations`

    :Parameters:
        markers : `dict`
            Dictionary of identifer keys, with `Trigpoint` values
        name : `str`
            Value to use as Xearth display string
    :rtype: `list`
    :return: List of strings representing an Xearth marker file
    :raise ValueError: Unsupported value for `name`

    """
    output = []
    for identifier, point in markers.items():
        line = ["%f %f " % (point.latitude, point.longitude), ]
        if hasattr(point, 'name') and point.name:
            if name == "identifier":
                line.append('"%s" # %s' % (identifier, point.name))
            elif name == "name":
                line.append('"%s" # %s' % (point.name, identifier))
            elif name == "comment":
                line.append('"%s" # %s' % (identifier, point.comment))
            else:
                raise ValueError("Unknown name type `%s'" % name)
            if hasattr(point, 'altitude') and point.altitude:
                line.append(", alt %im" % point.altitude)
        else:
            line.append('"%s"' % identifier)
        output.append("".join(line))
    # Return the list sorted on the marker name
    return sorted(output, key=lambda x: x.split()[2])

def calc_radius(latitude, ellipsoid="WGS84"):
    """Calculate earth radius for a given latitude

    This function is most useful when dealing with datasets that are very
    localised and require the accuracy of an ellipsoid model without the
    complexity of code necessary to actually use one.  The results are meant to
    be used as a `BODY_RADIUS` replacement when the simple geocentric value is
    not good enough.

    The original use for `calc_radius` is to set a more accurate radius value
    for use with trigpointing databases that are keyed on the OSGB36 datum, but
    it has been expanded to cover other ellipsoids.

    >>> calc_radius(52.015)
    6375.1660253118571
    >>> calc_radius(0)
    6335.4387009096872
    >>> calc_radius(90)
    6399.5939421215426
    >>> calc_radius(52.015, "FAI sphere")
    6371.0
    >>> calc_radius(0, "Airy (1830)")
    6335.0221785420217
    >>> calc_radius(90, "International")
    6399.9365538714392

    :Parameters:
        latitude : `float`
            Latitude to calculate earth radius for
        ellipsoid : `tuple` of `float` objects
            Ellipsoid model to use for calculation
    :rtype: `float`
    :return: Approximated Earth radius at the given latitude

    """

    ellipsoids = {
        "Airy (1830)": (6377.563, 6356.257), # Ordnance Survey default
        "Bessel": (6377.397, 6356.079),
        "Clarke (1880)": (6378.249145, 6356.51486955),
        "FAI sphere": (6371, 6371), # Idealised
        "GRS-67": (6378.160, 6356.775),
        "International": (6378.388, 6356.912),
        "Krasovsky": (6378.245, 6356.863),
        "NAD27": (6378.206, 6356.584),
        "WGS66": (6378.145, 6356.758),
        "WGS72": (6378.135, 6356.751),
        "WGS84": (6378.137, 6356.752), # GPS default
    }

    # Equatorial radius, polar radius
    major, minor = ellipsoids[ellipsoid]
    # eccentricity of the ellipsoid
    eccentricity = 1 - (minor**2 / major**2)

    sl = math.sin(math.radians(latitude))
    return (major * (1 - eccentricity)) / (1 - eccentricity * sl**2) ** 1.5

