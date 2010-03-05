#
# vim: set sw=4 sts=4 et tw=80 fileencoding=utf-8:
#
"""trigpoints - Imports trigpoint marker files"""
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

from functools import partial
from itertools import ifilter

from upoints import (point, utils)

class Trigpoint(point.Point):
    """
    Class for representing a location from a trigpoint marker file

    :warning: Although this class stores and presents the representation of
        altitude it doesn't take it in to account when making calculations.  For
        example, consider a point at the base of Mount Everest and a point at
        the peak of Mount Everest the actual distance travelled between the two
        would be larger than the reported value calculated at ground level.

    :since: 0.2.0

    :Ivariables:
        latitude
            Location's latitude
        longitude
            Locations's longitude
        altitude
            Location's altitude
        name
            Location's name
        identity
            Database identifier, if known
    """

    __slots__ = ('altitude', 'name', 'identity')

    def __init__(self, latitude, longitude, altitude, name=None, identity=None):
        """
        Initialise a new `Trigpoint` object

        >>> Trigpoint(52.010585, -0.173443, 97.0, "Bygrave")
        Trigpoint(52.010585, -0.173443, 97.0, 'Bygrave', None)

        :Parameters:
            latitude : `float` or coercible to `float`
                Location's latitude
            longitude : `float` or coercible to `float`
                Location's longitude
            altitude : `float` or coercible to `float`
                Location's altitude
            name : `str`
                Name for location
            identity : `int`
                Database identifier, if known
        """
        super(Trigpoint, self).__init__(latitude, longitude)
        self.altitude = altitude
        self.name = name
        self.identity = identity

    def __str__(self, mode="dms"):
        """
        Pretty printed location string

        >>> print(Trigpoint(52.010585, -0.173443, 97.0))
        52°00'38"N, 000°10'24"W alt 97m
        >>> print(Trigpoint(52.010585, -0.173443, 97.0).__str__(mode="dd"))
        N52.011°; W000.173° alt 97m
        >>> print(Trigpoint(52.010585, -0.173443, 97.0).__str__(mode="dm"))
        52°00.64'N, 000°10.41'W alt 97m
        >>> print(Trigpoint(52.010585, -0.173443, 97.0, "Bygrave"))
        Bygrave (52°00'38"N, 000°10'24"W alt 97m)

        :Parameters:
            mode : `str`
                Coordinate formatting system to use
        :rtype: `str`
        :return: Human readable string representation of `Trigpoint` object
        """
        location = [super(Trigpoint, self).__str__(mode), ]
        if self.altitude:
            location.append("alt %im" % self.altitude)

        if self.name:
            return "%s (%s)" % (self.name, " ".join(location))
        else:
            return " ".join(location)


class Trigpoints(point.KeyedPoints):
    """
    Class for representing a group of `Trigpoint` objects

    :since: 0.5.1
    """

    def __init__(self, marker_file=None):
        """
        Initialise a new `Trigpoints` object
        """
        super(Trigpoints, self).__init__()
        if marker_file:
            self.import_locations(marker_file)

    def import_locations(self, marker_file):
        """
        Import trigpoint database files

        `import_locations()` returns a dictionary with keys containing the
        trigpoint identifier, and values that are `Trigpoint` objects.

        It expects trigpoint marker files in the format provided at
        `alltrigs-wgs84.txt <http://www.haroldstreet.org.uk/trigpoints.php>`__,
        which is the following format::

            H  SOFTWARE NAME & VERSION
            I  GPSU 4.04,
            S SymbolSet=0
            ...
            W,500936,N52.066035,W000.281449,    37.0,Broom Farm
            W,501097,N52.010585,W000.173443,    97.0,Bygrave
            W,505392,N51.910886,W000.186462,   136.0,Sish Lane

        Any line not consisting of 6 comma separated fields will be ignored.
        The reader uses `Python <http://www.python.org/>`__'s `csv` module, so
        alternative whitespace formatting should have no effect.  The above file
        processed by `import_locations()` will return the following `dict`
        object::

            {500936: point.Point(52.066035, -0.281449, 37.0, "Broom Farm"),
             501097: point.Point(52.010585, -0.173443, 97.0, "Bygrave"),
             505392: point.Point(51.910886, -0.186462, 136.0, "Sish Lane")}

        >>> marker_file = open("trigpoints")
        >>> markers = Trigpoints(marker_file)
        >>> for key, value in sorted(markers.items()):
        ...     print("%s - %s" % (key, value))
        500936 - Broom Farm (52°03'57"N, 000°16'53"W alt 37m)
        501097 - Bygrave (52°00'38"N, 000°10'24"W alt 97m)
        505392 - Sish Lane (51°54'39"N, 000°11'11"W alt 136m)
        >>> marker_file.seek(0)
        >>> markers = Trigpoints(marker_file.readlines())
        >>> markers = Trigpoints(open("southern_trigpoints"))
        >>> print(markers[1])
        FakeLand (48°07'23"S, 000°07'23"W alt 12m)
        >>> markers = Trigpoints(open("broken_trigpoints"))
        >>> for key, value in sorted(markers.items()):
        ...     print("%s - %s" % (key, value))
        500968 - Brown Hill Nm  See The Heights (53°38'23"N, 001°39'34"W)
        501414 - Cheriton Hill Nm  See Paddlesworth (51°06'03"N, 001°08'33"E)

        :Parameters:
            marker_file : `file`, `list` or `str`
                Trigpoint marker data to read
        :rtype: `dict`
        :return: Named locations with `Trigpoint` objects
        :raise ValueError: Invalid value for `marker_file`
        """
        field_names = ("tag", "identity", "latitude", "longitude", "altitude",
                       "name")
        pos_parse = lambda x, s: float(s[1:]) if s[0] == x else 0 - float(s[1:])
        latitude_parse = partial(pos_parse, "N")
        longitude_parse = partial(pos_parse, "E")
        # A value of 8888.0 denotes unavailable data
        altitude_parse = lambda s: None if s.strip() == "8888.0" else float(s)
        field_parsers = (str, int, latitude_parse, longitude_parse,
                         altitude_parse, str)

        data = utils.prepare_csv_read(marker_file, field_names)

        for row in ifilter(lambda x: x['tag'] == "W", data):
            for name, parser in zip(field_names, field_parsers):
                row[name] = parser(row[name])
            del row['tag']
            try:
                self[row['identity']] = Trigpoint(**row)
            except TypeError:
                # Workaround formatting error in 506514 entry that contains
                # spurious comma
                del row[None]
                self[row['identity']] = Trigpoint(**row)

