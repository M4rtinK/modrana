#
# vim: set sw=4 sts=4 et tw=80 fileencoding=utf-8:
#
"""gpx - Imports GPS eXchange format data files"""
# Copyright (C) 2007-2010  James Rowe
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

from functools import partial
from operator import attrgetter
from xml.etree import ElementTree

from core.backports.six import string_types as basestring

try:
    from xml.etree import cElementTree as ET
except ImportError:
    try:
        from lxml import etree as ET
    except ImportError:
        ET = ElementTree
        logging.info("cElementTree is unavailable. XML processing will be "
                     "much slower with ElementTree")
if not ET.__name__ == "xml.etree.cElementTree":
    logging.warning("You have the fast cElementTree module available, if you "
                    "choose to use the human readable namespace prefixes in "
                    "XML output element generation will use the much slower "
                    "ElementTree code.  Slowdown can be in excess of five "
                    "times.")

from . import (point, utils)

#: Supported GPX namespace version to URI mapping

"""modrana:
   the header has been expanded,
   othervise the resulting GPX files dont validate
"""
GPX_VERSIONS = {
  "1.0": {'xsi:schemaLocation':"http://www.topografix.com/GPX/1/0"}, #TODO: make also a GPX1.0 header ?
#  "1.1": "http://www.topografix.com/GPX/1/1",
  "1.1": {
          'version':"1.1", 
          'creator':"modRana - http://www.modrana.org",
          'xmlns:xsi':"http://www.w3.org/2001/XMLSchema-instance", 
          'xmlns':"http://www.topografix.com/GPX/1/1", 
          'xsi:schemaLocation':"http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
          }
              }
#: Default GPX version to output
# Changing this will cause tests to fail.
DEF_GPX_VERSION = "1.1"

def create_elem(tag, attr=None, text=None, gpx_version=DEF_GPX_VERSION,
                human_namespace=False):
    """Create a partial :class:`ET.Element` wrapper with namespace defined

    :type tag: ``str``
    :param tag:    Tag name
    :type attr: ``dict``
    :param attr: Default attributes for tag
    :type text: ``str``
    :param text: Text content for the tag
    :type gpx_version: ``str``
    :param gpx_version: GPX version to use
    :type human_namespace: ``bool``
    :param human_namespace: Whether to generate output using human readable
        namespace prefixes
    :rtype: ``function``
    :return: :class:`ET.Element` wrapper with predefined namespace

    """

    """modrana:
       add the header to the gpx tag
    """
    if tag=='gpx':
      attr = GPX_VERSIONS[gpx_version]

    if not attr:
        attr = {}
    try:
        gpx_ns = GPX_VERSIONS[gpx_version]
    except KeyError:
        raise KeyError("Unknown GPX version `%s'" % gpx_version)
    if human_namespace:
        ElementTree._namespace_map[gpx_ns] = "gpx"
        element = ElementTree.Element("{%s}%s" % (gpx_ns, tag), attr)
    else:
#        element = ET.Element("{%s}%s" % (gpx_ns, tag), attr)
        # modrana:
        # this fixes the resulting GPX not being valid becuase of unknown
        # namespace prefixes
        element = ET.Element("%s" % (tag), attr)
    if text:
        element.text = text
    return element

class _GpxElem(point.TimedPoint):
    """Abstract class for representing an element from GPX data files

    .. versionadded:: 0.11.0

    """

    __slots__ = ('name', 'description', 'elevation', 'time', )

    _elem_name = None

    def __init__(self, latitude, longitude, name=None, description=None,
                 elevation=None, time=None):
        """Initialise a new ``_GpxElem`` object

        >>> _GpxElem(52, 0)
        _GpxElem(52.0, 0.0, None, None, None, None)
        >>> _GpxElem(52, 0, None)
        _GpxElem(52.0, 0.0, None, None, None, None)
        >>> _GpxElem(52, 0, "name", "desc")
        _GpxElem(52.0, 0.0, 'name', 'desc', None, None)

        :type latitude: ``float`` or coercible to ``float``
        :param latitude: Element's latitude
        :type longitude: ``float`` or coercible to ``float``
        :param longitude: Element's longitude
        :type name: ``str``
        :param name: Name for Element
        :type description: ``str``
        :param description: Element's description
        :type elevation: ``float``
        :param elevation: Element's elevation
        :type time: :class:`utils.Timestamp`
        :param time: Time the data was generated

        """
        super(_GpxElem, self).__init__(latitude, longitude, time=time)
        self.name = name
        self.description = description
        self.elevation = elevation

    def __str__(self, mode="dms"):
        """Pretty printed location string

        >>> print(_GpxElem(52, 0))
        52°00'00"N, 000°00'00"E
        >>> print(_GpxElem(52, 0, "name", "desc", 40))
        name (52°00'00"N, 000°00'00"E @ 40m) [desc]
        >>> print(_GpxElem(52, 0, "name", "desc", 40,
        ...                utils.Timestamp(2008, 7, 25)))
        name (52°00'00"N, 000°00'00"E @ 40m on 2008-07-25T00:00:00+00:00) [desc]

        :type mode: ``str``
        :param mode: Coordinate formatting system to use
        :rtype: ``str``
        :return: Human readable string representation of :class:`_GpxElem`
            object

        """
        location = super(_GpxElem, self).__str__(mode)
        if self.elevation:
            location += " @ %sm" % self.elevation
        if self.time:
            location += " on %s" % self.time # modified for modRana
#            location += " on %s" % self.time.isoformat()
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
        >>> ET.tostring(_GpxElem(52, 0, "Cambridge", "in the UK").togpx())
        '<ns0:None lat="52.0" lon="0.0" xmlns:ns0="http://www.topografix.com/GPX/1/1"><ns0:name>Cambridge</ns0:name><ns0:desc>in the UK</ns0:desc></ns0:None>'
        >>> ET.tostring(_GpxElem(52, 0, "name", "desc", 40,
        ...                      utils.Timestamp(2008, 7, 25)).togpx())
        '<ns0:None lat="52.0" lon="0.0" xmlns:ns0="http://www.topografix.com/GPX/1/1"><ns0:name>name</ns0:name><ns0:desc>desc</ns0:desc><ns0:ele>40</ns0:ele><ns0:time>2008-07-25T00:00:00+00:00</ns0:time></ns0:None>'

        :type gpx_version: ``str``
        :param gpx_version: GPX version to generate
        :type human_namespace: ``bool``
        :param human_namespace: Whether to generate output using human readable
            namespace prefixes
        :rtype: :class:`ET.Element`
        :return: GPX element

        """
        elementise = partial(create_elem, gpx_version=gpx_version,
                             human_namespace=human_namespace)
        element = elementise(self.__class__._elem_name,
                             {"lat": str(self.latitude),
                              "lon": str(self.longitude)})
        if self.name:
            element.append(elementise("name", None, self.name))
        if self.description:
            element.append(elementise("desc", None, self.description))
        if self.elevation:
            element.append(elementise("ele", None, str(self.elevation)))
        if self.time:
#            element.append(elementise("time", None, self.time.isoformat()))
            """modrana:
               the previous format was using current time type sufix
               this was changed just to "Z", as demanded by the specification
               the time should be just UTC, not local time
            """
#            element.append(elementise("time", None, time.strftime("%Y-%m-%dT%H:%M:%SZ")))
            # add Z on the end
            correctTime = "%sZ" % self.time
            element.append(elementise("time", None, correctTime))
        return element


class _SegWrap(list):
    """Abstract class for representing segmented elements from GPX data files

    .. versionadded:: 0.12.0

    """

    def __init__(self, gpx_file=None, metadata=None):
        """Initialise a new ``_SegWrap`` object"""
        super(_SegWrap, self).__init__()
        self.metadata = metadata if metadata else _GpxMeta()
        self._gpx_file = gpx_file
        if gpx_file:
            self.import_locations(gpx_file)

    def distance(self, method="haversine"):
        """Calculate distances between locations in segments

        :Parameters:
            method : ``str``
                Method used to calculate distance

        :rtype: ``list`` of ``list`` of ``float``
        :return: Groups of distance between points in segments

        """
        distances = []
        for segment in self:
            if len(segment) < 2:
                distances.append([])
            else:
                distances.append(segment.distance(method))
        return distances

    def bearing(self, format="numeric"):
        """Calculate bearing between locations in segments

        :type format: ``str``
        :param format: Format of the bearing string to return
        :rtype: ``list`` of ``list`` of ``float``
        :return: Groups of bearings between points in segments
        """
        bearings = []
        for segment in self:
            if len(segment) < 2:
                bearings.append([])
            else:
                bearings.append(segment.bearing(format))
        return bearings

    def final_bearing(self, format="numeric"):
        """Calculate final bearing between locations in segments

        :type format: ``str``
        :param format: Format of the bearing string to return
        :rtype: ``list`` of ``list`` of ``float``
        :return: Groups of bearings between points in segments
        """
        bearings = []
        for segment in self:
            if len(segment) < 2:
                bearings.append([])
            else:
                bearings.append(segment.final_bearing(format))
        return bearings

    def inverse(self):
        """Calculate the inverse geodesic between locations in segments

        :rtype: ``list`` of 2 ``tuple`` of ``float``
        :return: Groups in bearing and distance between points in segments

        """
        inverses = []
        for segment in self:
            if len(segment) < 2:
                inverses.append([])
            else:
                inverses.append(segment.inverse())
        return inverses

    def midpoint(self):
        """Calculate the midpoint between locations in segments

        :rtype: ``list`` of ``Point`` instance
        :return: Groups of midpoint between points in segments

        """
        midpoints = []
        for segment in self:
            if len(segment) < 2:
                midpoints.append([])
            else:
                midpoints.append(segment.midpoint())
        return midpoints

    def range(self, location, distance):
        """Test whether locations are within a given range of ``location``

        :type location: ``Point``
        :param location: Location to test range against
        :type distance: ``float``
        :param distance: Distance to test location is within
        :rtype: ``list`` of ``list`` of ``Point`` objects within specified range
        :return: Groups of points in range per segment

        """
        return (segment.range(location, distance) for segment in self)

    def destination(self, bearing, distance):
        """Calculate destination locations for given distance and bearings

        :type bearing: ``float`` or coercible to ``float``
        :param bearing: Bearing to move on in degrees
        :type distance: ``float`` or coercible to ``float``
        :param distance: Distance in kilometres
        :rtype: ``list`` of ``list`` of ``Point``
        :return: Groups of points shifted by ``distance`` and ``bearing``

        """
        return (segment.destination(bearing, distance) for segment in self)
    forward = destination

    def sunrise(self, date=None, zenith=None):
        """Calculate sunrise times for locations

        :type date: :class:`datetime.date`
        :param date: Calculate rise or set for given date
        :type zenith: ``None`` or ``str``
        :param zenith: Calculate sunrise events, or end of twilight
        :rtype: ``list`` of ``list`` of :class:`datetime.datetime`
        :return: The time for the sunrise for each point in each segment

        """
        return (segment.sunrise(date, zenith) for segment in self)

    def sunset(self, date=None, zenith=None):
        """Calculate sunset times for locations

        :type date: :class:`datetime.date`
        :param date: Calculate rise or set for given date
        :type zenith: ``None`` or ``str``
        :param zenith: Calculate sunset events, or start of twilight times
        :rtype: ``list`` of ``list`` of :class:`datetime.datetime`
        :return: The time for the sunset for each point in each segment

        """
        return (segment.sunset(date, zenith) for segment in self)

    def sun_events(self, date=None, zenith=None):
        """Calculate sunrise/sunset times for locations

        :type date: :class:`datetime.date`
        :param date: Calculate rise or set for given date
        :type zenith: ``None`` or ``str``
        :param zenith: Calculate rise/set events, or twilight times
        :rtype: ``list`` of ``list`` of 2 ``tuple`` of
            :class:`datetime.datetime`
        :return: The time for the sunrise and sunset events for each point in
            each segment

        """
        return (segment.sun_events(date, zenith) for segment in self)

    def to_grid_locator(self, precision="square"):
        """Calculate Maidenhead locator for locations

        :type precision: ``str``
        :param precision: Precision with which generate locator string
        :rtype: ``list`` of ``list`` of ``str``
        :return: Groups of Maidenhead locator for each point in segments

        """
        return (segment.to_grid_locator(precision) for segment in self)

    def speed(self):
        """Calculate speed between locations per segment

        :rtype: ``list`` of ``list`` of ``float``
        :return: Speed between points in each segment in km/h

        """
        return (segment.speed() for segment in self)


class _GpxMeta(object):
    """Class for representing GPX global metadata

    .. versionadded:: 0.12.0

    """
    __slots__ = ("name", "desc", "author", "copyright", "link", "time",
                 "keywords", "bounds", "extensions")

    def __init__(self, name=None, desc=None, author=None, copyright=None,
                 link=None, time=None, keywords=None, bounds=None,
                 extensions=None):
        """Initialise a new `_GpxMeta` object

        :type name: ``str``
        :param name: Name for the export
        :type desc: ``str``
        :param desc: Description for the GPX export
        :type author: ``dict``
        :param author: Author of the entire GPX data
        :type copyright: ``dict``
        :param copyright: Copyright data for the exported data
        :type link: ``list`` of ``str`` or ``dict``
        :param link: Links associated with the data
        :type time: :class:`utils.Timestamp`
        :param time:Time the data was generated
        :type keywords: ``str``
        :param keywords: Keywords associated with the data
        :type bounds: ``dict`` or ``list`` of ``Point`` objects
        :param bounds: Area used in the data
        :type extensions: ``list`` of :class:`ET.Element` objects
        :param extensions: Any external data associated with the export

        """
        super(_GpxMeta, self).__init__()
        self.name = name
        self.desc = desc
        self.author = author if author else {}
        self.copyright = copyright if copyright else {}
        self.link = link if link else []
        self.time = time
        self.keywords = keywords
        self.bounds = bounds
        self.extensions = extensions

    def togpx(self, gpx_version=DEF_GPX_VERSION, human_namespace=False):
        """Generate a GPX metadata element subtree

        >>> meta = _GpxMeta(time=(2008, 6, 3, 16, 12, 43, 1, 155, 0))
        >>> ET.tostring(meta.togpx())
        '<ns0:metadata xmlns:ns0="http://www.topografix.com/GPX/1/1"><ns0:time>2008-06-03T16:12:43+0000</ns0:time></ns0:metadata>'
        >>> meta.bounds = {"minlat": 52, "maxlat": 54, "minlon": -2,
        ...                "maxlon": 1}
        >>> ET.tostring(meta.togpx())
        '<ns0:metadata xmlns:ns0="http://www.topografix.com/GPX/1/1"><ns0:time>2008-06-03T16:12:43+0000</ns0:time><ns0:bounds maxlat="54" maxlon="1" minlat="52" minlon="-2" /></ns0:metadata>'
        >>> meta.bounds = [point.Point(52.015, -0.221),
        ...                point.Point(52.167, 0.390)]
        >>> ET.tostring(meta.togpx()) # doctest: +ELLIPSIS
        '<ns0:metadata xmlns:ns0="http://www.topografix.com/GPX/1/1"><ns0:time>...</ns0:time><ns0:bounds maxlat="52.167" maxlon="0.39" minlat="52.015" minlon="-0.221" /></ns0:metadata>'

        :type gpx_version: ``str``
        :param gpx_version: GPX version to generate
        :type human_namespace: ``bool``
        :param human_namespace: Whether to generate output using human readable
            namespace prefixes
        :rtype: :class:`ET.Element`
        :return: GPX metadata element

        """
        elementise = partial(create_elem, gpx_version=gpx_version,
                             human_namespace=human_namespace)
        metadata = elementise("metadata", None)
        if self.name:
            metadata.append(elementise("name", None, self.name))
        if self.desc:
            metadata.append(elementise("desc", None, self.desc))
        if self.author:
            element = elementise("author", None)
            if self.author['name']:
                element.append(elementise("name", None, self.author['name']))
            if self.author['email']:
                element.append(elementise("email",
                                          dict(zip(self.author['email'].split("@"),
                                                   ("id", "domain")))))
            if self.author['link']:
                element.append(elementise("link", None, self.author['link']))
            metadata.append(element)
        if self.copyright:
            author = {"author": self.copyright['name']} if self.copyright['name'] else None
            element = elementise("copyright", author)
            if self.copyright['year']:
                element.append(elementise("year", None, self.copyright['year']))
            if self.copyright['license']:
                license = elementise("license", None)
                element.append(license)
            metadata.append(element)
        if self.link:
            for link in self.link:
                if isinstance(link, basestring):
                    element = elementise("link", {"href": link})
                else:
                    element = elementise("link", {"href": link["href"]})
                    if link['text']:
                        element.append(elementise("text", None, link["text"]))
                    if link['type']:
                        element.append(elementise("type", None, link["type"]))
                metadata.append(element)
        element = elementise("time", None)
        if isinstance(self.time, (time.struct_time, tuple)):
            element.text = time.strftime("%Y-%m-%dT%H:%M:%SZ", self.time) # GPX documentation states, the Z on the end should be capital
        elif isinstance(self.time, utils.Timestamp):
            element.text = self.time.isoformat()
        else:
            element.text = time.strftime("%Y-%m-%dT%H:%M:%SZ") # GPX documentation states, the Z on the end should be capital
        metadata.append(element)
        if self.keywords:
            metadata.append(elementise("keywords", None, self.keywords))
        if self.bounds:
            if not isinstance(self.bounds, dict):
                latitudes = list(map(attrgetter("latitude"), self.bounds))
                longitudes = list(map(attrgetter("longitude"), self.bounds))
                bounds = {
                    "minlat": str(min(latitudes)),
                    "maxlat": str(max(latitudes)),
                    "minlon": str(min(longitudes)),
                    "maxlon": str(max(longitudes)),
                }
            else:
                bounds = dict([(k, str(v)) for k, v in self.bounds.items()])
            metadata.append(elementise("bounds", bounds))
        if self.extensions:
            element = elementise("extensions")
            for i in self.extensions:
                element.append(i)
            metadata.append(extensions)
        return metadata

    def import_metadata(self, elements, gpx_version=None):
        """Import information from GPX metadata

        :type elements: :class:`ET.Element`
        :param elements: GPX metadata subtree
        :type gpx_version: ``str``
        :param gpx_version: Specific GPX version entities to import

        """
        if gpx_version:
            try:
                accepted_gpx = {gpx_version: GPX_VERSIONS[gpx_version]}
            except KeyError:
                raise KeyError("Unknown GPX version `%s'" % gpx_version)
        else:
            accepted_gpx = GPX_VERSIONS

        for version, namespace in accepted_gpx.items():
            logging.info("Searching for GPX v%s entries" % version)
            metadata_elem = lambda name: ET.QName(namespace, name)

            for child in elements.getchildren():
                tag_ns, tag_name = child.tag[1:].split("}")
                if not tag_ns == namespace:
                    continue
                if tag_name in ("name", "desc", "keywords"):
                    setattr(self, tag_name, child.text)
                elif tag_name == "time":
                    self.time = utils.Timestamp.parse_isoformat(child.text)
                elif tag_name == "author":
                    self.author["name"] = child.findtext(metadata_elem("name"))
                    aemail = child.find(metadata_elem("email"))
                    if aemail:
                        self.author["email"] = "%s@%s" % (aemail.get("id"),
                                                          aemail.get("domain"))
                    self.author["link"] = child.findtext(metadata_elem("link"))
                elif tag_name == "bounds":
                    self.bounds = {
                        "minlat": child.get("minlat"),
                        "maxlat": child.get("maxlat"),
                        "minlon": child.get("minlon"),
                        "maxlon": child.get("maxlon"),
                    }
                elif tag_name == "extensions":
                    self.extensions = child.getchildren()
                elif tag_name == "copyright":
                    if child.get("author"):
                        self.copyright["name"] = child.get("author")
                    self.copyright["year"] = child.findtext(metadata_elem("year"))
                    self.copyright["license"] = child.findtext(metadata_elem("license"))
                elif tag_name == "link":
                    link = {
                        "href": link.get("href"),
                        "type": child.findtext(metadata_elem("type")),
                        "text": child.findtext(metadata_elem("text")),
                    }
                    self.link.append(link)

class Waypoint(_GpxElem):
    """Class for representing a waypoint element from GPX data files

    .. versionadded:: 0.8.0

    .. seealso::

        :class:`_GpxElem`

    >>> Waypoint(52, 0)
    Waypoint(52.0, 0.0, None, None, None, None)
    >>> Waypoint(52, 0, None)
    Waypoint(52.0, 0.0, None, None, None, None)
    >>> Waypoint(52, 0, "name", "desc")
    Waypoint(52.0, 0.0, 'name', 'desc', None, None)

    """

    __slots__ = ('name', 'description', )

    _elem_name = "wpt"


class Waypoints(point.TimedPoints):
    """Class for representing a group of :class:`Waypoint` objects

    .. versionadded:: 0.8.0

    """

    def __init__(self, gpx_file=None, metadata=None):
        """Initialise a new ``Waypoints`` object"""
        super(Waypoints, self).__init__()
        self.metadata = metadata if metadata else _GpxMeta()
        self._gpx_file = gpx_file
        if gpx_file:
            self.import_locations(gpx_file)

    def import_locations(self, gpx_file, gpx_version=None):
        """Import GPX data files

        ``import_locations()`` returns a list with :class:`Waypoint` objects.

        It expects data files in GPX format, as specified in `GPX 1.1 Schema
        Documentation`_, which is XML such as::

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

        The reader uses the :mod:`ElementTree` module, so should be very fast
        when importing data.  The above file processed by ``import_locations()``
        will return the following ``list`` object::

            [Waypoint(52.015, -0.221, "Home", "My place"),
             Waypoint(52.167, 0.390, "MSR", "Microsoft Research, Cambridge")]

        >>> waypoints = Waypoints(open("gpx"))
        >>> for value in sorted(waypoints, key=attrgetter("name")):
        ...     print(value)
        Home (52°00'54"N, 000°13'15"W on 2008-07-26T00:00:00+00:00) [My place]
        MSR (52°10'01"N, 000°23'24"E on 2008-07-27T00:00:00+00:00) [Microsoft Research, Cambridge]

        :type gpx_file: ``file``, ``list`` or ``str``
        :param gpx_file: GPX data to read
        :type gpx_version: ``str``
        :param gpx_version: Specific GPX version entities to import
        :rtype: ``list``
        :return: Locations with optional comments

        .. _GPX 1.1 Schema Documentation: http://www.topografix.com/GPX/1/1/

        """
        self._gpx_file = gpx_file
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
            metadata = data.find("//" + gpx_elem("metadata"))
            if metadata:
                self.metadata.import_metadata(metadata)
            waypoint_elem = "//" + gpx_elem("wpt")
            name_elem = gpx_elem("name")
            desc_elem = gpx_elem("desc")
            elev_elem = gpx_elem("ele")
            time_elem = gpx_elem("time")

            for waypoint in data.findall(waypoint_elem):
                latitude = waypoint.get("lat")
                longitude = waypoint.get("lon")
                name = waypoint.findtext(name_elem)
                description = waypoint.findtext(desc_elem)
                elevation = waypoint.findtext(elev_elem)
                if elevation:
                    elevation = float(elevation)
                time = waypoint.findtext(time_elem)
                if time:
                    time = utils.Timestamp.parse_isoformat(time)
                self.append(Waypoint(latitude, longitude, name, description,
                                     elevation, time))

    def export_gpx_file(self, gpx_version=DEF_GPX_VERSION,
                        human_namespace=False):
        """Generate GPX element tree from ``Waypoints`` object

        >>> from sys import stdout
        >>> locations = Waypoints(open("gpx"))
        >>> xml = locations.export_gpx_file()
        >>> xml.write(stdout) # doctest: +ELLIPSIS
        <ns0:gpx xmlns:ns0="http://www.topografix.com/GPX/1/1"><ns0:metadata><ns0:time>...</ns0:time><ns0:bounds maxlat="52.167" maxlon="0.39" minlat="52.015" minlon="-0.221" /></ns0:metadata><ns0:wpt lat="52.015" lon="-0.221"><ns0:name>Home</ns0:name><ns0:desc>My place</ns0:desc><ns0:time>2008-07-26T00:00:00+00:00</ns0:time></ns0:wpt><ns0:wpt lat="52.167" lon="0.39"><ns0:name>MSR</ns0:name><ns0:desc>Microsoft Research, Cambridge</ns0:desc><ns0:time>2008-07-27T00:00:00+00:00</ns0:time></ns0:wpt></ns0:gpx>

        :type gpx_version: ``str``
        :param gpx_version: GPX version to generate
        :type human_namespace: ``bool``
        :param human_namespace: Whether to generate output using human readable
            namespace prefixes
        :rtype: :class:`ET.ElementTree`
        :return: GPX element tree depicting ``Waypoints`` object

        """
        gpx = create_elem('gpx', None, None, gpx_version, human_namespace)
        if not self.metadata.bounds:
            self.metadata.bounds = self[:]
        gpx.append(self.metadata.togpx())
        for place in self:
            gpx.append(place.togpx(gpx_version, human_namespace))

        return ET.ElementTree(gpx)


class Trackpoint(_GpxElem):
    """Class for representing a trackpoint element from GPX data files

    .. versionadded:: 0.10.0

    >>> Trackpoint(52, 0)
    Trackpoint(52.0, 0.0, None, None, None, None)
    >>> Trackpoint(52, 0, None)
    Trackpoint(52.0, 0.0, None, None, None, None)
    >>> Trackpoint(52, 0, "name", "desc")
    Trackpoint(52.0, 0.0, 'name', 'desc', None, None)

    .. seealso::

        :class:`_GpxElem`

    """

    __slots__ = ('name', 'description', )

    _elem_name = "trkpt"


class Trackpoints(_SegWrap):
    """Class for representing a group of :class:`Trackpoint` objects

    .. versionadded:: 0.10.0

    """

    def import_locations(self, gpx_file, gpx_version=None):
        """Import GPX data files

        ``import_locations()`` returns a series of lists representing track
        segments with :class:`Trackpoint` objects as contents.

        It expects data files in GPX format, as specified in `GPX 1.1 Schema
        Documentation`_, which is XML such as::

            <?xml version="1.0" encoding="utf-8" standalone="no"?>
            <gpx version="1.1" creator="upoints/0.11.0"
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

        The reader uses the :mod:`ElementTree` module, so should be very fast
        when importing data.  The above file processed by ``import_locations()``
        will return the following ``list`` object::

            [[Trackpoint(52.015, -0.221, "Home", "My place"),
              Trackpoint(52.167, 0.390, "MSR", "Microsoft Research, Cambridge")], ]

        >>> trackpoints = Trackpoints(open("gpx_tracks"))
        >>> for value in sorted(trackpoints[0],
        ...                     key=attrgetter("name")):
        ...     print(value)
        Home (52°00'54"N, 000°13'15"W on 2008-07-26T00:00:00+00:00) [My place]
        MSR (52°10'01"N, 000°23'24"E on 2008-07-27T00:00:00+00:00) [Microsoft Research, Cambridge]

        :type gpx_file: ``file``, ``list`` or ``str``
        :param gpx_file: GPX data to read
        :type gpx_version: ``str``
        :param gpx_version: Specific GPX version entities to import
        :rtype: ``list``
        :return: Locations with optional comments

        .. _GPX 1.1 Schema Documentation: http://www.topografix.com/GPX/1/1/

        """
        self._gpx_file = gpx_file
        data = utils.prepare_xml_read(gpx_file)

        if gpx_version:
            try:
                accepted_gpx = {gpx_version: GPX_VERSIONS[gpx_version]}
            except KeyError:
#                print(GPX_VERSIONS)
                raise KeyError("Unknown GPX version `%s'" % gpx_version)
        else:
            accepted_gpx = GPX_VERSIONS

        for version, namespace in accepted_gpx.items():
            logging.info("Searching for GPX v%s entries" % version)
            """
            modrana:
            get the namespace from the tag
            this change was needed, because the old way of prefix handling was 
            changed to get rid of prefixes in output
            TODO: do this more cleanly"""

            # get just the namespace string
            namespace = data.getroot().tag.split('}')[0]
            namespace = namespace[1:]

            # create a qualified name containing the namespace
            gpx_elem = lambda name: ET.QName(namespace, name).text
            metadata = data.find("//" + gpx_elem("metadata"))
#            print(namespace)
#            print(data.getroot().tag)
#            print(gpx_elem("metadata"))
#            print(metadata)
            if metadata:
                self.metadata.import_metadata(metadata)               
            segment_elem = "//" + gpx_elem("trkseg")
            trackpoint_elem = gpx_elem("trkpt")
            name_elem = gpx_elem("name")
            desc_elem = gpx_elem("desc")
            elev_elem = gpx_elem("ele")
            time_elem = gpx_elem("time")


#            print("segment?")
#            print(data.findall(segment_elem))

            for segment in data.findall(segment_elem):
                points = point.TimedPoints()
                for trackpoint in segment.findall(trackpoint_elem):
                    latitude = trackpoint.get("lat")
                    longitude = trackpoint.get("lon")
                    name = trackpoint.findtext(name_elem)
                    description = trackpoint.findtext(desc_elem)
                    elevation = trackpoint.findtext(elev_elem)
                    if elevation:
                        elevation = float(elevation)
                    time = trackpoint.findtext(time_elem)
                    if time:
                        time = utils.Timestamp.parse_isoformat(time)
                    points.append(Trackpoint(latitude, longitude, name,
                                             description, elevation, time))
                self.append(points)

    def export_gpx_file(self, gpx_version=DEF_GPX_VERSION,
                        human_namespace=False):
        """Generate GPX element tree from ``Trackpoints``

        >>> from sys import stdout
        >>> locations = Trackpoints(open("gpx_tracks"))
        >>> xml = locations.export_gpx_file()
        >>> xml.write(stdout) # doctest: +ELLIPSIS
        <ns0:gpx xmlns:ns0="http://www.topografix.com/GPX/1/1"><ns0:metadata><ns0:time>...</ns0:time><ns0:bounds maxlat="52.167" maxlon="0.39" minlat="52.015" minlon="-0.221" /></ns0:metadata><ns0:trk><ns0:trkseg><ns0:trkpt lat="52.015" lon="-0.221"><ns0:name>Home</ns0:name><ns0:desc>My place</ns0:desc><ns0:time>2008-07-26T00:00:00+00:00</ns0:time></ns0:trkpt><ns0:trkpt lat="52.167" lon="0.39"><ns0:name>MSR</ns0:name><ns0:desc>Microsoft Research, Cambridge</ns0:desc><ns0:time>2008-07-27T00:00:00+00:00</ns0:time></ns0:trkpt></ns0:trkseg></ns0:trk></ns0:gpx>

        :type gpx_version: ``str``
        :param gpx_version: GPX version to generate
        :type human_namespace: ``bool``
        :param human_namespace: Whether to generate output using human readable
            namespace prefixes
        :rtype: :class:`ET.ElementTree`
        :return: GPX element tree depicting ``Trackpoints`` objects

        """
        elementise = partial(create_elem, gpx_version=gpx_version,
                             human_namespace=human_namespace)
        gpx = elementise('gpx', None)
        if not self.metadata.bounds:
            self.metadata.bounds = [j for i in self for j in i]
        gpx.append(self.metadata.togpx())
        track = elementise('trk', None)
        gpx.append(track)
        for segment in self:
            chunk = elementise('trkseg', None)
            track.append(chunk)
            for place in segment:
                chunk.append(place.togpx(gpx_version, human_namespace))

        return ET.ElementTree(gpx)


class Routepoint(_GpxElem):
    """Class for representing a ``rtepoint`` element from GPX data files

    .. versionadded:: 0.10.0

    .. seealso:

         :class:`_GpxElem`

    >>> Routepoint(52, 0)
    Routepoint(52.0, 0.0, None, None, None, None)
    >>> Routepoint(52, 0, None)
    Routepoint(52.0, 0.0, None, None, None, None)
    >>> Routepoint(52, 0, "name", "desc")
    Routepoint(52.0, 0.0, 'name', 'desc', None, None)

    """

    __slots__ = ('name', 'description', )

    _elem_name = "rtept"


class Routepoints(_SegWrap):
    """Class for representing a group of :class:`Routepoint` objects

    .. versionadded:: 0.10.0

    """

    def import_locations(self, gpx_file, gpx_version=None):
        """Import GPX data files

        ``import_locations()`` returns a series of lists representing track
        segments with :class:`Routepoint` objects as contents.

        It expects data files in GPX format, as specified in `GPX 1.1 Schema
        Documentation`_, which is XML such as::

            <?xml version="1.0" encoding="utf-8" standalone="no"?>
            <gpx version="1.1" creator="upoints/0.11.0"
            xmlns="http://www.topografix.com/GPX/1/1"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
              <rte>
                <rtept lat="52.015" lon="-0.221">
                  <name>Home</name>
                  <desc>My place</desc>
                </rtept>
                <rtept lat="52.167" lon="0.390">
                  <name>MSR</name>
                  <desc>Microsoft Research, Cambridge</desc>
                </rtept>
              </rte>
            </gpx>

        The reader uses the :mod:`ElementTree` module, so should be very fast
        when importing data.  The above file processed by ``import_locations()``
        will return the following ``list`` object::

            [[Routepoint(52.015, -0.221, "Home", "My place"),
              Routepoint(52.167, 0.390, "MSR", "Microsoft Research, Cambridge")], ]

        >>> routepoints = Routepoints(open("gpx_routes"))
        >>> for value in sorted(routepoints[0],
        ...                     key=attrgetter("name")):
        ...     print(value)
        Home (52°00'54"N, 000°13'15"W on 2008-07-26T00:00:00+00:00) [My place]
        MSR (52°10'01"N, 000°23'24"E on 2008-07-27T00:00:00+00:00) [Microsoft Research, Cambridge]

        :type gpx_file: ``file``, ``list`` or ``str``
        :param gpx_file: GPX data to read
        :type gpx_version: ``str``
        :param gpx_version: Specific GPX version entities to import
        :rtype: ``list``
        :return: Locations with optional comments

        .. _GPX 1.1 Schema Documentation: http://www.topografix.com/GPX/1/1/

        """
        self._gpx_file = gpx_file
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
            metadata = data.find("//" + gpx_elem("metadata"))
            if metadata:
                self.metadata.import_metadata(metadata)
            route_elem = "//" + gpx_elem("rte")
            routepoint_elem = gpx_elem("rtept")
            name_elem = gpx_elem("name")
            desc_elem = gpx_elem("desc")
            elev_elem = gpx_elem("ele")
            time_elem = gpx_elem("time")

            for route in data.findall(route_elem):
                points = point.TimedPoints()
                for routepoint in route.findall(routepoint_elem):
                    latitude = routepoint.get("lat")
                    longitude = routepoint.get("lon")
                    name = routepoint.findtext(name_elem)
                    description = routepoint.findtext(desc_elem)
                    elevation = routepoint.findtext(elev_elem)
                    if elevation:
                        elevation = float(elevation)
                    time = routepoint.findtext(time_elem)
                    if time:
                        time = utils.Timestamp.parse_isoformat(time)
                    points.append(Routepoint(latitude, longitude, name,
                                             description, elevation, time))
                self.append(points)

    def export_gpx_file(self, gpx_version=DEF_GPX_VERSION,
                        human_namespace=False):
        """Generate GPX element tree from :class:`Routepoints`

        >>> from sys import stdout
        >>> locations = Routepoints(open("gpx_routes"))
        >>> xml = locations.export_gpx_file()
        >>> xml.write(stdout) # doctest: +ELLIPSIS
        <ns0:gpx xmlns:ns0="http://www.topografix.com/GPX/1/1"><ns0:metadata><ns0:time>...</ns0:time><ns0:bounds maxlat="52.167" maxlon="0.39" minlat="52.015" minlon="-0.221" /></ns0:metadata><ns0:rte><ns0:rtept lat="52.015" lon="-0.221"><ns0:name>Home</ns0:name><ns0:desc>My place</ns0:desc><ns0:time>2008-07-26T00:00:00+00:00</ns0:time></ns0:rtept><ns0:rtept lat="52.167" lon="0.39"><ns0:name>MSR</ns0:name><ns0:desc>Microsoft Research, Cambridge</ns0:desc><ns0:time>2008-07-27T00:00:00+00:00</ns0:time></ns0:rtept></ns0:rte></ns0:gpx>

        :type gpx_version: ``str``
        :param gpx_version: GPX version to generate
        :type human_namespace: ``bool``
        :param human_namespace: Whether to generate output using human readable
            namespace prefixes
        :rtype: :class:`ET.ElementTree`
        :return: GPX element tree depicting :class:`Routepoints` objects

        """
        elementise = partial(create_elem, gpx_version=gpx_version,
                             human_namespace=human_namespace)
        gpx = elementise('gpx', None)
        if not self.metadata.bounds:
            self.metadata.bounds = [j for i in self for j in i]
        gpx.append(self.metadata.togpx())
        for rte in self:
            chunk = elementise('rte', None)
            gpx.append(chunk)
            for place in rte:
                chunk.append(place.togpx(gpx_version, human_namespace))

        return ET.ElementTree(gpx)

