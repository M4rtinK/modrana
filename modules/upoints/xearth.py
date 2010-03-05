#
# vim: set sw=4 sts=4 et tw=80 fileencoding=utf-8:
#
"""xearth - Imports xearth-style marker files"""
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

from upoints import (point, utils)

class Xearth(point.Point):
    """Class for representing a location from a Xearth marker

    :since: 0.2.0

    :Ivariables:
        latitude
            Location's latitude
        longitude
            Locations's longitude
        comment
            Location's comment

    """

    __slots__ = ('comment', )

    def __init__(self, latitude, longitude, comment=None):
        """Initialise a new `Xearth` object

        >>> Xearth(52.015, -0.221, "James Rowe's house")
        Xearth(52.015, -0.221, "James Rowe's house")

        :Parameters:
            latitude : `float` or coercible to `float`
                Location's latitude
            longitude : `float` or coercible to `float`
                Location's longitude
            comment : `str`
                Comment for location

        """
        super(Xearth, self).__init__(latitude, longitude)
        self.comment = comment

    def __str__(self, mode="dd"):
        """Pretty printed location string

        :see: `point.Point`

        >>> print(Xearth(52.015, -0.221))
        N52.015°; W000.221°
        >>> print(Xearth(52.015, -0.221).__str__(mode="dms"))
        52°00'54"N, 000°13'15"W
        >>> print(Xearth(52.015, -0.221).__str__(mode="dm"))
        52°00.90'N, 000°13.26'W
        >>> print(Xearth(52.015, -0.221, "James Rowe's house"))
        James Rowe's house (N52.015°; W000.221°)

        :Parameters:
            mode : `str`
                Coordinate formatting system to use
        :rtype: `str`
        :return: Human readable string representation of `Xearth` object

        """
        text = super(Xearth, self).__str__(mode)

        if self.comment:
            return "%s (%s)" % (self.comment, text)
        else:
            return text


class Xearths(point.KeyedPoints):
    """Class for representing a group of `Xearth` objects

    :since: 0.5.1

    """

    def __init__(self, marker_file=None):
        """Initialise a new `Xearths` object"""
        super(Xearths, self).__init__()
        if marker_file:
            self.import_locations(marker_file)

    def __str__(self):
        """`Xearth` objects rendered for use with Xearth/Xplanet

        >>> markers = Xearths(open("xearth"))
        >>> print(markers)
        52.015000 -0.221000 "Home"
        52.633300 -2.500000 "Telford"

        :rtype: `str`
        :return: Xearth/Xplanet marker file formatted output

        """
        return "\n".join(utils.dump_xearth_markers(self, "comment"))

    def import_locations(self, marker_file):
        """Parse Xearth data files

        `import_locations()` returns a dictionary with keys containing the
        `xearth <http://www.cs.colorado.edu/~tuna/xearth/>`__ name, and values
        consisting of a `Xearth` object and a string containing any comment
        found in the marker file.

        It expects Xearth marker files in the following format::

            # Comment

            52.015     -0.221 "Home"          # James Rowe's home
            52.6333    -2.5   "Telford"

        Any empty line or line starting with a '#' is ignored.  All data lines
        are whitespace-normalised, so actual layout should have no effect.  The
        above file processed by `import_locations()` will return the
        following `dict` object::

            {'Home': point.Point(52.015, -0.221, "James Rowe's home"),
             'Telford': point.Point(52.6333, -2.5, None)}

        :note: This function also handles the extended `xplanet
            <http://xplanet.sourceforge.net/>`__ marker files whose points can
            optionally contain added xplanet specific keywords for defining
            colours and fonts.

        >>> markers = Xearths(open("xearth"))
        >>> for key, value in sorted(markers.items()):
        ...     print("%s - %s" % (key, value))
        Home - James Rowe's home (N52.015°; W000.221°)
        Telford - N52.633°; W002.500°

        :Parameters:
            marker_file : `file`, `list` or `str`
                Xearth marker data to read
        :rtype: `dict`
        :return: Named locations with optional comments

        """
        data = utils.prepare_read(marker_file)

        for line in data:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            chunk = line.split("#")
            data = chunk[0]
            comment = chunk[1].strip() if len(chunk) == 2 else None
            # Need maximum split of 2, because name may contain whitespace
            latitude, longitude, name = data.split(None, 2)
            name = name.strip()
            # Find matching start and end quote, and keep only the contents
            name = name[1:name.find(name[0], 1)]
            self[name.strip()] = Xearth(latitude, longitude, comment)

