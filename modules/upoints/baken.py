#
# vim: set sw=4 sts=4 et tw=80 fileencoding=utf-8:
#
"""baken - Imports baken data files"""
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

import ConfigParser
import logging
import re

from upoints import (point, utils)

class Baken(point.Point):
    """Class for representing location from baken data files

    :since: 0.4.0

    :Ivariables:
        latitude
            Location's latitude
        longitude
            Locations's longitude
        antenna
            Location's antenna type
        direction
            Antenna's direction
        frequency
            Transmitter's frequency
        height
            Antenna's height
        locator
            Location's locator string
        mode
            Transmitter's mode
        operator
            Transmitter's operator
        power
            Transmitter's power
        qth
            Location's qth

    """

    __slots__ = ('antenna', 'direction', 'frequency', 'height', '_locator',
                 'mode', 'operator', 'power', 'qth')

    def __init__(self, latitude, longitude, antenna=None, direction=None,
                 frequency=None, height=None, locator=None, mode=None,
                 operator=None, power=None, qth=None):
        """Initialise a new `Baken` object

        >>> Baken(14.460, 20.680, None, None, None, 0.000, None, None, None,
        ...       None, None)
        Baken(14.46, 20.68, None, None, None, 0.0, None, None, None, None, None)
        >>> Baken(None, None, "2 x Turnstile", None, 50.000, 460.000, "IO93BF",
        ...       "A1A", None, 25, None)
        Baken(53.2291666667, -1.875, '2 x Turnstile', None, 50.0, 460.0,
              'IO93BF', 'A1A', None, 25, None)
        >>> obj = Baken(None, None)
        Traceback (most recent call last):
        ...
        LookupError: Unable to instantiate baken object, no latitude or
        locator string

        :Parameters:
            latitude : `float` or coercible to `float`
                Location's latitude
            longitude : `float` or coercible to `float`
                Location's longitude
            antenna : `str`
                Location's antenna type
            direction : `tuple` of `int`
                Antenna's direction
            frequency : `float`
                Transmitter's frequency
            height : `float`
                Antenna's height
            locator : `str`
                Location's Maidenhead locator string
            mode : `str`
                Transmitter's mode
            operator : `tuple` of `str`
                Transmitter's operator
            power : `float`
                Transmitter's power
            qth : `str`
                Location's qth
        :raise LookupError: No position data to use

        """
        if not latitude is None:
            super(Baken, self).__init__(latitude, longitude)
        elif not locator is None:
            latitude, longitude = utils.from_grid_locator(locator)
            super(Baken, self).__init__(latitude, longitude)
        else:
            raise LookupError("Unable to instantiate baken object, no "
                              "latitude or locator string")

        self.antenna = antenna
        self.direction = direction
        self.frequency = frequency
        self.height = height
        self._locator = locator
        self.mode = mode
        self.operator = operator
        self.power = power
        self.qth = qth

    def _set_locator(self, value):
        """Update the locator, and trigger a latitude and longitude update

        >>> test = Baken(None, None, "2 x Turnstile", None, 50.000, 460.000,
        ...              "IO93BF", "A1A", None, 25, None)
        >>> test.locator = "JN44FH"
        >>> test
        Baken(44.3125, 8.45833333333, '2 x Turnstile', None, 50.0, 460.0,
              'JN44FH', 'A1A', None, 25, None)

        :Parameters:
            value : `str`
                New Maidenhead locator string

        """
        self._locator = value
        self._latitude, self._longitude = utils.from_grid_locator(value)
    locator = property(lambda self: self._locator,
                       lambda self, value: self._set_locator(value))

    def __str__(self, mode="dms"):
        """Pretty printed location string

        >>> print(Baken(14.460, 20.680, None, None, None, 0.000, None, None,
        ...             None, None, None))
        14°27'36"N, 020°40'48"E
        >>> print(Baken(None, None, "2 x Turnstile", None, 50.000, 460.000,
        ...             "IO93BF", "A1A", None, 25, None))
        IO93BF (53°13'45"N, 001°52'30"W)

        :Parameters:
            mode : `str`
                Coordinate formatting system to use
        :rtype: `str`
        :return: Human readable string representation of `Baken` object

        """
        text = super(Baken, self).__str__(mode)
        if self._locator:
            text = "%s (%s)" % (self._locator, text)
        return text


class Bakens(point.KeyedPoints):
    """Class for representing a group of `Baken` objects

    :since: 0.5.1

    """

    def __init__(self, baken_file=None):
        """Initialise a new `Bakens` object"""
        super(Bakens, self).__init__()
        if baken_file:
            self.import_locations(baken_file)

    def import_locations(self, baken_file):
        """Import baken data files

        `import_locations()` returns a dictionary with keys containing the
        section title, and values consisting of a collection `Baken` objects.

        It expects data files in the format used by the baken amateur radio
        package, which is Windows INI style files such as::

            [Abeche, Chad]
            latitude=14.460000
            longitude=20.680000
            height=0.000000

            [GB3BUX]
            frequency=50.000
            locator=IO93BF
            power=25 TX
            antenna=2 x Turnstile
            height=460
            mode=A1A

        The reader uses `Python <http://www.python.org/>`__'s `ConfigParser`
        module, so should be reasonably robust against encodings and such.  The
        above file processed by `import_locations()` will return the following
        `dict` object::

            {"Abeche, Chad": Baken(14.460, 20.680, None, None, None, 0.000,
                                   None, None, None, None, None),
             "GB3BUX": : Baken(None, None, "2 x Turnstile", None, 50.000,
                               460.000, "IO93BF", "A1A", None, 25, None)}

        >>> locations = Bakens(open("baken_data"))
        >>> for key, value in sorted(locations.items()):
        ...     print("%s - %s" % (key, value))
        Abeche, Chad - 14°27'36"N, 020°40'48"E
        GB3BUX - IO93BF (53°13'45"N, 001°52'30"W)
        IW1RCT - JN44FH (44°18'45"N, 008°27'29"E)
        >>> locations = Bakens(open("no_valid_baken"))
        >>> len(locations)
        0

        :Parameters:
            baken_file : `file`, `list` or `str`
                Baken data to read
        :rtype: `dict`
        :return: Named locations and their associated values

        """
        data = ConfigParser.ConfigParser()
        if hasattr(baken_file, "readlines"):
            data.readfp(baken_file)
        elif isinstance(baken_file, list):
            data.read(baken_file)
        elif isinstance(baken_file, basestring):
            data.readfp(open(baken_file))
        else:
            raise TypeError("Unable to handle data of type `%s`"
                            % type(baken_file))
        valid_locator = re.compile("[A-Z]{2}[0-9]{2}[A-Z]{2}")
        for name in data.sections():
            elements = {}
            for item in ("latitude", "longitude", "antenna", "direction",
                         "frequency", "height", "locator", "mode", "operator",
                         "power", "qth"):
                if data.has_option(name, item):
                    if item in ("antenna", "locator", "mode", "power", "qth"):
                        elements[item] = data.get(name, item)
                    elif item == "operator":
                        elements[item] = elements[item].split(",")
                    elif item == "direction":
                        elements[item] = data.get(name, item).split(",")
                    else:
                        try:
                            elements[item] = data.getfloat(name, item)
                        except ValueError:
                            logging.debug("Multiple frequency workaround for "
                                          "`%s' entry" % name)
                            elements[item] = map(float,
                                                 data.get(name, item).split(","))
                else:
                    elements[item] = None
            if elements["latitude"] is None \
               and not valid_locator.match(elements["locator"]):
                logging.info("Skipping `%s' entry, as it contains no location "
                             "data" % name)
                continue

            self[name] = Baken(**elements)

