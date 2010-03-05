#
# vim: set sw=4 sts=4 et tw=80 fileencoding=utf-8:
#
"""upoints - Modules for working with points on Earth"""
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

__version__ = "0.11.0"
__date__ = "2008-05-20"
__author__ = "James Rowe <jnrowe@ukfsn.org>"
__copyright__ = "Copyright (C) 2007-2008 James Rowe"
__license__ = "GNU General Public License Version 3"
__credits__ = "Cédric Dufour, Kelly Turner, Simon Woods"
__history__ = "See Mercurial repository"

from email.utils import parseaddr

__doc__ += """.

``upoints`` is a collection of `GPL v3`_ licensed modules for working with
points on Earth, or other near spherical objects.  It allows you to calculate
the distance and bearings between points, mangle xearth_/xplanet_ data files,
work with online UK trigpoint databases, NOAA_'s weather station database and
other such location databases.

.. _GPL v3: http://www.gnu.org/licenses/
.. _xearth: http://www.cs.colorado.edu/~tuna/xearth/
.. _xplanet: http://xplanet.sourceforge.net/
.. _NOAA: http://weather.noaa.gov/

The `upoints.point` module is the simplest interface available, and is mainly
useful as a naïve object for simple calculation and subclassing for specific
usage.  An example of how to use it follows:

>>> Home = point.Point(52.015, -0.221)
>>> Telford = point.Point(52.6333, -2.5000)
>>> int(Home.distance(Telford))
169
>>> int(Home.bearing(Telford))
294
>>> int(Home.final_bearing(Telford))
293
>>> import datetime
>>> Home.sun_events(datetime.date(2007, 6, 28))
(datetime.time(3, 42), datetime.time(20, 25))
>>> Home.sunrise(datetime.date(2007, 6, 28))
datetime.time(3, 42)
>>> Home.sunset(datetime.date(2007, 6, 28))
datetime.time(20, 25)

:version: %s
:author: `%s <mailto:%s>`__
:copyright: %s
:status: WIP
:license: %s
""" % ((__version__, ) + parseaddr(__author__) + (__copyright__, __license__))

from upoints import (baken, cellid, cities, geonames, gpx, kml, nmea, osm,
                     point, trigpoints, tzdata, utils, weather_stations, xearth)

