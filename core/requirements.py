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
import functools
from core import constants
from core.point import Point
from core.singleton import modrana

import logging
log = logging.getLogger("core.requirements")

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
        location.start_location()

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
    status = modrana.dmod.connectivity_status
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
            status = modrana.dmod.connectivity_status
            log.info('waiting for internet connectivity')
            log.info(status)
            if status == True or status is None:
                break
            # check if the thread was cancelled
            if controller and controller.callback is None:
                # the thread was cancelled
                log.info("connectivity status check cancelled")
                status = constants.CONNECTIVITY_UNKNOWN
                break
            time.sleep(1)
            elapsed = time.time() - startTimestamp
        if status is constants.OFFLINE:
            modrana.notify("requirements: failed to connect to the Internet")
        return status
    else:
        log.warning('warning, unknown connection status:')
        log.warning(status)
        return status

def gps(conditional=False):
    """The given function requires GPS,
    start it and wait for a fix or timeout

    :param kwargTrigger: if the key specified is in kwargs of the
    wrapped function and it's value evaluates to true, then start GPS
    :type kwargTrigger: hashable type other than None
    """
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            # check if GPS is needed
            controller=kwargs.get("controller")
            needsGPS = True
            if conditional:
                needsGPS = kwargs.get("gps")
            if needsGPS:
                del kwargs["gps"]  # not needed by the wrapped function
                pos = locateCurrentPosition(controller=controller)
                if pos:
                    kwargs["around"] = pos  # feed the position as the around argument
                else:
                    # requirements not fulfilled,
                    # disable the callback and return an empty list
                    if controller:
                        controller.callback = None
                    return []
            # requirement fulfilled,
            # call the wrapped function
            return function(*args, **kwargs)
        return wrapper
    return decorator

def internet(function):
    """The given function requires Internet, start it
    and wait for it to connect or timeout
    """
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        controller=kwargs.get("controller")
        # tell the device module we need Internet connectivity
        modrana.dmod.enable_internet_connectivity()
        # check if it is available
        status = checkConnectivity(controller=controller)
        if status is constants.OFFLINE:
            # requirement not fulfilled (we are offline),
            # disable the callback and return an empty list
            if controller:
                controller.callback = None
            return []
        # requirement fulfilled,
        # call the wrapped function
        return function(*args, **kwargs)
    return wrapper


def startGPS(conditional=False):
    """Start GPS

    :param conditional: if true, check for the "gps"
    key in the kwargs of the wrapped function,
    if the value evaluates as True, start GPS
    :type conditional: bool
    """
    def decorate(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            start = True
            # check if the kwargs trigger is enabled
            if conditional:
                start = kwargs.get("gps")
            # check if GPS usage is enabled in modRana
            gpsEnabled = modrana.get('GPSEnabled')
            if start and gpsEnabled:
                location = modrana.m.get('location')
                if location:
                    location.start_location()

            return function(*args, **kwargs)
        return wrapper
    return decorate

def startInternet(function):
    """Start Internet"""

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        # tell the device module we need Internet connectivity
        modrana.dmod.enable_internet_connectivity()

        return function(*args, **kwargs)
    return wrapper


def needsAround(function):
    """If there is no "around" location in kwargs,
    enable the GPS requirement, as the current position
    is needed to be set to the around variable"""

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        # check if Around is provided and not None

        around = kwargs.get("around")
        if not around:
            kwargs["gps"] = True
        else:
            kwargs["gps"] = False

        # requirement fulfilled,
        # call the wrapped function
        return function(*args, **kwargs)
    return wrapper
