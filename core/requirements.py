# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# ModRana check and acquire various requirements
#----------------------------------------------------------------------------
# Copyright 2013, Martin Kolman
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

import time
from core import constants
from core.point import Point
from core.singleton import modrana

def _nop():
    return []

def locateCurrentPosition(controller=None):
    """Try to locate current position and return it when done or time out"""
    result = None
    sleepTime = 0.5 # in seconds
    pos = modrana.get('pos', None)
    fix = modrana.get('fix', 1)
    # check if GPS usage is explicitly disabled in modRana
    gpsEnabled = modrana.get('GPSEnabled')
    if gpsEnabled == False:
        if pos:
            modrana.notify("GPS OFF, using last known position", 5000)
            return Point(*pos)
        else:
            modrana.notify("GPS OFF, no last known position", 5000)
            return None

    if fix > 1 and pos:
        return Point(*pos)  # fix found, return it at once

    # check if GPS hardware has been enabled
    location = modrana.m.get("location")
    if not location.enabled:
        # location usage has not be disabled but location
        # has not been started, so start location
        location.startLocation()

    # wait for the fix
    startTimestamp = time.time()
    elapsed = 0
    if controller:
        controller.status = "GPS fix in progress"
    while elapsed < constants.LOCATION_TIMEOUT:
        pos = modrana.get('pos', None)
        fix = modrana.get('fix', 1)
        if fix > 1 and pos:
            break
        time.sleep(sleepTime)
        elapsed = time.time() - startTimestamp
    if fix > 1 and pos: # got GPS fix ?
        return Point(*pos)
    else: # no GPS lock
        pos = modrana.get("pos")
        if pos:
            modrana.notify("no fix, using last known position", 5000)
            return Point(*pos)
        else:
            modrana.notify("failed to get GPS fix", 5000)
            return None

def checkConnectivity(controller=None):
    """Check for Internet connectivity - if no Internet connectivity is available,
    wait for up to 30 seconds and then fail (this is used to handle cases where
    the device was offline and the Internet connection is just being established)"""
    status = modrana.dmod.getInternetConnectivityStatus()
    if status is constants.CONNECTIVITY_UNKNOWN: # Connectivity status monitoring not supported
        return status # skip
    elif status is constants.ONLINE:
        return status # Internet connectivity is most probably available
    elif status is constants.OFFLINE:
        startTimestamp = time.time()
        elapsed = 0
        if controller:
            controller.status = "waiting for Internet connectivity"
        while elapsed < constants.INTERNET_CONNECTIVITY_TIMEOUT:
            status = modrana.dmod.getInternetConnectivityStatus()
            print('requirements: waiting for internet connectivity')
            print(status)
            if status == True or status is None:
                break
            # check if the thread was cancelled
            if controller and controller.callback is None:
                # the thread was cancelled
                print("requirements: connectivity status check cancelled")
                status = constants.CONNECTIVITY_UNKNOWN
                break
            time.sleep(1)
            elapsed = time.time() - startTimestamp
        if status is constants.OFFLINE:
            modrana.notify("requirements: failed to connect to the Internet")
        return status
    else:
        print('requirements: warning, unknown connection status:')
        print(status)
        return status


# Decorators

def gps(function):
    """Check if the given function requires GPS and try to provide it"""
    def wrapper(*args, **kwargs):
        # check if GPS is needed
        controller=kwargs.get("controller")
        needsGPS = kwargs.get("gps")
        if needsGPS:
            del kwargs["gps"]
            pos = locateCurrentPosition(controller=controller)
            if pos:
                kwargs["around"] = pos  # feed the position as the around argument
            else:
                # requirements not fulfilled,
                # just run a no-op function and don't call the callback
                controller.callback = None
                return _nop()
        # requirement fulfilled,
        # call the wrapped function
        return function(*args, **kwargs)
    return wrapper

def internet(function):
    """Check if the given function requires Internet and try to provide it"""
    def wrapper(*args, **kwargs):
        # check if GPS is needed
        controller=kwargs.get("controller")
        # tell the device module we need Internet connectivity
        modrana.dmod.enableInternetConnectivity()
        # check if it is available
        status = checkConnectivity(controller=controller)
        if status is constants.OFFLINE:
            # requirements not fulfilled,
            # just run a no-op function and don't call the callback
            if controller:
                controller.callback = None
            return _nop()

        # requirement fulfilled,
        # call the wrapped function
        return function(*args, **kwargs)
    return wrapper

def needsAround(function):
    """If there is no "around" location in kwargs,
    enable the GPS requirement, as the current position
    is needed to be set to the around variable"""
    def wrapper(*args, **kwargs):
        # check if Around is provided and not None

        around = kwargs.get("around")
        if not around:
            kwargs["gps"] = True

        # requirement fulfilled,
        # call the wrapped function
        return function(*args, **kwargs)
    return wrapper
