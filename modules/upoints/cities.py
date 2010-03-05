#
# vim: set sw=4 sts=4 et tw=80 fileencoding=utf-8:
#
"""cities - Imports GNU miscfiles cities data files"""
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

import logging
import time

from upoints import (point, trigpoints, utils)

TEMPLATE = """\
ID          : %s
Type        : %s
Population  : %s
Size        : %s
Name        : %s
 Country    : %s
 Region     : %s
Location    : %s
 Longitude  : %s
 Latitude   : %s
 Elevation  : %s
Date        : %s
Entered-By  : %s""" #: GNU miscfiles cities.dat template

class City(trigpoints.Trigpoint):
    """Class for representing an entry from the GNU miscfiles cities data file

    :since: 0.2.0

    :Ivariables:
        identifier
            Numeric identifier for object
        name
            Place name
        ptype
            Place type
        population
            Place population, if known
        size
            Place Size
        country
            Country the place is in
        region
            Region the place is in
        location
            Body, always Earth in miscfiles 1.4.2
        latitude
            Place's latitude
        longitude
            Place's longitude
        altitude
            Place's elevation
        date
            Entry date
        entered
            Entry's author

    """

    __slots__ = ('identifier', 'ptype', 'population', 'size', 'country',
                 'region', 'location', 'date', 'entered')

    def __init__(self, identifier, name, ptype, region, country, location,
                 population, size, latitude, longitude, altitude, date,
                 entered):
        """Initialise a new `City` object

        >>> City(498, "Zwickau", "City", "Sachsen", "DE", "Earth", 108835,
        ...      None, 12.5, 50.72, None, (1997, 4, 10, 0, 0, 0, 3, 100, -1),
        ...      "M.Dowling@tu-bs.de")
        City(498, 'Zwickau', 'City', 'Sachsen', 'DE', 'Earth', 108835, None,
             12.5, 50.72, None, (1997, 4, 10, 0, 0, 0, 3, 100, -1),
             'M.Dowling@tu-bs.de')

        :Parameters:
            identifier : `int`
                Numeric identifier for object
            name : `str`
                Place name
            ptype : `str`
                Type of place
            region : `str` or `None`
                Region place can be found
            country : `str` or `None`
                Country name place can be found
            location : `str`
                Body place can be found
            population : `int` or `None`
                Place's population
            size : `int` or `None`
                Place's area
            latitude : `float`
                Station's latitude
            longitude : `float`
                Station's longitude
            altitude : `int` or `None`
                Station's elevation
            date : ``time.struct_time``
                Date the entry was added
            entered : `str` or `None`
                Entry's author

        """
        super(City, self).__init__(latitude, longitude, altitude, name)
        self.identifier = identifier
        self.ptype = ptype
        self.region = region
        self.country = country
        self.location = location
        self.population = population
        self.size = size
        self.date = date
        self.entered = entered

    def __str__(self, mode=None):
        """Pretty printed location string

        >>> t = City(498, "Zwickau", "City", "Sachsen", "DE", "Earth", 108835,
        ...          None, 50.72, 12.5, None,
        ...          (1997, 4, 10, 0, 0, 0, 3, 100, -1), "M.Dowling@tu-bs.de")
        >>> print(t)
        ID          : 498
        Type        : City
        Population  : 108835
        Size        : 
        Name        : Zwickau
         Country    : DE
         Region     : Sachsen
        Location    : Earth
         Longitude  : 12.5
         Latitude   : 50.72
         Elevation  : 
        Date        : 19970410
        Entered-By  : M.Dowling@tu-bs.de

        :Parameters:
            mode : `None`
                Dummy parameter to maintain signature of
                `trigpoints.Trigpoint.__str__`
        :rtype: `str`
        :return: Human readable string representation of `City` object

        """
        values = map(utils.value_or_empty,
                     (self.identifier, self.ptype,
                      self.population, self.size,
                      self.name, self.country,
                      self.region, self.location,
                      self.longitude, self.latitude,
                      self.altitude,
                      time.strftime("%Y%m%d", self.date) if self.date else "",
                      self.entered))
        return TEMPLATE % tuple(values)


class Cities(point.Points):
    """Class for representing a group of `City` objects

    :since: 0.5.1

    """

    def __init__(self, data=None):
        """Initialise a new `Cities` object"""
        super(Cities, self).__init__()
        if data:
            self.import_locations(data)

    def import_locations(self, data):
        """Parse GNU miscfiles cities data files

        `import_locations()` returns a list containing `City` objects.

        It expects data files in the same format that `GNU miscfiles
        <http://www.gnu.org/directory/miscfiles.html>`__  provided,
        that is::

            ID          : 1
            Type        : City
            Population  : 210700
            Size        : 
            Name        : Aberdeen
             Country    : UK
             Region     : Scotland
            Location    : Earth
             Longitude  : -2.083
             Latitude   :   57.150
             Elevation  : 
            Date        : 19961206
            Entered-By  : Rob.Hooft@EMBL-Heidelberg.DE
            //
            ID          : 2
            Type        : City
            Population  : 1950000
            Size        : 
            Name        : Abidjan
             Country    : Ivory Coast
             Region     : 
            Location    : Earth
             Longitude  : -3.867
             Latitude   :    5.333
             Elevation  : 
            Date        : 19961206
            Entered-By  : Rob.Hooft@EMBL-Heidelberg.DE

        When processed by `import_locations()` will return `list` object in
        the following style::

            [City(1, "City", 210700, None, "Aberdeen", "UK", "Scotland",
                  "Earth", -2.083, 57.15, None, (1996, 12, 6, 0, 0, 0, 4,
                  341, -1), "Rob.Hooft@EMBL-Heidelberg.DE"),
             City(2, "City", 1950000, None, "Abidjan", "Ivory Coast", "",
                  "Earth", -3.867, 5.333, None, (1996, 12, 6, 0, 0, 0, 4,
                  341, -1), "Rob.Hooft@EMBL-Heidelberg.DE")])

        >>> cities_file = open("city_data")
        >>> cities = Cities(cities_file)
        >>> for city in sorted(cities, key=lambda x: x.identifier):
        ...     print("%i - %s (%s;%s)" % (city.identifier, city.name, city.latitude,
        ...                                city.longitude))
        126 - London (51.5;-0.083)
        127 - Luxembourg (49.617;6.117)
        128 - Lyon (45.767;4.867)
        >>> cities_file.seek(0)
        >>> manual_list = cities_file.read().split("//\\n")
        >>> cities = Cities(manual_list)

        :Parameters:
            data : `file`, `list` or `str`
                NOAA station data to read
        :rtype: `list`
        :return: Places as `City` objects
        :raise TypeError: Invalid value for data

        """
        if hasattr(data, "read"):
            data = data.read().split("//\n")
        elif isinstance(data, list):
            pass
        elif isinstance(data, basestring):
            data = open(data).read().split("//\n")
        else:
            raise TypeError("Unable to handle data of type `%s'" % type(data))

        keys = ("identifier", "ptype", "population", "size", "name", "country",
                "region", "location", "longitude", "latitude", "altitude",
                "date", "entered")

        for record in data:
            # We truncate after splitting because the v1.4.2 datafile contains
            # a broken separator between 229 and 230 that would otherwise break
            # the import
            data = [i.split(":")[1].strip() for i in record.splitlines()[:13]]
            entries = dict(zip(keys, data))

            # Entry for Utrecht has the incorrect value of 0.000 for elevation.
            if entries["altitude"] == "0.000":
                logging.debug("Ignoring `0.000' value for elevation in `%s' "
                              "entry" % record)
                entries["altitude"] = ""
            for i in ("identifier", "population", "size", "altitude"):
                entries[i] = int(entries[i]) if entries[i] else None
            for i in ("longitude", "latitude"):
                entries[i] = float(entries[i]) if entries[i] else None
            entries["date"] = time.strptime(entries["date"], "%Y%m%d")
            self.append(City(**entries))

