# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Sample of a modRana device-specific module.
# It is a basic modRana module, that has some special features
# and is loaded only on the correpsponding device.
#----------------------------------------------------------------------------
# Copyright 2010, Martin Kolman
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
from modules.device_modules.base_device_module import DeviceModule
from core.constants import DEVICE_TYPE_SMARTPHONE

import logging
log = logging.getLogger("device.nemo")

QTM_IMPORT_SUCCESS = False
try:
    from QtMobility.SystemInfo import QSystemScreenSaver

    QTM_IMPORT_SUCCESS = True
except Exception:
    log.exception('QtMobility import failed - do you have python-qtmobility installed ?')
# ^^ back-light control for QML GUI

# NOTE: use the device_ prefix when naming the module

def getModule(m, d, i):
    return DeviceNemo(m, d, i)


class DeviceNemo(DeviceModule):
    """A Nokia N9 device module"""

    def __init__(self, m, d, i):
        DeviceModule.__init__(self, m, d, i)
        # create the screen-saver controller
        self.qScreenSaver = QSystemScreenSaver()

    def getDeviceIDString(self):
        return "nemo"

    def getDeviceName(self):
        return "Nemo Mobile device"

    def getWinWH(self):
        """N9/N950 screen resolution"""
        #TODO: handle different Nemo devices ?
        return 854, 480

    def startInFullscreen(self):
        """
        non-fullscreen mode just draw some weird toolbar & status-bar
        on Harmattan
        """
        return True

    def fullscreenOnly(self):
        """
        basically no need to
        """
        return True

    def screenBlankingControlSupported(self):
        """
        Screen blanking support is handled through Qt Mobility
        """
        return QTM_IMPORT_SUCCESS

    def pauseScreenBlanking(self):
        """
        inhibit screen blanking
        """
        QSystemScreenSaver.setScreenSaverInhibit(self.qScreenSaver)

    def getSupportedGUIModuleIds(self):
        return ["QML:harmattan", "QML:indep"]

    # as python-qtmobility currently segfaults
    # when asked for location info,
    # use the default (GPSD = no position) for now
    #  def getLocationType(self):
    #    return "qt_mobility"

    def hasButtons(self):
        # TODO: support for volume buttons
        return False


    # ** LOCATION **

    def handlesLocation(self):
        """using Qt Mobility"""
        return False

    def startLocation(self):
        pass

    def stopLocation(self):
        pass


    # ** PATHS **

    # as nemo currently doesn't have a MyDocs partition or
    # equivalent, just use the default paths in ~/.modrana

    def needsQuitButton(self):
        """No need for a separate Quit button thanks to the Nemo UI"""
        return False

    @property
    def getDeviceType(self):
        # TODO: amend once some Nemo tablets show up
        return DEVICE_TYPE_SMARTPHONE
