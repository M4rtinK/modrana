#
# vim: set sw=4 sts=4 et tw=80 fileencoding=utf-8:
#
"""cellid - Imports OpenCellID data files"""
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

import datetime

from upoints import (point, utils)

class Cell(point.Point):
    """Class for representing a cellular cite from OpenCellID.org

    :since: 0.11.0

    :Ivariables:
        ident : `int`
            OpenCellID database identifier
        latitude
            Cell's latitude
        longitude
            Cell's longitude
        mcc
            Cell's country code
        mnc
            Cell's network code
        lac
            Cell's local area code
        cellid
            Cell's identifier
        crange
            Cell's range
        samples
            Number of samples for the cell
        created
            Date the cell was first entered
        updated
            Date of the last update

    """

    __slots__ = ('ident', 'mcc', 'mnc', 'lac', 'cellid', 'crange', 'samples',
                 'created', 'updated')

    def __init__(self, ident, latitude, longitude, mcc, mnc, lac, cellid,
                 crange, samples, created, updated):
        """Initialise a new `Cell` object

        >>> Cell(4, 52.015, -0.221, 21, 46, 40000, 10, 0, 1,
        ...      datetime.datetime(2008, 4, 15, 15, 21, 35),
        ...      datetime.datetime(2008, 4, 15, 15, 28, 49))
        Cell(4, 52.015, -0.221, 21, 46, 40000, 10, 0, 1,
             datetime.datetime(2008, 4, 15, 15, 21, 35),
             datetime.datetime(2008, 4, 15, 15, 28, 49))

        :Parameters:
            ident : `int`
                OpenCellID database identifier
            latitude : `float`
                Cell's latitude
            longitude : `float`
                Cell's longitude
            mcc : `int`
                Cell's country code
            mnc : `int`
                Cell's network code
            lac : `int`
                Cell's local area code
            cellid : `int`
                Cell's identifier
            crange : `int`
                Cell's range
            samples : `int`
                Number of samples for the cell
            created : `datetime.datetime`
                Date the cell was first entered
            updated : `datetime.datetime`
                Date of the last update

        """
        super(Cell, self).__init__(latitude, longitude)
        self.ident = ident
        self.mcc = mcc
        self.mnc = mnc
        self.lac = lac
        self.cellid = cellid
        self.crange = crange
        self.samples = samples
        self.created = created
        self.updated = updated

    def __str__(self, mode=None):
        """OpenCellID.org-style location string

        :see: `point.Point`

        >>> print(Cell(4, 52.015, -0.221, 21, 46, 40000, 10, 0, 1,
        ...       datetime.datetime(2008, 4, 15, 15, 21, 35),
        ...       datetime.datetime(2008, 4, 15, 15, 28, 49)))
        4,52.0150000000000,-0.221000000000000,21,46,40000,10,0,1,2008-04-15 15:21:35,2008-04-15 15:28:49

        :Parameters:
            mode : any
                For compatibility with parent class
        :rtype: `str`
        :return: OpenCellID.org-style string representation of `Cell` object

        """
        return "%i,%.13f,%.15f,%i,%i,%i,%i,%i,%i,%s,%s" \
            % (self.ident, self.latitude, self.longitude, self.mcc, self.mnc,
               self.lac, self.cellid, self.crange, self.samples,
               self.created.strftime("%Y-%m-%d %H:%M:%S"),
               self.updated.strftime("%Y-%m-%d %H:%M:%S"))


class Cells(point.KeyedPoints):
    """Class for representing a group of `Cell` objects

    :since: 0.11.0

    """

    def __init__(self, cells_file=None):
        """Initialise a new `Cells` object"""
        super(Cells, self).__init__()
        if cells_file:
            self.import_locations(cells_file)

    def __str__(self):
        """`Cells` objects rendered as export from OpenCellID.org

        >>> cells = Cells(open("cells"))
        >>> print(cells)
        22747,52.0438995361328,-0.224637001752853,234,33,2319,647,0,1,2008-04-05 21:32:40,2008-04-05 21:32:40
        22995,52.3305015563965,-0.225562006235123,234,10,20566,4068,0,1,2008-04-05 21:32:59,2008-04-05 21:32:59
        23008,52.3506011962891,-0.223410993814468,234,10,10566,4068,0,1,2008-04-05 21:32:59,2008-04-05 21:32:59

        :rtype: `str`
        :return: OpenCellID.org formatted output

        """
        return "\n".join(map(str, sorted(self.values(), key=lambda x: x.ident)))

    def import_locations(self, cells_file):
        """Parse OpenCellID.org data files

        `import_locations()` returns a dictionary with keys containing the
        `OpenCellID <http://opencellid.org>`__ database identifier, and values
        consisting of a `Cell` objects.

        It expects cell files in the following format::

            22747,52.0438995361328,-0.224637001752853,234,33,2319,647,0,1,2008-04-05 21:32:40,2008-04-05 21:32:40
            22995,52.3305015563965,-0.225562006235123,234,10,20566,4068,0,1,2008-04-05 21:32:59,2008-04-05 21:32:59
            23008,52.3506011962891,-0.223410993814468,234,10,10566,4068,0,1,2008-04-05 21:32:59,2008-04-05 21:32:59

        The above file processed by `import_locations()` will return the
        following `dict` object::

            {23008: Cell(23008, 52.3506011963, -0.223410993814, 234, 10, 10566,
                         4068, 0, 1, datetime.datetime(2008, 4, 5, 21, 32, 59),
                         datetime.datetime(2008, 4, 5, 21, 32, 59)),
             22747: Cell(22747, 52.0438995361, -0.224637001753, 234, 33, 2319,
                         647, 0, 1, datetime.datetime(2008, 4, 5, 21, 32, 40),
                         datetime.datetime(2008, 4, 5, 21, 32, 40)),
             22995: Cell(22995, 52.3305015564, -0.225562006235, 234, 10, 20566,
                         4068, 0, 1, datetime.datetime(2008, 4, 5, 21, 32, 59),
                         datetime.datetime(2008, 4, 5, 21, 32, 59))}

        >>> cells = Cells(open("cells"))
        >>> for value in sorted(cells.values(), key=lambda x: x.ident):
        ...     print(value)
        22747,52.0438995361328,-0.224637001752853,234,33,2319,647,0,1,2008-04-05 21:32:40,2008-04-05 21:32:40
        22995,52.3305015563965,-0.225562006235123,234,10,20566,4068,0,1,2008-04-05 21:32:59,2008-04-05 21:32:59
        23008,52.3506011962891,-0.223410993814468,234,10,10566,4068,0,1,2008-04-05 21:32:59,2008-04-05 21:32:59

        :Parameters:
            cells_file : `file`, `list` or `str`
                Cell data to read
        :rtype: `dict`
        :return: Cell data with their associated database identifier

        """
        self._cells_file = cells_file
        field_names = ("ident", "latitude", "longitude", "mcc", "mnc", "lac",
                       "cellid", "crange", "samples", "created", "updated")
        parse_date = lambda s: datetime.datetime.strptime(s,
                                                          "%Y-%m-%d %H:%M:%S")
        field_parsers = (int, float, float, int, int, int, int, int, int,
                         parse_date, parse_date)
        data = utils.prepare_csv_read(cells_file, field_names)

        for row in data:
            for name, parser in zip(field_names, field_parsers):
                row[name] = parser(row[name])
            self[row['ident']] = Cell(**row)

