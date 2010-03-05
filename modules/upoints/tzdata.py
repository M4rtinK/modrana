#
# vim: set sw=4 sts=4 et tw=80 fileencoding=utf-8:
#
"""tzdata - Imports timezone data files from UNIX zoneinfo"""
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

from itertools import ifilter

from upoints import (point, utils)

class Zone(point.Point):
    """Class for representing timezone descriptions from zoneinfo data

    :since: 0.6.0

    :Ivariables:
        latitude
            Location's latitude
        longitude
            Locations's longitude
        country
            Location's ISO 3166 country code
        zone
            Location's zone name as used in zoneinfo database
        comments
            Location comments

    """

    __slots__ = ('country', 'zone', 'comments')

    def __init__(self, location, country, zone, comments=None):
        """Initialise a new `Zone` object

        >>> Zone("+513030-0000731", 'GB', "Europe/London")
        Zone('+513030-0000730', 'GB', 'Europe/London', None)

        :Parameters:
            location : `str`
                Primary location in ISO 6709 format
            country : `str`
                Location's ISO 3166 country code
            zone : `str`
                Location's zone name as used in zoneinfo databse
            comments : `list`
                Location's alternate names

        """
        latitude, longitude = utils.from_iso6709(location + "/")[:2]
        super(Zone, self).__init__(latitude, longitude)

        self.country = country
        self.zone = zone
        self.comments = comments

    def __repr__(self):
        """Self-documenting string representation

        >>> Zone("+513030-0000731", 'GB', "Europe/London")
        Zone('+513030-0000730', 'GB', 'Europe/London', None)

        :rtype: `str`
        :return: String to recreate `Zone` object

        """
        location = utils.to_iso6709(self.latitude, self.longitude,
                                    format="dms")[:-1]
        return utils.repr_assist(self, {"location": location})

    def __str__(self, mode="dms"):
        """Pretty printed location string

        >>> print(Zone("+513030-0000731", 'GB', "Europe/London"))
        Europe/London (GB: 51°30'30"N, 000°07'30"W)
        >>> print(Zone("+0658-15813", "FM", "Pacific/Ponape",
        ...            ["Ponape (Pohnpei)", ]))
        Pacific/Ponape (FM: 06°58'00"N, 158°13'00"W also Ponape (Pohnpei))

        :Parameters:
            mode : `str`
                Coordinate formatting system to use
        :rtype: `str`
        :return: Human readable string representation of `Zone` object

        """
        text = ["%s (%s: %s" % (self.zone, self.country,
                                super(Zone, self).__str__(mode)), ]
        if self.comments:
            text.append(" also " + ", ".join(self.comments))
        text.append(")")
        return "".join(text)


class Zones(point.Points):
    """Class for representing a group of `Zone` objects

    :since: 0.6.0

    """

    def __init__(self, zone_file=None):
        """Initialise a new Zones object"""
        super(Zones, self).__init__()
        if zone_file:
            self.import_locations(zone_file)

    def import_locations(self, zone_file):
        """Parse zoneinfo zone description data files

        `import_locations()` returns a list of `Zone` objects.

        It expects data files in one of the following formats::

            AN	+1211-06900	America/Curacao
            AO	-0848+01314	Africa/Luanda
            AQ	-7750+16636	Antarctica/McMurdo	McMurdo Station, Ross Island

        Files containing the data in this format can be found in ``zone.tab`` file
        that is normally found in ``/usr/share/zoneinfo`` on UNIX-like systems, or
        from the `standard distribution site <ftp://elsie.nci.nih.gov/pub/>`__.

        When processed by `import_locations()` a `list` object of the
        following style will be returned::

            [Zone(None, None, "AN", "America/Curacao", None),
             Zone(None, None, "AO", "Africa/Luanda", None),
             Zone(None, None, "AO", "Antartica/McMurdo",
                  ["McMurdo Station", "Ross Island"])]

        >>> zones = Zones(open("timezones"))
        >>> for value in sorted(zones,
        ...                     key=lambda x: x.zone):
        ...     print(value)
        Africa/Luanda (AO: 08°48'00"S, 013°14'00"E)
        America/Curacao (AN: 12°11'00"N, 069°00'00"W)
        Antarctica/McMurdo (AQ: 77°50'00"S, 166°36'00"E also McMurdo Station,
        Ross Island)

        :Parameters:
            zone_file : `file`, `list` or `str`
                zone.tab data to read
        :rtype: `list`
        :return: Locations as `Zone` objects
        :raise FileFormatError: Unknown file format

        """
        field_names = ("country", "location", "zone", "comments")

        data = utils.prepare_csv_read(zone_file, field_names, delimiter=r"	")

        for row in ifilter(lambda x: not x['country'].startswith("#"), data):
            if row['comments']:
                row['comments'] = row['comments'].split(", ")
            self.append(Zone(**row))

    def dump_zone_file(self):
        """Generate a zoneinfo compatible zone description table

        >>> zones = Zones(open("timezones"))
        >>> Zones.dump_zone_file(zones)
        ['AN\\t+121100-0690000\\tAmerica/Curacao',
         'AO\\t-084800+0131400\\tAfrica/Luanda',
         'AQ\\t-775000+1663600\\tAntarctica/McMurdo\\tMcMurdo Station, Ross Island']

        :rtype: `list`
        :return: zoneinfo descriptions

        """
        data = []
        for zone in sorted(self, key=lambda x: x.country):
            text = ["%s	%s	%s"
                    % (zone.country,
                       utils.to_iso6709(zone.latitude, zone.longitude,
                                        format="dms")[:-1],
                       zone.zone), ]
            if zone.comments:
                text.append("	%s" % ", ".join(zone.comments))
            data.append("".join(text))
        return data

