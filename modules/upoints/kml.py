#
# vim: set sw=4 sts=4 et tw=80 fileencoding=utf-8:
#
"""kml - Imports KML data files"""
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

from functools import partial
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

from upoints import (point, trigpoints, utils)

# Supported KML versions
KML_VERSIONS = {
  "2.0": "http://earth.google.com/kml/2.0",
  "2.1": "http://earth.google.com/kml/2.1",
  "2.2": "http://earth.google.com/kml/2.2",
} #: Supported KML namespace version to URI mapping

# Changing this will cause tests to fail.
DEF_KML_VERSION = "2.2" #: Default KML version to output

def create_elem(tag, attr=None, kml_version=DEF_KML_VERSION,
                human_namespace=False):
    """Create a partial ``ET.Element`` wrapper with namespace defined

    :Parameters:
        tag : `str`
            Tag name
        attr : `dict`
            Default attributes for tag
        kml_version : `str`
            KML version to use
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
        kml_ns = KML_VERSIONS[kml_version]
    except KeyError:
        raise KeyError("Unknown KML version `%s'" % kml_version)
    if human_namespace:
        ElementTree._namespace_map[kml_ns] = "kml"
        return ElementTree.Element("{%s}%s" % (kml_ns, tag), attr)
    else:
        return ET.Element("{%s}%s" % (kml_ns, tag), attr)

class Placemark(trigpoints.Trigpoint):
    """Class for representing a Placemark element from KML data files

    :since: 0.6.0

    :Ivariables:
        latitude
            Placemark's latitude
        longitude
            Placemark's longitude
        altitude
            Placemark's altitude

    """

    __slots__ = ('description', )

    def __init__(self, latitude, longitude, altitude=None, name=None,
                 description=None):
        """Initialise a new `Placemark` object

        >>> Placemark(52, 0, 4)
        Placemark(52.0, 0.0, 4.0, None, None)
        >>> Placemark(52, 0, None)
        Placemark(52.0, 0.0, None, None, None)
        >>> Placemark(52, 0, None, "name", "desc")
        Placemark(52.0, 0.0, None, 'name', 'desc')

        :Parameters:
            latitude : `float` or coercible to `float`
                Placemarks's latitude
            longitude : `float` or coercible to `float`
                Placemark's longitude
            altitude : `float` or coercible to `float`
                Placemark's altitude
            name : `str`
                Name for placemark
            description : `str`
                Placemark's description

        """
        super(Placemark, self).__init__(latitude, longitude, altitude, name)

        if altitude:
            self.altitude = float(altitude)
        self.description = description

    def __str__(self, mode="dms"):
        """Pretty printed location string

        >>> print(Placemark(52, 0, 4))
        52°00'00"N, 000°00'00"E alt 4m
        >>> print(Placemark(52, 0, None))
        52°00'00"N, 000°00'00"E
        >>> print(Placemark(52, 0, None, "name", "desc"))
        name (52°00'00"N, 000°00'00"E) [desc]
        >>> print(Placemark(52, 0, 42, "name", "desc"))
        name (52°00'00"N, 000°00'00"E alt 42m) [desc]

        :Parameters:
            mode : `str`
                Coordinate formatting system to use
        :rtype: `str`
        :return: Human readable string representation of `Placemark` object

        """
        location = super(Placemark, self).__str__(mode)
        if self.description:
            return "%s [%s]" % (location, self.description)
        else:
            return location

    def tokml(self, kml_version=DEF_KML_VERSION, human_namespace=False):
        """Generate a KML Placemark element subtree

        >>> ET.tostring(Placemark(52, 0, 4).tokml())
        '<ns0:Placemark xmlns:ns0="http://earth.google.com/kml/2.2"><ns0:Point><ns0:coordinates>0.0,52.0,4</ns0:coordinates></ns0:Point></ns0:Placemark>'
        >>> ET.tostring(Placemark(52, 0, 4, "Cambridge").tokml())
        '<ns0:Placemark id="Cambridge" xmlns:ns0="http://earth.google.com/kml/2.2"><ns0:name>Cambridge</ns0:name><ns0:Point><ns0:coordinates>0.0,52.0,4</ns0:coordinates></ns0:Point></ns0:Placemark>'
        >>> ET.tostring(Placemark(52, 0, 4).tokml(kml_version="2.0"))
        '<ns0:Placemark xmlns:ns0="http://earth.google.com/kml/2.0"><ns0:Point><ns0:coordinates>0.0,52.0,4</ns0:coordinates></ns0:Point></ns0:Placemark>'
        >>> ET.tostring(Placemark(52, 0, 4, "Cambridge", "in the UK").tokml())
        '<ns0:Placemark id="Cambridge" xmlns:ns0="http://earth.google.com/kml/2.2"><ns0:name>Cambridge</ns0:name><ns0:description>in the UK</ns0:description><ns0:Point><ns0:coordinates>0.0,52.0,4</ns0:coordinates></ns0:Point></ns0:Placemark>'

        :Parameters:
            kml_version : `str`
                KML version to generate
            human_namespace : `bool`
                Whether to generate output using human readable
                namespace prefixes
        :rtype: ``ET.Element``
        :return: KML Placemark element

        """
        element = partial(create_elem, kml_version=kml_version,
                          human_namespace=human_namespace)
        placemark = element("Placemark")
        if self.name:
            placemark.set("id", self.name)
            nametag = element("name")
            nametag.text = self.name
        if self.description:
            desctag = element("description")
            desctag.text = self.description
        tpoint = element("Point")
        coords = element("coordinates")

        data = [str(self.longitude), str(self.latitude)]
        if self.altitude:
            if int(self.altitude) == self.altitude:
                data.append("%i" % self.altitude)
            else:
                data.append(str(self.altitude))
        coords.text = ",".join(data)

        if self.name:
            placemark.append(nametag)
        if self.description:
            placemark.append(desctag)
        placemark.append(tpoint)
        tpoint.append(coords)

        return placemark


class Placemarks(point.KeyedPoints):
    """Class for representing a group of `Placemark` objects

    :since: 0.6.0

    """

    def __init__(self, kml_file=None):
        """Initialise a new `Placemarks` object"""
        super(Placemarks, self).__init__()
        if kml_file:
            self.import_locations(kml_file)

    def import_locations(self, kml_file, kml_version=None):
        """Import KML data files

        `import_locations()` returns a dictionary with keys containing the
        section title, and values consisting of `Placemark` objects.

        It expects data files in KML format, as specified in `KML Reference
        <http://code.google.com/apis/kml/documentation/kml_tags_21.html>`__,
        which is XML such as::

            <?xml version="1.0" encoding="utf-8"?>
            <kml xmlns="http://earth.google.com/kml/2.1">
                <Document>
                    <Placemark id="Home">
                        <name>Home</name>
                        <Point>
                            <coordinates>-0.221,52.015,60</coordinates>
                        </Point>
                    </Placemark>
                    <Placemark id="Cambridge">
                        <name>Cambridge</name>
                        <Point>
                            <coordinates>0.390,52.167</coordinates>
                        </Point>
                    </Placemark>
                </Document>
            </kml>

        The reader uses `Python <http://www.python.org/>`__'s `ElementTree`
        module, so should be very fast when importing data.  The above file
        processed by `import_locations()` will return the following `dict`
        object::

            {"Home": Placemark(52.015, -0.221, 60),
             "Cambridge": Placemark(52.167, 0.390, None)}

        >>> locations = Placemarks(open("kml"))
        >>> for value in sorted(locations.values(),
        ...                     key=lambda x: x.name.lower()):
        ...     print(value)
        Cambridge (52°10'01"N, 000°23'24"E)
        Home (52°00'54"N, 000°13'15"W alt 60m)

        The `kml_version` parameter allows the caller to specify the specific
        KML version that should be processed, this allows the caller to process
        inputs which contain entries in more than one namespace without
        duplicates resulting from entries in being specified with different
        namespaces.

        :Parameters:
            kml_file : `file`, `list` or `str`
                KML data to read
            kml_version : `str`
                Specific KML version entities to import
        :rtype: `dict`
        :return: Named locations with optional comments

        """
        data = utils.prepare_xml_read(kml_file)

        if kml_version:
            try:
                accepted_kml = {kml_version: KML_VERSIONS[kml_version]}
            except KeyError:
                raise KeyError("Unknown KML version `%s'" % kml_version)
        else:
            accepted_kml = KML_VERSIONS

        for version, namespace in accepted_kml.items():
            logging.info("Searching for KML v%s entries" % version)
            kml_elem = lambda name: ET.QName(namespace, name).text
            placemark_elem = "//" + kml_elem("Placemark")
            name_elem = kml_elem("name")
            coords_elem = kml_elem("Point") + "/" + kml_elem("coordinates")
            desc_elem = kml_elem("description")

            for place in data.findall(placemark_elem):
                name = place.findtext(name_elem)
                coords = place.findtext(coords_elem)
                if coords is None:
                    logging.info("No coordinates found for `%s' entry" % name)
                    continue
                coords = coords.split(",")
                if len(coords) == 2:
                    longitude, latitude = coords
                    altitude = None
                elif len(coords) == 3:
                    longitude, latitude, altitude = coords
                else:
                    raise ValueError("Unable to handle coordinates value `%s'"
                                     % coords)
                description = place.findtext(desc_elem)
                self[name] = Placemark(latitude, longitude, altitude, name,
                                       description)

    def export_kml_file(self, kml_version=DEF_KML_VERSION,
                        human_namespace=False):
        """Generate KML element tree from `Placemarks`

        >>> from sys import stdout
        >>> locations = Placemarks(open("kml"))
        >>> xml = locations.export_kml_file()
        >>> xml.write(stdout)
        <ns0:kml xmlns:ns0="http://earth.google.com/kml/2.2"><ns0:Document><ns0:Placemark id="Home"><ns0:name>Home</ns0:name><ns0:Point><ns0:coordinates>-0.221,52.015,60</ns0:coordinates></ns0:Point></ns0:Placemark><ns0:Placemark id="Cambridge"><ns0:name>Cambridge</ns0:name><ns0:Point><ns0:coordinates>0.39,52.167</ns0:coordinates></ns0:Point></ns0:Placemark></ns0:Document></ns0:kml>
        >>> xml = locations.export_kml_file("2.0")
        >>> xml.write(stdout)
        <ns0:kml xmlns:ns0="http://earth.google.com/kml/2.0"><ns0:Document><ns0:Placemark id="Home"><ns0:name>Home</ns0:name><ns0:Point><ns0:coordinates>-0.221,52.015,60</ns0:coordinates></ns0:Point></ns0:Placemark><ns0:Placemark id="Cambridge"><ns0:name>Cambridge</ns0:name><ns0:Point><ns0:coordinates>0.39,52.167</ns0:coordinates></ns0:Point></ns0:Placemark></ns0:Document></ns0:kml>

        :Parameters:
            kml_version : `str`
                KML version to generate
            human_namespace : `bool`
                Whether to generate output using human readable
                namespace prefixes
        :rtype: ``ET.ElementTree``
        :return: KML element tree depicting `Placemarks`

        """
        element = partial(create_elem, kml_version=kml_version,
                          human_namespace=human_namespace)
        kml = element('kml')
        doc = element('Document')
        for place in self.values():
            doc.append(place.tokml(kml_version, human_namespace))
        kml.append(doc)

        return ET.ElementTree(kml)

