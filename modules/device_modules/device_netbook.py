# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# An a generic netbook device module.
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
from core.constants import DEVICE_TYPE_DESKTOP


def getModule(*args, **kwargs):
    return DeviceNetbook(*args, **kwargs)


class DeviceNetbook(DeviceModule):
    """A netbook modRana device-specific module"""

    def __init__(self, *args, **kwargs):
        DeviceModule.__init__(self, *args, **kwargs)

    @property
    def device_id(self):
        return "netbook"

    @property
    def device_name(self):
        return "A generic netbook"

    @property
    def window_wh(self):
        return 1024, 600

    @property
    def start_in_fullscreen(self):
        return False

    @property
    def supported_gui_module_ids(self):
        return ["GTK", "qt5"]

    @property
    def device_type(self):
        return DEVICE_TYPE_DESKTOP