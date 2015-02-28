# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Supplies position from a textfile
#---------------------------------------------------------------------------
# Copyright 2007-2008, Oliver White
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
#---------------------------------------------------------------------------
from modules.base_module import RanaModule
import sys
import os
import socket
from time import sleep
import re


def getModule(*args, **kwargs):
    return PosFromFile(*args, **kwargs)


class PosFromFile(RanaModule):
    """Supplies position info from GPSD"""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)

    def update(self):
        filename = self.get('pos_filename', 'pos.txt')
        if not os.path.exists(filename):
            self.status = "File not available"
            return
        try:
            file = open(filename, 'r')
        except IOError:
            self.status = "Can't open file"
        text = file.readline(50)
        file.close()
        try:
            lat, lon = [float(i) for i in text.rstrip().split(",")]
            self.set('pos', (lat, lon))
            self.set('pos_source', 'file')
            self.status = "OK"
            return {'valid': True, 'lat': lat, 'lon': lon, 'source': 'textfile'}
        except ValueError:
            self.status = "Invalid file"


if __name__ == "__main__":
    d = {'pos_filename': 'pos.txt'}
    a = PosFromFile({}, d)
    for i in range(5):
        a.update()
        print("%s: %s" % (a.getStatus(), d.get('pos', None)))
        sleep(3)
