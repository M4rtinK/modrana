#
# vim: set sw=4 sts=4 et tw=80 fileencoding=utf-8:
#
"""gpx - Imports GPS eXchange format data files"""
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
import sys

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

from upoints import (point, utils)

# Supported GPX versions
GPX_VERSIONS = {
  "1.0": "http://www.topografix.com/GPX/1/0",
  "1.1": "http://www.topografix.com/GPX/1/1",
} #: Supported GPX namespace version to URI mapping

# Changing this will cause tests to fail.
DEF_GPX_VERSION = "1.1" #: Default GPX version to output

def create_elem(tag, attr=None, gpx_version=DEF_GPX_VERSION,
                human_namespace=False):
    """Create a partial ``ET.Element`` wrapper with namespace defined

    :Parameters:
        tag : `str`
            Tag name
        attr : `dict`
            Default attributes for tag
        gpx_version : `str`
            GPX version to use
        human_namespace : `bool`
            Whether to generate output using human readable
            namespace prefixes
    :rtype: ``function``
    :return: ``ET.Element`` wrapper with predefined namespace

    """
    if human_namespace and "xml.etree.cElementTree" in sys.modules:
        logging.warning("You have the fast cElementTree module available, if "
                        "you choose to use the human readable namespace "
                        "prefixes in XML output element generation will use "
                        "the much slower ElementTree code.  Slowdown can be in "
                        "excess of five times.")
    if not attr:
        attr = {}
    try:
        gpx_ns = GPX_VERSIONS[gpx_version]
    except KeyError:
        raise KeyError("Unknown GPX version `%s'" % gpx_version)
    if human_namespace:
        ElementTree._namespace_map[gpx_ns] = "gpx"
        return ElementTree.Element("{%s}%s" % (gpx_ns, tag), attr)
    else:
        return ET.Element("{%s}%s" % (gpx_ns, tag), attr)

class _GpxElem(point.Point):
    """Abstract class for representing an element from GPX data files

    :since: 0.11.0

    :Ivariables:
        latitude
            Waypoint's latitude
        longitude
            Waypoint's longitude
        name
            Waypoint's name
        description
            Waypoint's description

    """

    __slots__ = ('name', 'description', )

    _elem_name = None

    def __init__(self, latitude, longitude, name=None, description=None):
        """Initialise a new `Waypoint` object

        >>> _GpxElem(52, 0)
        _GpxElem(52.0, 0.0, None, None)
        >>> _GpxElem(52, 0, None)
        _GpxElem(52.0, 0.0, None, None)
        >>> _GpxElem(52, 0, "name", "desc")
        _GpxElem(52.0, 0.0, 'name', 'desc')

        :Parameters:
            latitude : `float` or coercible to `float`
                Element's latitude
            longitude : `float` or coercible to `float`
                Element's longitude
            name : `str`
                Name for Element
            description : `str`
                Element's description

        """
        super(_GpxElem, self).__init__(latitude, longitude)

        self.name = name
        self.description = description

    def __str__(self, mode="dms"):
        """Pretty printed location string

        >>> print(_GpxElem(52, 0))
        52°00'00"N, 000°00'00"E
        >>> print(_GpxElem(52, 0, "name", "desc"))
        name (52°00'00"N, 000°00'00"E) [desc]

        :Parameters:
            mode : `str`
                Coordinate formatting system to use
        :rtype: `str`
        :return: Human readable string representation of `_GpxElem` object

        """
        location = super(_GpxElem, self).__str__(mode)
        if self.name:
            text = ["%s (%s)" % (self.name, location), ]
        else:
            text = [location, ]
        if self.description:
            text.append("[%s]" % self.description)
        return " ".join(text)

    def togpx(self, gpx_version=DEF_GPX_VERSION, human_namespace=False):
        """Generate a GPX waypoint element subtree

        >>> ET.tostring(_GpxElem(52, 0).togpx())
        '<ns0:None lat="52.0" lon="0.0" xmlns:ns0="http://www.topografix.com/GPX/1/1" />'
        >>> ET.tostring(_GpxElem(52, 0, "Cambridge").togpx())
        '<ns0:None lat="52.0" lon="0.0" xmlns:ns0="http://www.topografix.com/GPX/1/1"><ns0:name>Cambridge</ns0:name></ns0:None>'
        >>> ET.tostring(_GpxElem(52, 0, "Cambridge", "in the UK").togpx())
        '<ns0:None lat="52.0" lon="0.0" xmlns:ns0="http://www.topografix.com/GPX/1/1"><ns0:name>Cambridge</ns0:name><ns0:desc>in the UK</ns0:desc></ns0:None>'

        :Parameters:
            gpx_version : `str`
                GPX version to generate
            human_namespace : `bool`
                Whether to generate output using human readable
                namespace prefixes
        :rtype: ``ET.Element``
        :return: GPX waypoint element

        """
        waypoint = create_elem(self.__class__._elem_name,
                               {"lat": str(self.latitude),
                                "lon": str(self.longitude)},
                               gpx_version, human_namespace)
        if self.name:
            nametag = create_elem("name", None, gpx_version, human_namespace)
            nametag.text = self.name
            waypoint.append(nametag)
        if self.description:
            desctag = create_elem("desc", None, gpx_version, human_namespace)
            desctag.text = self.description
            waypoint.append(desctag)
        return waypoint


class Waypoint(_GpxElem):
    """Class for representing a waypoint element from GPX data files

    >>> Waypoint(52, 0)
    Waypoint(52.0, 0.0, None, None)
    >>> Waypoint(52, 0, None)
    Waypoint(52.0, 0.0, None, None)
    >>> Waypoint(52, 0, "name", "desc")
    Waypoint(52.0, 0.0, 'name', 'desc')

    :since: 0.8.0

    :Ivariables:
        latitude
            Waypoint's latitude
        longitude
            Waypoint's longitude
        name
            Waypoint's name
        description
            Waypoint's description

    """

    __slots__ = ('name', 'description', )

    _elem_name = "wpt"


class Waypoints(point.Points):
    """Class for representing a group of `Waypoint` objects

    :since: 0.8.0

    """

    def __init__(self, gpx_file=None):
        """Initialise a new `Waypoints` object"""
        super(Waypoints, self).__init__()
        if gpx_file:
            self.import_locations(gpx_file)

    def import_locations(self, gpx_file, gpx_version=None):
        """Import GPX data files

        `import_locations()` returns a list with `Waypoint` objects.

        It expects data files in GPX format, as specified in `GPX 1.1 Schema
        Documentation <http://www.topografix.com/GPX/1/1/>`__, which is XML such
        as::

            <?xml version="1.0" encoding="utf-8" standalone="no"?>
            <gpx version="1.1" creator="PocketGPSWorld.com"
            xmlns="http://www.topografix.com/GPX/1/1"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">

              <wpt lat="52.015" lon="-0.221">
                <name>Home</name>
                <desc>My place</desc>
              </wpt>
              <wpt lat="52.167" lon="0.390">
                <name>MSR</name>
                <desc>Microsoft Research, Cambridge</desc>
              </wpt>
            </gpx>

        The reader uses `Python <http://www.python.org/>`__'s `ElementTree`
        module, so should be very fast when importing data.  The above file
        processed by `import_locations()` will return the following `list`
        object::

            [Waypoint(52.015, -0.221, "Home", "My place"),
             Waypoint(52.167, 0.390, "MSR", "Microsoft Research, Cambridge")]

        >>> waypoints = Waypoints(open("gpx"))
        >>> for value in sorted(waypoints,
        ...                     key=lambda x: x.name.lower()):
        ...     print(value)
        Home (52°00'54"N, 000°13'15"W) [My place]
        MSR (52°10'01"N, 000°23'24"E) [Microsoft Research, Cambridge]

        :Parameters:
            gpx_file : `file`, `list` or `str`
                GPX data to read
            gpx_version : `str`
                Specific GPX version entities to import
        :rtype: `list`
        :return: Locations with optional comments

        """
        data = utils.prepare_xml_read(gpx_file)

        if gpx_version:
            try:
                accepted_gpx = {gpx_version: GPX_VERSIONS[gpx_version]}
            except KeyError:
                raise KeyError("Unknown GPX version `%s'" % gpx_version)
        else:
            accepted_gpx = GPX_VERSIONS

        for version, namespace in accepted_gpx.items():
            logging.info("Searching for GPX v%s entries" % version)

            gpx_elem = lambda name: ET.QName(namespace, name).text
            waypoint_elem = "//" + gpx_elem("wpt")
            name_elem = gpx_elem("name")
            desc_elem = gpx_elem("desc")

            for waypoint in data.findall(waypoint_elem):
                latitude = waypoint.get("lat")
                longitude = waypoint.get("lon")
                name = waypoint.findtext(name_elem)
                description = waypoint.findtext(desc_elem)
                self.append(Waypoint(latitude, longitude, name, description))

    def export_gpx_file(self, gpx_version=DEF_GPX_VERSION,
                        human_namespace=False):
        """Generate GPX element tree from `Waypoints` object

        >>> from sys import stdout
        >>> locations = Waypoints(open("gpx"))
        >>> xml = locations.export_gpx_file()
        >>> xml.write(stdout)
        <ns0:gpx xmlns:ns0="http://www.topografix.com/GPX/1/1"><ns0:wpt lat="52.015" lon="-0.221"><ns0:name>Home</ns0:name><ns0:desc>My place</ns0:desc></ns0:wpt><ns0:wpt lat="52.167" lon="0.39"><ns0:name>MSR</ns0:name><ns0:desc>Microsoft Research, Cambridge</ns0:desc></ns0:wpt></ns0:gpx>

        :Parameters:
            gpx_version : `str`
                GPX version to generate
            human_namespace : `bool`
                Whether to generate output using human readable
                namespace prefixes
        :rtype: ``ET.ElementTree``
        :return: GPX element tree depicting `Waypoints` object

        """
        gpx = create_elem('gpx', None, gpx_version, human_namespace)
        for place in self:
            gpx.append(place.togpx(gpx_version, human_namespace))

        return ET.ElementTree(gpx)

class Trackpoint(_GpxElem):
    """Class for representing a waypoint element from GPX data files

    >>> Trackpoint(52, 0)
    Trackpoint(52.0, 0.0, None, None)
    >>> Trackpoint(52, 0, None)
    Trackpoint(52.0, 0.0, None, None)
    >>> Trackpoint(52, 0, "name", "desc")
    Trackpoint(52.0, 0.0, 'name', 'desc')

    :since: 0.10.0

    :Ivariables:
        latitude
            Trackpoint's latitude
        longitude
            Trackpoint's longitude
        name
            Trackpoint's name
        description
            Trackpoint's description

    """

    __slots__ = ('name', 'description', )

    _elem_name = "trkpt"


class Trackpoints(list):
    """Class for representing a group of `Trackpoint` objects

    :since: 0.10.0

    """

    def __init__(self, gpx_file=None):
        """Initialise a new `Trackpoints` object"""
        super(Trackpoints, self).__init__()
        if gpx_file:
            self.import_locations(gpx_file)

    def import_locations(self, gpx_file, gpx_version=None):
        """Import GPX data files

        `import_locations()` returns a series of lists representing track
        segments with `Trackpoint` objects as contents.

        It expects data files in GPX format, as specified in `GPX 1.1 Schema
        Documentation <http://www.topografix.com/GPX/1/1/>`__, which is XML such
        as::

            <?xml version="1.0" encoding="utf-8" standalone="no"?>
            <gpx version="1.1" creator="PocketGPSWorld.com"
            xmlns="http://www.topografix.com/GPX/1/1"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
              <trk>
                <trkseg>
                  <trkpt lat="52.015" lon="-0.221">
                    <name>Home</name>
                    <desc>My place</desc>
                  </trkpt>
                  <trkpt lat="52.167" lon="0.390">
                    <name>MSR</name>
                    <desc>Microsoft Research, Cambridge</desc>
                  </trkpt>
                </trkseg>
              </trk>
            </gpx>

        The reader uses `Python <http://www.python.org/>`__'s `ElementTree`
        module, so should be very fast when importing data.  The above file
        processed by `import_locations()` will return the following `list`
        object::

            [[Trackpoint(52.015, -0.221, "Home", "My place"),
              Trackpoint(52.167, 0.390, "MSR", "Microsoft Research, Cambridge")], ]

        >>> trackpoints = Trackpoints(open("gpx_tracks"))
        >>> for value in sorted(trackpoints[0],
        ...                     key=lambda x: x.name.lower()):
        ...     print(value)
        Home (52°00'54"N, 000°13'15"W) [My place]
        MSR (52°10'01"N, 000°23'24"E) [Microsoft Research, Cambridge]

        :Parameters:
            gpx_file : `file`, `list` or `str`
                GPX data to read
            gpx_version : `str`
                Specific GPX version entities to import
        :rtype: `list`
        :return: Locations with optional comments

        """
        data = utils.prepare_xml_read(gpx_file)

        if gpx_version:
            try:
                accepted_gpx = {gpx_version: GPX_VERSIONS[gpx_version]}
            except KeyError:
                raise KeyError("Unknown GPX version `%s'" % gpx_version)
        else:
            accepted_gpx = GPX_VERSIONS

        for version, namespace in accepted_gpx.items():
            logging.info("Searching for GPX v%s entries" % version)

            gpx_elem = lambda name: ET.QName(namespace, name).text
            segment_elem = "//" + gpx_elem("trkseg")
            trackpoint_elem = gpx_elem("trkpt")
            name_elem = gpx_elem("name")
            desc_elem = gpx_elem("desc")

            for segment in data.findall(segment_elem):
                points = point.Points()
                for trackpoint in segment.findall(trackpoint_elem):
                    latitude = trackpoint.get("lat")
                    longitude = trackpoint.get("lon")
                    name = trackpoint.findtext(name_elem)
                    description = trackpoint.findtext(desc_elem)
                    points.append(Trackpoint(latitude, longitude, name,
                                             description))
                self.append(points)

    def export_gpx_file(self, gpx_version=DEF_GPX_VERSION,
                        human_namespace=False):
        """Generate GPX element tree from `Trackpoints`

        >>> from sys import stdout
        >>> locations = Trackpoints(open("gpx_tracks"))
        >>> xml = locations.export_gpx_file()
        >>> xml.write(stdout)
        <ns0:gpx xmlns:ns0="http://www.topografix.com/GPX/1/1"><ns0:trk><ns0:trkseg><ns0:trkpt lat="52.015" lon="-0.221"><ns0:name>Home</ns0:name><ns0:desc>My place</ns0:desc></ns0:trkpt><ns0:trkpt lat="52.167" lon="0.39"><ns0:name>MSR</ns0:name><ns0:desc>Microsoft Research, Cambridge</ns0:desc></ns0:trkpt></ns0:trkseg></ns0:trk></ns0:gpx>

        :Parameters:
            gpx_version : `str`
                GPX version to generate
            human_namespace : `bool`
                Whether to generate output using human readable
                namespace prefixes
        :rtype: ``ET.ElementTree``
        :return: GPX element tree depicting `Trackpoint` objects

        """
        gpx = create_elem('gpx', None, gpx_version, human_namespace)
        track = create_elem('trk', None, gpx_version, human_namespace)
        gpx.append(track)
        for segment in self:
            chunk = create_elem('trkseg', None, gpx_version, human_namespace)
            track.append(chunk)
            for place in segment:
                chunk.append(place.togpx(gpx_version, human_namespace))

        return ET.ElementTree(gpx)

