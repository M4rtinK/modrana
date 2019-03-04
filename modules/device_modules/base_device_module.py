from __future__ import with_statement  # for Python 2.5
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Base class for Rana device-specific modules
# * it inherits everything in the base module
# * ads some default functions and handling,
#   that can be overridden for a specific devices
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
from core import constants
from modules.base_module import RanaModule
from core.signal import Signal

import sys
import os
import logging
PYTHON3 = sys.version_info[0] > 2

class DeviceModule(RanaModule):
    """A modRana device module"""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self.internetConnectivityChanged = Signal()

    @property
    def device_id(self):
        """
        return an unique string identifying the device module
        """
        return None

    @property
    def device_name(self):
        """return a "human" name of the device"""
        return "unknown device"

    @property
    def window_wh(self):
        """
        return the preferred application window size in pixels
        """
        # we'll use VGA as a default value
        return 640, 480

    @property
    def start_in_fullscreen(self):
        """weather or not to start modRana in fullscreen
        NOTE: this is a default value and can be overridden by a
        user-set options key, etc."""
        return False

    @property
    def fullscreen_only(self):
        """
        some platforms are basically fullscreen-only (Harmattan),
        as applications only switch between fullscreen and a task switcher
        """
        return False

    @property
    def screen_blanking_control_supported(self):
        """ there is no universal way to control screen blanking,
        so its off by default
        -> it can be implemented and enabled in the corresponding device module"""
        return False

    def pause_screen_blanking(self):
        """
        calling this method should pause screen blanking
        * on mobile devices, screen balking needs to be paused every n seconds
        * on desktop, one call might be enough, still, several calls should
        be handled without issues
        * also what about restoring the screen blanking on Desktop
        once modRana exits ?
        """
        pass

    @property
    def uses_dashboard(self):
        """report if the device minimizes the windows into a dashboard instead of hiding
        them out of view - the user might want that the window redraws on the dashboard or not"""
        return False

    @property
    def supported_gui_module_ids(self):
        """supported GUI module IDs, ordered by preference from left to right

        THE ":" NOTATION
        single GUI modules might support different subsets, the usability of
        these subsets can vary based on the current platform
        -> this functions enabled device modules to report which GUI subsets
        are most suitable for the given platform
        -> the string starts with the module id prefix, is separated by : and
        continues with the subset id

        EXAMPLE:
        ["qt5:silica","qt5:controls2","GTK"]
        -> Qt 5 GUI with Silica Components is preferred,
        -> Qt 5 GUI with Qt Quick Controls 2 is less preferred
        -> the "classic" GTK 2 GUI is set as a fallback if everything else fails

        NOTE: it's unlikely an real platform that can host both Silica,
              Controls 2 & GTK2 GUI exists

        CURRENT USAGE
        Actually none since the QML UI was deprecated, but I guess it could be used
        in the future to switch Universal Component backends.
        """
        return ["GTK", "qt5"] # as default try GTK first and then the Qt 5 GUI

    @property
    def handles_location(self):
        """report whether the device module handles position updates by itself"""
        return False

    @property
    def location_type(self):
        """modRana uses gpsd by default"""
        return 'gpsd'

    @property
    def use_simple_map_dragging(self):
        """should we use a fast but less fluent
        or nice and but slow(-er) map dragging method ?
           by default, we use the nice method
        """
        return False

    @property
    def long_press_click_skip_count(self):
        """how many clicks to skip after a long press is detected and exercised
        * this might be device specific, as for example SHR on the Neo FreeRunner
        fires two clicks after lp, but Maemo on N900 fires just one
        * default value -> 1
         * should work for Maemo and normal PC Linuxes (Ubuntu)
        """
        return 1

    def text_entry_imminent(self):
        """text entry box will be shown after this method finishes
           - on some platforms, there are some steps needed to make sure
           it is actually visible (like disabling fullscreen, etc.)"""
        pass

    def text_entry_done(self):
        """we are done with text entry, so all the needed steps can be reversed again
           (enable fullscreen, etc.)"""
        pass

    @property
    def has_custom_notification_support(self):
        """report if the device provides its own notification method"""
        return False

    def notify(self, message, msTimeout=0, icon=""):
        """send a notification"""
        pass

    @property
    def has_keyboard(self):
        """report if the device has a keyboard"""
        return True

    @property
    def has_buttons(self):
        """report if the device has some usable buttons other than keyboard"""
        if self.has_volume_keys:
            return True
        else:
            return False

    @property
    def has_volume_keys(self):
        """report if the device has application-usable volume control keys or their
        equivalent - basically just two nearby button that can be used for zooming up/down,
        skipping to next/last and similar actions"""
        return False

    def enable_volume_keys(self):
        pass

    def start_location(self, start_main_loop=False):
        """start handling location - check handles_location if this is supported"""
        pass

    def stop_location(self):
        """stop handling location - check handles_location if this is supported"""
        pass

    @property
    def profile_path(self):
        """Return path to the main profile folder or None
        if default path should be used.

        :returns: path to the profile folder or None
        :rtype: str or None
        """
        return None

    @property
    def tracklog_folder_path(self):
        """return device specific tracklog folder or None if default should be used"""
        return None

    @property
    def map_folder_path(self):
        """return device specific map folder or None if default should be used"""
        return None

    @property
    def routing_data_folder_path(self):
        """return device specific map folder or None if default should be used"""
        return None

    @property
    def poi_folder_path(self):
        """return device specific POI folder or None if default should be used"""
        return None

    def _getLog(self):
        deviceModuleSuffix = ".".join(self._importName.split("_", 1))
        # this should turn "device_n900" to device.n900,
        # which together with the "mod" prefix should
        # result in a nice "mod.device.n900" logger hierarchy
        return logging.getLogger("mod.%s" % deviceModuleSuffix)

    @property
    def log_folder_path(self):
        """default path is handled through the options module"""
        return None

    @property
    def cache_folder_path(self):
        """Return path to the cache folder or None to use default"""
        return None

    @property
    def needs_quit_button(self):
        """On some platforms (Android chroot) applications
        need to provide their own shutdown buttons"""
        return False

    @property
    def needs_back_button(self):
        """Some platforms (Jolla) don't need a in-UI back button"""
        return True

    @property
    def needs_page_background(self):
        """Some platforms (Jolla) don't need a page background"""
        return True

    @property
    def handles_url_opening(self):
        """
        report if opening of URI is handled by the device module
        * for example, on the N900 a special DBUS command not available
        elsewhere needs to be used
        """
        return False

    def open_url(self, url):
        """
        open an URL
        """
        pass

    @property
    def connectivity_status(self):
        """report the current status of internet connectivity on the device
        None - status reporting not supported or status unknown
        True - connected to the Internet
        False - disconnected from the Internet
        """
        connected = constants.OFFLINE
        # open the /proc/net/route file
        #with open('/proc/net/route', 'rc') as f:

        openMode = "r"
        if not PYTHON3:
            openMode = "rc"
            # TODO: check if this is still needed on Python 2.5
            # on the N900
            
        with open('/proc/net/route', openMode) as f:
            for line in f:
                # the line is delimited by tabulators
                lineSplit = line.split('\t')
                # check if the length is valid
                if len(lineSplit) >= 11:
                    if lineSplit[1] == '00000000' and lineSplit[7] == '00000000':
                        # if destination and mask are 00000000,
                        # it is probably an Internet connection
                        connected = constants.ONLINE
                        break
        return connected

    def enable_internet_connectivity(self):
        """try to make sure that the device connects to the internet"""
        # TODO: respect the modRana internet connectivity state
        pass

    @property
    def start_drag_distance(self):
        """Distance in pixel for discerning drag from a click
        A correct start drag distance is important on high DPI screens
        as the default values don't work correctly on them.
        """
        return None

    @property
    def device_type(self):
        """Returns type of the current device

        The device can currently be either a PC
        (desktop or laptop/notebook),
        smartphone or a tablet.
        This is currently used mainly for rough
        DPI estimation.
        Example:
        * high resolution & PC -> low DPI
        * high resolution & smartphone -> high DPI
        * high resolution & smartphone -> low DPI

        This could also be used in the future to
        use different PC/smartphone/tablet GUI styles.

        By default, the device type is unknown.
        """
        return None

    @property
    def default_theme(self):
        """Some platforms might need a tweaked default theme,
        this property can be used to set it.

        :returns: default theme tuple for the given platform
        or tuple based on default theme constants if the given
        platform has no default theme set
        :rtype: a (theme_id, theme_name) tuple
        """
        return constants.DEFAULT_THEME_ID, constants.DEFAULT_THEME_NAME

    @property
    def defaultTileStorageType(self):
        """Default tile storage type for the platform
        Some platforms might not heavy issues with many small files
        and there might be a bigger possibility of sharing tile files
        with other mapping applications. On other platforms storing
        many small files might be very inefficient or there might be
        other issues such as the files being indexed into a gallery,
        etc.

        :returns: default tile storage type
        :rtype: str
        """
        return constants.DEFAULT_TILE_STORAGE_TYPE

    # offline routing
    @property
    def offline_routing_providers(self):
        """Offline routing providers available on the platform.

        :returns: list of available offline routing providers
        :rtype: list
        """
        return []

    @property
    def monav_light_binary_path(self):
        return "/usr/bin/monav-light"

    @property
    def qmlscene_command(self):
        """What should be called to start the qmlscene.

        :returns: command to run to start qmlscene
        :rtype: str
        """
        return "qmlscene"

    @property
    def universal_components_backend(self):
        """Path to a Universal Components backend suitable for the given platform.

        We default to the Controls UC backend.

        :returns: path to suitable UC backend
        :rtype: str
        """
        return "controls"

#  def getAutorotationSupported(self):
#    return False
#
#  def getAutorotationenabled(self):
#    pass
#
#  def getAutorotationState(self):
#    pass
#
#  def enableAutorotation(self):
#    pass
#
#  def disableAutorotation(self):
#    pass
