#!/usr/bin/python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# modRana logging
#----------------------------------------------------------------------------
# Copyright 2014, Martin Kolman
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
from __future__ import with_statement  # Python 2.5 compatibility

import logging
import logging.handlers
import os
import gzip
import sys
import threading

from core import utils
from core import qrc

ANDROID_SPECIAL_LOG_FOLDER = "/sdcard/modrana_debug_logs"

log_manager = None


class FilterAll(logging.Filter):
    """A filter tha filters out all log messages"""

    def filter(self, record):
        return False


class LogManager(object):
    def __init__(self):
        """Initialize logging for modRana
        Logging is quite important as a one never knows when a bug shows
        up and it is important to know what was modRana doing at that time.
        """

        self._log_folder_path = None
        self._file_handler = None
        self._log_file_enabled = False
        self._log_file_enabled_lock = threading.RLock()
        self._log_file_path = None
        self._log_file_compression = False
        self._compressed_log_file = None
        self._log_file_override = False
        self._filterAll = FilterAll()
        self._stdoutLoggingDisabled = False

        # create main modRana logger (root logger)
        self._root_modrana_logger = logging.getLogger('')
        self._root_modrana_logger.setLevel(logging.DEBUG)
        # name is undocumented and might blow up in the future ^_-
        self._root_modrana_logger.name = ""

        # create log for the core modules
        self._core_logger = logging.getLogger('core')
        self._core_logger.setLevel(logging.DEBUG)

        # create a log for non-core/standalone/feature specific modules
        # (BaseModule subclasses)
        self._mod_logger = logging.getLogger('mod')
        self._mod_logger.setLevel(logging.DEBUG)

        # as we set the root logger to accept even debug messages,
        # we need to explicitly tell urllib3 to skip debug level
        # messages
        urllib3_logger = logging.getLogger("urllib3")
        urllib3_logger.setLevel(logging.ERROR)

        # create console handler that prints everything to stdout
        # (as was done previously by just using print)
        self._console_handler = logging.StreamHandler()
        self._console_handler.setLevel(logging.DEBUG)

        # create formatters and add them to the handlers
        # omit some stuff when printing to console to make the logs fit to terminal windows
        console_formatter = logging.Formatter('%(levelname)s %(name)s: %(message)s')
        # file viewers should be able to handle longer lines
        self._console_handler.setFormatter(console_formatter)

        # also, the file log can't be created and opened at once as modRana needs to load
        # and consult the persistent settings database first, but we don't want to loose
        # any early log messages
        # * solution -> MemoryLogHandler stores the log messages and is either flushed to the
        #   log file or discarded when modRana discovers that logging to file is disabled
        self._memory_handler = logging.handlers.MemoryHandler(capacity = 1024*10)
        self._memory_handler.setLevel(logging.DEBUG)

        # now we attach the console and memory handlers to the root modRana logger
        # * like this all messages should arrive in the handlers
        self._root_modrana_logger.addHandler(self._console_handler)
        self._root_modrana_logger.addHandler(self._memory_handler)

        # check if we are running on Android - if we do (by checking qrc usage), check
        # if the Android debug log folder exists - if it does, enable the log file at once
        # This is done Android being such a mess needs the possibility to easily enable early
        # logging to debug all the breakage. :)
        if qrc.is_qrc:
            # check for the debug log folder (note that this is on purpose folder is different
            # from the folder used to store debug logs enabled by the user)
            if os.path.isdir(ANDROID_SPECIAL_LOG_FOLDER):
                self._root_modrana_logger.debug("special Android log folder (%s) detected", ANDROID_SPECIAL_LOG_FOLDER)
                self._root_modrana_logger.debug("enabling early Android log file")
                self.log_folder_path = ANDROID_SPECIAL_LOG_FOLDER
                self.enable_log_file()
                self._log_file_override = True
                self._root_modrana_logger.debug("early Android log file enabled")

    @property
    def log_folder_path(self):
        return self._log_folder_path

    @log_folder_path.setter
    def log_folder_path(self, path):
        self._log_folder_path = path

    def _get_log_filename(self, compression=False):
        if compression:
            return "modrana_%s.log.gz" % utils.get_time_hash_string()
        else:
            return "modrana_%s.log" % utils.get_time_hash_string()

    def clear_early_log(self):
        """ModRana stores early log messages in a MemoryHandler to have a complete log file
        in case logging to file is enabled later in modRana startup.
        But if modRana discovers after consulting the persistent options database that
        logging to should not be enabled, we need to remove the MemoryHandler & clear it's contents.
        """
        if self._memory_handler:
            self._root_modrana_logger.removeHandler(self._memory_handler)
            self._memory_handler.flush()
            self._memory_handler = None

    def get_log_file_path(self):
        """For use from QML/PyOtherSide - it has some
           issues with accessing properties
           """
        return self._log_file_path

    @property
    def log_file_path(self):
        return self._log_file_path

    @log_file_path.setter
    def log_file_path(self, value):
        self._log_file_path = value

    def enable_log_file(self, compression=False):
        """Enable logging modRana log messages to file.

        If this is called during startup, early log messages preceding the log file
        activation are dumped to the log, so no messages from a modRana run should be
        missing from the log file.
        """

        # attempt to enable the log file
        with self._log_file_enabled_lock:
            # check if the log file is not already enabled
            if self._log_file_enabled:
                self._root_modrana_logger.error("log file already exist")
                return

            # first try to make sure the logging folder actually exists
            if not utils.create_folder_path(self.log_folder_path):
                self._root_modrana_logger.error("failed to create logging folder in: %s",
                                                self.log_folder_path)
                return

            self._log_file_compression = compression

            # create a file logger that logs everything
            log_file_path = os.path.join(self.log_folder_path, self._get_log_filename(compression=compression))
            if compression:
                if sys.version_info >= (3, 0):
                    self._compressed_log_file = gzip.open(log_file_path, mode="wt", encoding="utf-8")
                else:
                    self._compressed_log_file = gzip.open(log_file_path, mode="wb")
                self._file_handler = logging.StreamHandler(self._compressed_log_file)
            else:
                self._file_handler = logging.FileHandler(log_file_path)
            self._file_handler.setLevel(logging.DEBUG)
            full_formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
            self._file_handler.setFormatter(full_formatter)

            # dump any early log messages to the log file
            if self._memory_handler:
                self._memory_handler.setTarget(self._file_handler)
                self._memory_handler.flush()
                # write all the early log records
                self._file_handler.flush()
                # now attach the log file to the root logger
                self._root_modrana_logger.addHandler(self._file_handler)
                # flush the memory logger again in case any messages arrived before
                # the last flush and connecting the log file to the root logger
                # (this might duplicate some messages, but we should not loose any
                # as both the MemoryHandler and root logger are connected at the moment)
                # now flush & nuke the MemoryHandler
                self._root_modrana_logger.removeHandler(self._memory_handler)
                self._memory_handler.flush()
                self._memory_handler.close()
                self._memory_handler = None
            else :
                # just attach the log file to the root logger
                self._root_modrana_logger.addHandler(self._file_handler)
            self.log_file_path = log_file_path
            self._log_file_enabled = True
        self._root_modrana_logger.info("log file enabled: %s" % log_file_path)

    def disable_log_file(self):
        with self._log_file_enabled_lock:
            if self._log_file_override:
                # in some cases (Android debugging) we might not want to disable the log file
                # even if it is disabled in options
                self._root_modrana_logger.info("not disabling log file due to log file override")
                return
            if self._file_handler:
                self._root_modrana_logger.info("disabling the log file in: %s", self.log_folder_path)
                self._root_modrana_logger.info(self.log_file_path)
                self._root_modrana_logger.removeHandler(self._file_handler)
                if self._log_file_compression:
                    self._file_handler.flush()
                    self._file_handler.close()
                    if self._compressed_log_file:
                        self._compressed_log_file.close()
                        self._compressed_log_file = None
                else:
                    self._file_handler.close()
                self._file_handler = None
                self._log_file_path = None
                self._log_file_compression = False
                self._root_modrana_logger.info("log file disabled")

    @property
    def log_file_enabled(self):
        with self._log_file_enabled_lock:
            return self._log_file_enabled

    def disableStdoutLog(self):
        """Disable output to stdout from to console log handler

        This is mainly used in the CLI mode to not pollute stdout with modRana log messages.
        """
        self._console_handler.addFilter(self._filterAll)
        self._stdoutLoggingDisabled = True

    def enableStdoutLog(self):
        """Enable logging to stdout that has been previously disabled with disableStdoutLog()"""
        if self._stdoutLoggingDisabled:
            self._console_handler.removeFilter(self._filterAll)
            self._stdoutLoggingDisabled = False


def init_logging():
    global log_manager
    log_manager = LogManager()
