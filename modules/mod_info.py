# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# A modRana module providing various kinds of information.
#----------------------------------------------------------------------------
# Copyright 2007, Oliver White
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
from core.point import Point
from core.i18n import _

def getModule(*args, **kwargs):
    return Info(*args, **kwargs)


class Info(RanaModule):
    """A modRana information handling module"""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self.versionString = "unknown version"
        currentVersionString = self.modrana.paths.version_string
        if currentVersionString is not None:
            # check version string validity
            self.versionString = currentVersionString


        self._dirPoint = None
        dirPoint = self.get("directionPointLatLon", None)
        if dirPoint:
            lat, lon = dirPoint
            self._dirPoint = Point(lat, lon)

    @property
    def pay_pal_url(self):
        return "https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=martin%2ekolman%40gmail%2ecom&lc=CZ&item_name=The%20modRana%20project&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donate_LG%2egif%3aNonHosted"

    @property
    def flattr_url(self):
        return "https://flattr.com/thing/678708/modRana-flexible-GPS-navigation-system"

    @property
    def gratipay_url(self):
        return "https://gratipay.com/M4rtinK"

    @property
    def bitcoin_address(self):
        return "14DXzkqqYCfSG5vZNYPnPiZzg3wW2hXsE8"

    @property
    def discussions(self):
        """List of modRana-relevant discussions, with the most relevant discussion on top."""
        return [("http://talk.maemo.org/showthread.php?t=58861", _("talk.maemo.org thread"))]

    @property
    def main_discussion(self):
        """Url for the most relevant modRana discussion."""
        return self.discussions[0]

    @property
    def website_url(self):
        """Url to the modRana homepage."""
        return "http://www.modrana.org"

    @property
    def source_repository_url(self):
        """Link to the modRana source code."""
        return "https://github.com/M4rtinK/modrana"

    @property
    def translation_url(self):
        """Url for the modRana translation project."""
        return "https://www.transifex.com/martink/modrana"

    @property
    def email_address(self):
        """ModRana project email address."""
        return "modrana@gmail.com"

    def handleMessage(self, message, messageType, args):
        if message == "setPoint":
            # open the coordinates entry dialog
            entry = self.m.get('textEntry', None)
            if entry:
                initialText = ""
                dirPoint = self.get("directionPointLatLon", None)
                if dirPoint:
                    initialText = "%f,%f" % dirPoint
                entry.entryBox(self, 'directionPointCoordinates', 'Coordinates (Example: 1.23,4.56)', initialText=initialText)
        elif message == "clearPoint":
            self._dirPoint = None
            self.set("directionPointLatLon" ,None)