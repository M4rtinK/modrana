#!/usr/bin/python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# modRana qrc handling
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
#
# On Android with PyOtherSide modRana might be distributed using the qrc
# mechanism and might need a few tweaks applied to work properly.
#
from __future__ import with_statement  # for Python 2.5

import logging
import shutil
log = logging.getLogger("core.qrc")
import os

IS_QRC = __file__.startswith("qrc:")

VERSION_FILE_NAME = "version.txt"

if IS_QRC:
    import pyotherside

# looks like @property does not work outside of class ?
is_qrc = IS_QRC

def export_from_qrc(root, target):
    """Recursively export a given qrc subtree as given by root
       to the target folder.
    """
    #log.debug("exporting %s from qrc", root)
    try:
        file_counter = 0
        folder_counter = 0
        for entry in pyotherside.qrc_list_dir(root):
            name = os.path.join(root, entry)
            if pyotherside.qrc_is_dir(name):
                #log.debug('Creating directory: %s', name)
                os.makedirs(os.path.join(target, name))
                folder_counter += 1
                export_from_qrc(name, os.path.join(target, name))
            else:
                data = pyotherside.qrc_get_file_contents(name)
                #log.debug('Creating file: %s (%d bytes)', name, len(data))
                with open(name, "wb") as f:
                    f.write(data)
                file_counter += 1
        #log.debug("%d files and %d folders exported from %s", file_counter, folder_counter, root)
    except Exception:
       log.exception("qrc export from %s to %s failed", root, target)

def _get_qrc_version():
    from core import paths
    if pyotherside.qrc_is_file(paths.VERSION_INFO_FILENAME):
        try:
            return pyotherside.qrc_get_file_contents(paths.VERSION_INFO_FILENAME).decode("utf-8").rstrip()
        except Exception:
            log.exception("reading modRana version from qrc file failed")
            return None
    else:
        log.warning("modRana version qrc file not found (development version ?)")
        return None



def handle_qrc():
    """Export files needed by modRana from qrc to "normal" storage"""
    from core import paths
    if is_qrc:
        log.info("modRana is using qrc")
        # modRana needs some data as files on filesystem, it might be
        # good to eventually load larger stuff directly from qrc, but
        # but for now unpacking them is enough and some files such as
        # configs should always remain as separate files due to easier
        # change management
        qrc_version = _get_qrc_version()
        local_version = paths.get_version_string()
        log.debug("versions:")
        log.debug("qrc: %s", qrc_version)
        log.debug("local: %s", local_version)

        # only replace the exported files if both version are not None
        # but different
        if qrc_version != local_version or qrc_version is local_version is None:
            try:
                # cleanup
                if os.path.exists("data"):
                    log.info("removing old local folder data")
                    shutil.rmtree("data")
                if os.path.isfile(paths.VERSION_INFO_FILENAME):
                    log.info("removing old local version file")
                    os.remove(paths.VERSION_INFO_FILENAME)

                # extract
                log.info("extracting files & folders needed by modRana from qrc")

                os.makedirs("data")
                log.info("extracting the data folder and its content")
                export_from_qrc('data', ".")

                # only write the version file once done ;-)
                if qrc_version:
                    log.info("writing version string %s to local file" % qrc_version)
                    with open(paths.VERSION_INFO_FILENAME, "wt") as f:
                        f.write(qrc_version)
                log.info("all needed data successfully extracted from qrc")
            except Exception:
                log.exception("qrc export failed")
        else:
            log.info("local files already exported and up to date")
