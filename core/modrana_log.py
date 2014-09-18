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

import logging
import logging.handlers
import os

from core import utils

log_manager = None

class LogManager(object):
    def __init__(self):
        """Initialize logging for modRana
        Logging is quite important as a one never knows when a bug shows
        up and it is important to know what was modRana doing at that time.
        """

        self._log_folder_path = None
        self._file_handler = None

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

        # create console handler that prints everything to stdout
        # (as was done previously by just using print)
        self._console_handler = logging.StreamHandler()
        self._console_handler.setLevel(logging.DEBUG)

        # create formatters and add them to the handlers
        # omit some stuff when printing to console to make the logs fit to terminal windows
        console_formatter = logging.Formatter('%(levelname)s %(name)s: %(message)s')
        # file viewers should be able to handle longer lines
        self._full_formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s:%(message)s')
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

    @property
    def log_folder_path(self):
        return self._log_folder_path

    @log_folder_path.setter
    def log_folder_path(self, path):
        self._log_folder_path = path

    def _get_log_filename(self):
        return "modrana_%.log" % utils.getTimeHashString()

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

    def enable_log_file(self):
        """Enable logging modRana log messages to file.

        If this is called during startup, early log messages preceding the log file
        activation are dumped to the log, so no messages from a modRana run should be
        missing from the log file.
        """
        # first try to make sure the logging folder actually exists
        if not utils.createFolderPath(self.log_folder_path):
            self._root_modrana_logger.error("failed to create logging folder in: %s",
                                            self.log_folder_path)
            return

        if self._file_handler:
            self._root_modrana_logger.error("log file already exist")
            return

        # create a file logger that logs everything
        self._file_handler = logging.FileHandler(
            os.path.join(self.log_folder_path, self._get_log_filename())
        )
        self._file_handler.setLevel(logging.DEBUG)

        # dump any early log messages to the log file
        if self._memory_handler:
            self._memory_handler.setTarget(self._file_handler)
            self._memory_handler.flush()
            # now attach the log file to the root logger
            self._root_modrana_logger.addHandler(self._file_handler)
            # flush the memory logger again in case any messages arrived before
            # the last flush and connecting the log file to the root logger
            # (this might duplicate some messages, but we should not loose any
            # as both the MemoryHandler and root logger are connected at the moment)
            # now flush & nuke the MemoryHandler
            self._memory_handler.flush()
            self._memory_handler.close()
            self._root_modrana_logger.removeHandler(self._memory_handler)
            self._memory_handler = None
        else :
            # just attach the log file to the root logger
            self._root_modrana_logger.addHandler(self._file_handler)

    def disable_log_file(self):
        self._root_modrana_logger.info("disabling the log file in: %s", self.log_folder_path)
        self._file_handler.close()
        self._root_modrana_logger.removeHandler(self._file_handler)
        self._file_handler = None
        self._root_modrana_logger.info("log file disabled")

def init_logging():
    global log_manager
    log_manager = LogManager()