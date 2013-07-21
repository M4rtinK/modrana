# -*- coding: utf-8 -*-
#
# gPodder - A media aggregator and podcast client
# Copyright (c) 2005-2010 Thomas Perl and the gPodder Team
#
# gPodder is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# gPodder is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import dbus

import hildon
import osso

# Replace this with your own gettext() functionality
#import gpodder
#_ = gpodder.gettext
#_ = "_"


class FremantleRotation(object):
    """thp's screen rotation for Maemo 5

    Simply instantiate an object of this class and let it auto-rotate
    your StackableWindows depending on the device orientation.

    If you need to relayout a window, connect to its "configure-event"
    signal and measure the ratio of width/height and relayout for that.

    You can set the mode for rotation to AUTOMATIC (default), NEVER or
    ALWAYS with the set_mode() method.
    """
    AUTOMATIC, NEVER, ALWAYS = range(3)

    # Human-readable captions for the above constants
    MODE_CAPTIONS = ('Automatic', 'Landscape', 'Portrait')

    # Privately-used constants
    _PORTRAIT, _LANDSCAPE = ('portrait', 'landscape')
    _ENABLE_ACCEL = 'req_accelerometer_enable'
    _DISABLE_ACCEL = 'req_accelerometer_disable'

    # Defined in mce/dbus-names.h
    _MCE_SERVICE = 'com.nokia.mce'
    _MCE_REQUEST_PATH = '/com/nokia/mce/request'
    _MCE_REQUEST_IF = 'com.nokia.mce.request'

    # sysfs device name for the keyboard slider switch
    KBD_SLIDER = '/sys/devices/platform/gpio-switch/slide/state'
    _KBD_OPEN = 'open'
    _KBD_CLOSED = 'closed'

    def __init__(self, app_name, main_window=None, version='1.0', mode=0):
        """Create a new rotation manager

        app_name    ... The name of your application (for osso.Context)
        main_window ... The root window (optional, hildon.StackableWindow)
        version     ... The version of your application (optional, string)
        mode        ... Initial mode for this manager (default: AUTOMATIC)
        """
        self._orientation = None
        self._main_window = main_window
        self._stack = hildon.WindowStack.get_default()
        self._mode = -1
        self._last_dbus_orientation = None
        self._keyboard_state = self._get_keyboard_state()
        app_id = '-'.join((app_name, self.__class__.__name__))
        self._osso_context = osso.Context(app_id, version, False)
        program = hildon.Program.get_instance()
        program.connect('notify::is-topmost', self._on_topmost_changed)
        system_bus = dbus.Bus.get_system()
        system_bus.add_signal_receiver(self._on_orientation_signal,
                                       signal_name='sig_device_orientation_ind',
                                       dbus_interface='com.nokia.mce.signal',
                                       path='/com/nokia/mce/signal')

        system_bus.add_signal_receiver(self._on_keyboard_signal,
                                       signal_name='Condition',
                                       dbus_interface='org.freedesktop.Hal.Device',
                                       path='/org/freedesktop/Hal/devices/platform_slide')
        self.set_mode(mode)

        # check for current orientation - the first signal comes after and orientation change,
        # so if the device is already in portrait when the app is launched, it won't
        # rotate to the correct orientation before being oriented to landscape and back

        mceRequest = system_bus.get_object('com.nokia.mce', '/com/nokia/mce/request')
        dir(mceRequest)
        orientationInfo = mceRequest.get_device_orientation()
        # send a fake CB with current orientation info
        self._on_orientation_signal(*orientationInfo)

    def get_mode(self):
        """Get the currently-set rotation mode

        This will return one of three values: AUTOMATIC, ALWAYS or NEVER.
        """
        return self._mode

    def set_mode(self, new_mode):
        """Set the rotation mode

        You can set the rotation mode to AUTOMATIC (use hardware rotation
        info), ALWAYS (force portrait) and NEVER (force landscape).
        """
        if new_mode not in (self.AUTOMATIC, self.ALWAYS, self.NEVER):
            raise ValueError('Unknown rotation mode')

        if self._mode != new_mode:
            if self._mode == self.AUTOMATIC:
                # Remember the current "automatic" orientation for later
                self._last_dbus_orientation = self._orientation
                # Tell MCE that we don't need the accelerometer anymore
                self._send_mce_request(self._DISABLE_ACCEL)

            if new_mode == self.NEVER:
                self._orientation_changed(self._LANDSCAPE)
            elif new_mode == self.ALWAYS and \
                            self._keyboard_state != self._KBD_OPEN:
                self._orientation_changed(self._PORTRAIT)
            elif new_mode == self.AUTOMATIC:
                # Restore the last-known "automatic" orientation
                self._orientation_changed(self._last_dbus_orientation)
                # Tell MCE that we need the accelerometer again
                self._send_mce_request(self._ENABLE_ACCEL)

            self._mode = new_mode

    def _send_mce_request(self, request):
        rpc = osso.Rpc(self._osso_context)
        rpc.rpc_run(self._MCE_SERVICE,
                    self._MCE_REQUEST_PATH,
                    self._MCE_REQUEST_IF,
                    request,
                    use_system_bus=True)

    def _on_topmost_changed(self, program, property_spec):
        # XXX: This seems to never get called on Fremantle(?)
        if self._mode == self.AUTOMATIC:
            if program.get_is_topmost():
                self._send_mce_request(self._ENABLE_ACCEL)
            else:
                self._send_mce_request(self._DISABLE_ACCEL)

    def _get_main_window(self):
        if self._main_window:
            # If we have gotten the main window as parameter, return it and
            # don't try "harder" to find another window using the stack
            return self._main_window
        else:
            # The main window is at the "bottom" of the window stack, and as
            # the list we get with get_windows() is sorted "topmost first", we
            # simply take the last item of the list to get our main window
            windows = self._stack.get_windows()
            if windows:
                return windows[-1]
            else:
                return None

    def _orientation_changed(self, orientation):
        if self._orientation == orientation:
            # Ignore repeated requests
            return

        flags = 0

        if orientation != self._LANDSCAPE:
            flags |= hildon.PORTRAIT_MODE_SUPPORT

        if orientation == self._PORTRAIT:
            flags |= hildon.PORTRAIT_MODE_REQUEST

        window = self._get_main_window()
        if window is not None:
            hildon.hildon_gtk_window_set_portrait_flags(window, flags)

        self._orientation = orientation

    def _get_keyboard_state(self):
        # For sbox, if the device does not exist assume that it's closed
        try:
            return open(self.KBD_SLIDER).read().strip()
        except IOError:
            return self._KBD_CLOSED

    def _keyboard_state_changed(self):
        state = self._get_keyboard_state()

        if state == self._KBD_OPEN:
            self._orientation_changed(self._LANDSCAPE)
        elif state == self._KBD_CLOSED:
            if self._mode == self.AUTOMATIC:
                self._orientation_changed(self._last_dbus_orientation)
            elif self._mode == self.ALWAYS:
                self._orientation_changed(self._PORTRAIT)

        self._keyboard_state = state

    def _on_keyboard_signal(self, condition, button_name):
        if condition == 'ButtonPressed' and button_name == 'cover':
            self._keyboard_state_changed()

    def _on_orientation_signal(self, orientation, stand, face, x, y, z):
        if orientation in (self._PORTRAIT, self._LANDSCAPE):
            if self._mode == self.AUTOMATIC and \
                            self._keyboard_state != self._KBD_OPEN:
                # Automatically set the rotation based on hardware orientation
                self._orientation_changed(orientation)

            # Save the current orientation for "automatic" mode later on
            self._last_dbus_orientation = orientation

