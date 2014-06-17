#
# vim: set sw=4 sts=4 et tw=80 fileencoding=utf-8:
#
"""osm - Imports OpenStreetMap data files"""
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
import urllib

from operator import attrgetter
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

from . import (__version__, point, utils)

def _parse_flags(element):
    """Parse OSM XML element for generic data

    :type element: :class:`ET.Element`
    :param element: Element to parse
    :rtype: ``tuple``
    :return: Generic OSM data for object instantiation

    """
    visible = True if element.get("visible") else False
    user = element.get("user")
    timestamp = element.get("timestamp")
    if timestamp:
        timestamp = utils.Timestamp.parse_isoformat(timestamp)
    tags = {}
    for tag in element.findall("tag"):
        key = tag.get("k")
        value = tag.get("v")
        tags[key] = value

    return visible, user, timestamp, tags

def _get_flags(osm_obj):
    """Create element independent flags output

    :type osm_obj: :class:`Node`
    :param osm_obj: Object with OSM-style metadata
    :rtype: ``list``
    :return: Human readable flags output

    """
    flags = []
    if osm_obj.visible:
        flags.append("visible")
    if osm_obj.user:
        flags.append("user: %s" % osm_obj.user)
    if osm_obj.timestamp:
        flags.append("timestamp: %s" % osm_obj.timestamp.isoformat())
    if osm_obj.tags:
        flags.append(", ".join("%s: %s" % (k, v)
                               for k, v in osm_obj.tags.items()))
    return flags

def get_area_url(location, distance):
    """Generate URL for downloading OSM data within a region

    This function defines a boundary box where the edges touch a circle of
    ``distance`` kilometres in radius.  It is important to note that the box is
    neither a square, nor bounded within the circle.

    The bounding box is strictly a trapezoid whose north and south edges are
    different lengths, which is longer is dependant on whether the box is
    calculated for a location in the Northern or Southern hemisphere.  You will
    get a shorter north edge in the Northern hemisphere, and vice versa.  This
    is simply because we are applying a flat transformation to a spherical
    object, however for all general cases the difference will be negligible.

    >>> get_area_url(point.Point(52.015, -0.221), 3)
    'http://api.openstreetmap.org/api/0.5/map?bbox=-0.264864438253,51.9880034021,-0.177135561747,52.0419965979'
    >>> get_area_url(point.Point(52.015, -0.221), 12)
    'http://api.openstreetmap.org/api/0.5/map?bbox=-0.396457433591,51.9070136086,-0.045542566409,52.1229863914'

    :type location: :class:`Point`-like object
    :param location: Centre of the region
    :type distance: ``int``
    :param distance: Boundary distance in kilometres
    :rtype: ``str``
    :return: URL that can be used to fetch the OSM data within ``distance`` of
        ``location``

    """
    locations = [location.destination(i, distance) for i in range(0, 360, 90)]
    latitudes = map(attrgetter("latitude"), locations)
    longitudes = map(attrgetter("longitude"), locations)

    bounds = (min(longitudes), min(latitudes), max(longitudes), max(latitudes))

    return ("http://api.openstreetmap.org/api/0.5/map?bbox="
            + ",".join(map(str, bounds)))


class Node(point.Point):
    """Class for representing a node element from OSM data files

    .. versionadded:: 0.9.0

    """

    __slots__ = ('ident', 'visible', 'user', 'timestamp', 'tags')

    def __init__(self, ident, latitude, longitude, visible=False, user=None,
                 timestamp=None, tags=None):
        """Initialise a new ``Node`` object

        >>> Node(0, 52, 0)
        Node(0, 52.0, 0.0, False, None, None, None)
        >>> Node(0, 52, 0, True, "jnrowe", utils.Timestamp(2008, 1, 25))
        Node(0, 52.0, 0.0, True, 'jnrowe',
             Timestamp(2008, 1, 25, 0, 0), None)
        >>> Node(0, 52, 0, tags={"key": "value"})
        Node(0, 52.0, 0.0, False, None, None, {'key': 'value'})

        :type ident: ``int``
        :param ident: Unique identifier for the node
        :type latitude: ``float`` or coercible to ``float``
        :param latitude: Nodes's latitude
        :type longitude: ``float`` or coercible to ``float``
        :param longitude: Node's longitude
        :type visible: ``bool``
        :param visible: Whether the node is visible
        :type user: ``str``
        :param user: User who logged the node
        :type timestamp: ``str``
        :param timestamp: The date and time a node was logged
        :type tags: ``dict``
        :param tags: Tags associated with the node

        """
        super(Node, self).__init__(latitude, longitude)

        self.ident = ident
        self.visible = visible
        self.user = user
        self.timestamp = timestamp
        self.tags = tags

    def __str__(self, mode="dms"):
        """Pretty printed location string

        >>> print(Node(0, 52, 0))
        Node 0 (52°00'00"N, 000°00'00"E)
        >>> print(Node(0, 52, 0, True, "jnrowe",
        ...            utils.Timestamp(2008, 1, 25)))
        Node 0 (52°00'00"N, 000°00'00"E) [visible, user: jnrowe, timestamp:
        2008-01-25T00:00:00+00:00]
        >>> print(Node(0, 52, 0, tags={"key": "value"}))
        Node 0 (52°00'00"N, 000°00'00"E) [key: value]

        :type mode: ``str``
        :param mode: Coordinate formatting system to use
        :rtype: ``str``
        :return: Human readable string representation of ``Node`` object

        """
        text = ["Node %i (%s)" % (self.ident, super(Node, self).__str__(mode)), ]
        flags = _get_flags(self)

        if flags:
            text.append("[%s]" % ", ".join(flags))
        return " ".join(text)

    def toosm(self):
        """Generate a OSM node element subtree

        >>> ET.tostring(Node(0, 52, 0).toosm())
         '<node id="0" lat="52.0" lon="0.0" visible="false" />'
        >>> ET.tostring(Node(0, 52, 0, True, "jnrowe",
        ...                  utils.Timestamp(2008, 1, 25)).toosm())
        '<node id="0" lat="52.0" lon="0.0" timestamp="2008-01-25T00:00:00+00:00" user="jnrowe" visible="true" />'
        >>> ET.tostring(Node(0, 52, 0, tags={"key": "value"}).toosm())
        '<node id="0" lat="52.0" lon="0.0" visible="false"><tag k="key" v="value" /></node>'

        :rtype: :class:`ET.Element`
        :return: OSM node element

        """
        node = ET.Element("node", {"id": str(self.ident),
                                   "lat": str(self.latitude),
                                   "lon": str(self.longitude)})
        node.set("visible", "true" if self.visible else "false")
        if self.user:
            node.set("user", self.user)
        if self.timestamp:
            node.set("timestamp", self.timestamp.isoformat())
        if self.tags:
            for key, value in self.tags.items():
                tag = ET.Element("tag", {"k": key, "v": value})
                node.append(tag)

        return node

    def get_area_url(self, distance):
        """Generate URL for downloading OSM data within a region

        >>> Home = Node(0, 52, 0)
        >>> Home.get_area_url(3)
        'http://api.openstreetmap.org/api/0.5/map?bbox=-0.0438497383115,51.9730034021,0.0438497383115,52.0269965979'
        >>> Home.get_area_url(12)
        'http://api.openstreetmap.org/api/0.5/map?bbox=-0.175398634277,51.8920136086,0.175398634277,52.1079863914'

        :type distance: ``int``
        :param distance: Boundary distance in kilometres
        :rtype: ``str``
        :return: URL that can be used to fetch the OSM data within ``distance``
            of ``location``

        """
        return get_area_url(self, distance)

    def fetch_area_osm(self, distance):
        """Fetch, and import, an OSM region

        >>> Home = Node(0, 52, 0)
        >>> # The following test is skipped, because the Osm object doesn't
        >>> # support a reliable way __repr__ method.
        >>> Home.fetch_area_osm(3) # doctest: +SKIP

        :type distance: ``int``
        :param distance: Boundary distance in kilometres
        :rtype: :class:`Osm`
        :return: All the data OSM has on a region imported for use

        """
        return Osm(urllib.urlopen(get_area_url(self, distance)))

    @staticmethod
    def parse_elem(element):
        """Parse a OSM node XML element

        :type element: :class:`ET.Element`
        :param element: XML Element to parse
        :rtype: ``Node``
        :return: ``Node`` object representing parsed element

        """
        ident = int(element.get("id"))
        latitude = element.get("lat")
        longitude = element.get("lon")

        flags = _parse_flags(element)

        return Node(ident, latitude, longitude, *flags)


class Way(point.Points):
    """Class for representing a way element from OSM data files

    .. versionadded:: 0.9.0

    """

    __slots__ = ('ident', 'visible', 'user', 'timestamp', 'tags')

    def __init__(self, ident, nodes, visible=False, user=None, timestamp=None,
                 tags=None):
        """Initialise a new ``Way`` object

        :type ident: ``int``
        :param ident: Unique identifier for the way
        :type nodes: ``list`` of ``str`` objects
        :param nodes: Identifiers of the nodes that form this way
        :type visible: ``bool``
        :param visible: Whether the way is visible
        :type user: ``str``
        :param user: User who logged the way
        :type timestamp: ``str``
        :param timestamp: The date and time a way was logged
        :type tags: ``dict``
        :param tags: Tags associated with the way

        """
        super(Way, self).__init__()

        self.extend(nodes)

        self.ident = ident
        self.visible = visible
        self.user = user
        self.timestamp = timestamp
        self.tags = tags

    def __repr__(self):
        """Self-documenting string representation

        >>> Way(0, (0, 1, 2))
        Way(0, [0, 1, 2], False, None, None, None)
        >>> Way(0, (0, 1, 2), True, "jnrowe", utils.Timestamp(2008, 1, 25))
        Way(0, [0, 1, 2], True, 'jnrowe', Timestamp(2008, 1, 25, 0, 0),
            None)
        >>> Way(0, (0, 1, 2), tags={"key": "value"})
        Way(0, [0, 1, 2], False, None, None, {'key': 'value'})

        :rtype: ``str``
        :return: String to recreate ``Way`` object

        """
        return utils.repr_assist(self, {"nodes": self[:]})

    def __str__(self, nodes=False):
        """Pretty printed location string

        >>> print(Way(0, (0, 1, 2)))
        Way 0 (nodes: 0, 1, 2)
        >>> print(Way(0, (0, 1, 2), True, "jnrowe",
        ...           utils.Timestamp(2008, 1, 25)))
        Way 0 (nodes: 0, 1, 2) [visible, user: jnrowe, timestamp: 2008-01-25T00:00:00+00:00]
        >>> print(Way(0, (0, 1, 2), tags={"key": "value"}))
        Way 0 (nodes: 0, 1, 2) [key: value]
        >>> nodes = [
        ...     Node(0, 52.015749, -0.221765, True, "jnrowe",
        ...          utils.Timestamp(2008, 1, 25, 12, 52, 11), None),
        ...     Node(1, 52.015761, -0.221767, True, None,
        ...          utils.Timestamp(2008, 1, 25, 12, 53, 14),
        ...          {"created_by": "hand", "highway": "crossing"}),
        ...     Node(2, 52.015754, -0.221766, True, "jnrowe",
        ...          utils.Timestamp(2008, 1, 25, 12, 52, 30),
        ...          {"amenity": "pub"}),
        ... ]
        >>> print(Way(0, (0, 1, 2), tags={"key": "value"}).__str__(nodes))
        Way 0 [key: value]
            Node 0 (52°00'56"N, 000°13'18"W) [visible, user: jnrowe, timestamp: 2008-01-25T12:52:11+00:00]
            Node 1 (52°00'56"N, 000°13'18"W) [visible, timestamp: 2008-01-25T12:53:14+00:00, highway: crossing, created_by: hand]
            Node 2 (52°00'56"N, 000°13'18"W) [visible, user: jnrowe, timestamp: 2008-01-25T12:52:30+00:00, amenity: pub]

        :type nodes: ``list``
        :param nodes: Nodes to be used in expanding references
        :rtype: ``str``
        :return: Human readable string representation of ``Way`` object

        """
        text = ["Way %i" % (self.ident), ]
        if not nodes:
            text.append(" (nodes: %s)" % str(self[:])[1:-1])
        flags = _get_flags(self)

        if flags:
            text.append(" [%s]" % ", ".join(flags))
        if nodes:
            text.append("\n")
            text.append("\n".join("    %s" % nodes[node] for node in self[:]))

        return "".join(text)

    def toosm(self):
        """Generate a OSM way element subtree

        >>> ET.tostring(Way(0, (0, 1, 2)).toosm())
        '<way id="0" visible="false"><nd ref="0" /><nd ref="1" /><nd ref="2" /></way>'
        >>> ET.tostring(Way(0, (0, 1, 2), True, "jnrowe",
        ...                 utils.Timestamp(2008, 1, 25)).toosm())
        '<way id="0" timestamp="2008-01-25T00:00:00+00:00" user="jnrowe" visible="true"><nd ref="0" /><nd ref="1" /><nd ref="2" /></way>'
        >>> ET.tostring(Way(0, (0, 1, 2), tags={"key": "value"}).toosm())
        '<way id="0" visible="false"><tag k="key" v="value" /><nd ref="0" /><nd ref="1" /><nd ref="2" /></way>'

        :rtype: :class:`ET.Element`
        :return: OSM way element

        """
        way = ET.Element("way", {"id": str(self.ident)})
        way.set("visible", "true" if self.visible else "false")
        if self.user:
            way.set("user", self.user)
        if self.timestamp:
            way.set("timestamp", self.timestamp.isoformat())
        if self.tags:
            for key, value in self.tags.items():
                tag = ET.Element("tag", {"k": key, "v": value})
                way.append(tag)

        for node in self:
            tag = ET.Element("nd", {"ref": str(node)})
            way.append(tag)

        return way

    @staticmethod
    def parse_elem(element):
        """Parse a OSM way XML element

        :type element: :class:`ET.Element`
        :param element: XML Element to parse
        :rtype: ``Way``
        :return: `Way` object representing parsed element

        """
        ident = int(element.get("id"))
        flags = _parse_flags(element)
        nodes = [node.get("ref") for node in element.findall("nd")]
        return Way(ident, nodes, *flags)


class Osm(point.Points):
    """Class for representing an OSM region

    .. versionadded:: 0.9.0

    """

    def __init__(self, osm_file=None):
        """Initialise a new ``Osm`` object"""
        super(Osm, self).__init__()
        self._osm_file = osm_file
        if osm_file:
            self.import_locations(osm_file)
        self.generator = "upoints/%s" % __version__
        self.version = "0.5"

    def import_locations(self, osm_file):
        """Import OSM data files

        ``import_locations()`` returns a list of ``Node`` and ``Way`` objects.

        It expects data files conforming to the `OpenStreetMap 0.5 DTD`_, which
        is XML such as::

            <?xml version="1.0" encoding="UTF-8"?>
            <osm version="0.5" generator="upoints/0.9.0">
              <node id="0" lat="52.015749" lon="-0.221765" user="jnrowe" visible="true" timestamp="2008-01-25T12:52:11+00:00" />
              <node id="1" lat="52.015761" lon="-0.221767" visible="true" timestamp="2008-01-25T12:53:00+00:00">
                <tag k="created_by" v="hand" />
                <tag k="highway" v="crossing" />
              </node>
              <node id="2" lat="52.015754" lon="-0.221766" user="jnrowe" visible="true" timestamp="2008-01-25T12:52:30+00:00">
                <tag k="amenity" v="pub" />
              </node>
              <way id="0" visible="true" timestamp="2008-01-25T13:00:00+0000">
                <nd ref="0" />
                <nd ref="1" />
                <nd ref="2" />
                <tag k="ref" v="My Way" />
                <tag k="highway" v="primary" />
              </way>
            </osm>

        The reader uses the :mod:`ElementTree` module, so should be very fast
        when importing data.  The above file processed by ``import_locations()``
        will return the following `Osm` object::

            Osm([
                Node(0, 52.015749, -0.221765, True, "jnrowe",
                     utils.Timestamp(2008, 1, 25, 12, 52, 11), None),
                Node(1, 52.015761, -0.221767, True,
                     utils.Timestamp(2008, 1, 25, 12, 53), None,
                     {"created_by": "hand", "highway": "crossing"}),
                Node(2, 52.015754, -0.221766, True, "jnrowe",
                     utils.Timestamp(2008, 1, 25, 12, 52, 30),
                     {"amenity": "pub"}),
                Way(0, [0, 1, 2], True, None,
                    utils.Timestamp(2008, 1, 25, 13, 00),
                    {"ref": "My Way", "highway": "primary"})],
                generator="upoints/0.9.0")

        >>> region = Osm(open("osm"))
        >>> for node in sorted([x for x in region if isinstance(x, Node)],
        ...                    key=attrgetter("ident")):
        ...     print(node)
        Node 0 (52°00'56"N, 000°13'18"W) [visible, user: jnrowe, timestamp: 2008-01-25T12:52:11+00:00]
        Node 1 (52°00'56"N, 000°13'18"W) [visible, timestamp: 2008-01-25T12:53:00+00:00, highway: crossing, created_by: hand]
        Node 2 (52°00'56"N, 000°13'18"W) [visible, user: jnrowe, timestamp: 2008-01-25T12:52:30+00:00, amenity: pub]

        :type osm_file: ``file``, ``list`` or ``str``
        :param osm_file: OpenStreetMap data to read
        :rtype: ``Osm``
        :return: Nodes and ways from the data

        .. _OpenStreetMap 0.5 DTD:
            http://wiki.openstreetmap.org/index.php/OSM_Protocol_Version_0.5/DTD

        """
        self._osm_file = osm_file
        data = utils.prepare_xml_read(osm_file)

        # This would be a lot simpler if OSM exports defined a namespace
        root = data.getroot()
        if not root.tag == "osm":
            raise ValueError("Root element `%s' is not `osm'" % root.tag)
        self.version = root.get("version")
        if not self.version:
            raise ValueError("No specified OSM version")
        elif not self.version == "0.5":
            raise ValueError("Unsupported OSM version `%s'" % root)

        self.generator = root.get("generator")

        for elem in root.getchildren():
            if elem.tag == "node":
                self.append(Node.parse_elem(elem))
            elif elem.tag == "way":
                self.append(Way.parse_elem(elem))

    def export_osm_file(self):
        """Generate OpenStreetMap element tree from `Osm`

        >>> from sys import stdout
        >>> region = Osm(open("osm"))
        >>> xml = region.export_osm_file()
        >>> xml.write(stdout) # doctest: +ELLIPSIS
        <osm generator="upoints/..." version="0.5"><node id="0" lat="52.015749" lon="-0.221765" timestamp="2008-01-25T12:52:11+00:00" user="jnrowe" visible="true" /><node id="1" lat="52.015761" lon="-0.221767" timestamp="2008-01-25T12:53:00+00:00" visible="true"><tag k="highway" v="crossing" /><tag k="created_by" v="hand" /></node><node id="2" lat="52.015754" lon="-0.221766" timestamp="2008-01-25T12:52:30+00:00" user="jnrowe" visible="true"><tag k="amenity" v="pub" /></node><way id="0" timestamp="2008-01-25T13:00:00+00:00" visible="true"><tag k="ref" v="My Way" /><tag k="highway" v="primary" /><nd ref="0" /><nd ref="1" /><nd ref="2" /></way></osm>

        """
        osm = ET.Element('osm', {"generator": self.generator,
                                 "version": self.version})
        for obj in self:
            osm.append(obj.toosm())

        return ET.ElementTree(osm)

