# -*- coding: utf-8 -*-
# modRana - shared utility classes and methods
from __future__ import with_statement # for python 2.5
import threading
import os
import sys
import subprocess
import re
import shutil

from core import constants
from core import qrc
from core.backports.six import b
from core.backports import six

StringIO = six.moves.cStringIO

PYTHON3 = sys.version_info[0] > 2

if PYTHON3:
    from urllib.parse import urlparse as urllib_parse
else:
    from urlparse import urlparse as urllib_parse

if qrc.is_qrc:
    import pyotherside

import time

import logging
log = logging.getLogger("core.utils")

class Empty(Exception):
    """Exception raised by the Synchronized circular stack"""
    pass


class SynchronizedCircularStack(object):
    """
    this should be a synchronized circular stack implementation
    * LIFO
    * once the size limit is reached, items re discarded,
      starting by the oldest ones
    * thread safe using a mutex
    _max_items sets the maximum number of items, 0=infinite size
    """

    def __init__(self, max_items=0):
        self.list = []
        self._list_lock = threading.Lock()
        self._max_items = max_items

    def push(self, item):
        """add a new item to the stack, make sure the size stays in bounds"""
        with self._list_lock:
            self.list.append(item)
            # check list size
            if self._max_items:
                # discard oldest items to get back to the limit
                while len(self.list) > self._max_items:
                    del self.list[0]

    def push_batch(self, item_list):
        """batch push items in a smart way"""
        with self._list_lock:
            # reverse the input list to simulate stack pushes
            # then combine the old list and the new one
            # and finally slice it to fit to the size limit
            item_list.reverse()
            self.list.extend(item_list)
            self.list = self.list[-self._max_items:]

    def pop(self):
        """
        NOTE: when the queue is empty, the Empty exception is raised
        """
        with self._list_lock:
            if len(self.list) == 0:
                raise Empty
            else:
                return self.list.pop()

    def pop_valid(self):
        """
        if the stack is not empty and the item is valid, return
        (popped_item, True)
        if the stack is empty and no items are available, return
        (None, True)

        this basically enables easy consuming
        th queue without having to handle the
        Empty exception
        """
        with self._list_lock:
            if len(self.list) == 0:
                return None, False
            else:
                return self.list.pop(), True

    def is_in(self, item):
        """item existence testing"""
        with self._list_lock:
            return item in self.list

#  def isInNonSync(self, item):
#    """non-synchronized version of item existence testing"""
#    return item in self.list

class ListContainer(object):
    """a WIP efficient list container, that does not need to actually store the
    whole list in memory"""

    def __init__(self):
        pass

    def get_item(self, index):
        """return item with a given index"""
        pass

    def get_items_in_range(self, startIndex, stopIndex):
        """return all items in range"""
        pass

    def get_length(self):
        """-1 indicates unknown item count"""
        pass


class SimpleListContainer(ListContainer):
    def __init__(self, items=None):
        if not items: items = []
        ListContainer.__init__(self)
        self.items = items

    def get_item(self, index):
        return self.items[index]

    def get_items_in_range(self, startIndex, stopIndex):
        return self.items[startIndex:stopIndex]

    def get_length(self):
        return len(self.items)


class PointListContainer(ListContainer):
    def __init__(self, points=None):
        if not points: points = []
        ListContainer.__init__(self)
        self.points = points

    def get_item(self, index):
        return self.points[index]

    def get_items_in_range(self, startIndex, stopIndex):
        return self.points[startIndex:stopIndex]

    def get_length(self):
        return len(self.points)


def is_the_string_an_image(s):
    """Test if the string contains an image.

    By reading its magic number.

    :param str s: string to be checked
    :returns: True is string is likely an image, False otherwise
    :rtype: bool
    """

    if PYTHON3: # in Python 3 we directly get bytes
        h = s
    else: # in Python <3 we get a string
        # create a file-like object
        f = StringIO(s)
        # read the header from it
        h = f.read(32)
        # cleanup
        f.close()

    # NOTE: magic numbers taken from imghdr source code

    # as most tiles are PNGs, check for PNG first
    if h[:8] == b("\211PNG\r\n\032\n"):
        return True
    elif h[6:10] in (b('JFIF'), b('Exif')): # JPEG in JFIF or Exif format
        return True
    elif h[:6] in (b('GIF87a'), b('GIF89a')): # GIF ('87 and '89 variants)
        return True
    elif h[:2] in (b('MM'), b('II'), b('BM')): # tiff or BMP
        return True
    else: # probably not an image file
        return False

def create_folder_path(new_path):
    """Create a path for a directory and all needed parent folders.

    -> parent directories will be created
    -> if directory already exists, then do nothing
    -> if there is another filesystem object (like a file)
       with the same name, raise an exception

    :param str new_path: path to be created
    :return: True on success, False otherwise
    :rtype: bool
    """
    if not new_path:
        log.error("cannot create folder, wrong path:")
        log.error(new_path)
        return False
    if os.path.isdir(new_path):
        return True
    elif os.path.isfile(new_path):
        log.error("cannot create directory, file already exists: %s", new_path)
        return False
    else:
        log.info("creating path: %s", new_path)
        try:
            head, tail = os.path.split(new_path)
            if head and not os.path.isdir(head):
                os.makedirs(head)
            if tail:
                os.mkdir(new_path)
            return True
        except Exception:
            log.exception("path creation failed")
            return False

#from
# http://stackoverflow.com/questions/3167154/
# how-to-split-a-dos-path-into-its-components-in-python
def split_path(path):
    """Split a filesystem path to a list of components.

    :param str: filesystem path
    :returns: paths split to components
    :rtype: list
    """
    path_split_list = []
    while os.path.basename(path):
        path_split_list.append(os.path.basename(path))
        path = os.path.dirname(path)
    path_split_list.reverse()
    return path_split_list

# from:
# http://www.5dollarwhitebox.org/drupal/node/84
def bytes_to_pretty_unit_string(bytes):
    """Convert a value in bytes into a pretty human readbale string.

    :returns: a human readable representation of a number of bytes
    :rtype: str
    """
    bytes = float(bytes)
    if bytes >= 1099511627776:
        terabytes = bytes / 1099511627776
        size = '%.2fTB' % terabytes
    elif bytes >= 1073741824:
        gigabytes = bytes / 1073741824
        size = '%.2fGB' % gigabytes
    elif bytes >= 1048576:
        megabytes = bytes / 1048576
        size = '%.2fMB' % megabytes
    elif bytes >= 1024:
        kilobytes = bytes / 1024
        size = '%.2fKB' % kilobytes
    else:
        size = '%.2fb' % bytes
    return size

def free_space_in_path(path):
    """Return free space in the given path in bytes

    :param string path: path to check
    :returns: free space in path in bytes, None if free space
              could not be determined
    :rtype: int or None
    """
    try:
        f = os.statvfs(path)
        return f.f_bsize * f.f_bavail
    except Exception:
        log.exception("using statvfs() for free space detection failed")

    # yes, this can happen even on Unix-like operating systems such as
    # Android, if the Python build that is used is incorrectly compiled
    log.debug("calling the df utility as a fallback to broken statvfs()")
    try:
        df_process = subprocess.Popen(["df", path], stdout=subprocess.PIPE)
        df_output = df_process.communicate()[0].decode('utf-8')
        # replace continuous whitespace and tabs by single whitespace
        df_output = re.sub("\s\s+", " ", df_output)
        # split by whitespace and extract free space info
        mega_bytes_available_string = df_output.split("\n")[1].split(" ")[3]
        if mega_bytes_available_string.upper().endswith("M"):
            mega_bytes_available_string = int(mega_bytes_available_string[:-1])*1024*1024
        else:
            mega_bytes_available_string = int(mega_bytes_available_string)*1024
        return mega_bytes_available_string
    except Exception:
        log.exception("calling df also failed, yay! :P")
        return None

def create_connection_pool(url, max_threads=1):
    """Create the connection pool -> to facilitate socket reuse

    :param string url: root URL for the threadpool
    :param int max_threads: pool capacity
    :returns: connection pool instance
    """
    # only import urllib3 once needed
    if sys.version_info[:2] <= (2, 5):
        from core.backports import urllib3_python25 as urllib3
    else:
        import urllib3
    return urllib3.connection_from_url(url, timeout=constants.INTERNET_CONNECTIVITY_TIMEOUT,
                                       maxsize=max_threads, block=False)
def get_time_hash_string():
    """Get a "hash" like time based string useable for use in file names.

    :returns: a time based has string
    :rtype: str
    """
    return time.strftime("%Y%m%d#%H-%M-%S", time.gmtime())

def get_elapsed_time_string(start_timestamp):
    return "%1.2f ms" % (1000 * (time.clock() - start_timestamp))

# Note about the "internal" functions
#
# This are used to work with files that modRana ships and expects to be available
# once installed (themes, example tracklogs, default configuration files).
# These files are normally just present in the modRana installation directory,
# but in some case (running on Android) might be bundled using qrc. In such case they
# are not available like "real" files/folders and special functions need to be called
# to access them.
#
# These internal_* function serve as wrappers that make it possible to handle both "normal"
# and qrc bundled files and folders in the same way.
#
# If modRana is running from qrc, the path is expected to point
# inside the qrc bundle. If you need to work with both qrc and non-qrc paths at once
# (eq. listing stuff from qrc & from real filesystem on Android) you need to handle
# that yourself (check if path should go to qrc and not use an internal_* function). :)

def internal_listdir(path):
    """Internal listdir function that works on both normal files and files
    bundled in qrc.

    :param str path: path to the folder to list
    :returns: folder contents
    :rtype: list of strings
    """
    if qrc.is_qrc:
        return pyotherside.qrc_list_dir(path)
    else:
        return os.listdir(path)

def internal_isdir(path):
    """Internal isdir function that works on both normal files and files
    bundled in qrc.

    :param str path: path to the folder to check
    :returns: True if path is file, False if not
    :rtype: bool
    """
    if qrc.is_qrc:
        return pyotherside.qrc_is_dir(path)
    else:
        return os.path.isdir(path)

def internal_isfile(path):
    """Internal isfile function that works on both normal files and files
    bundled in qrc.

    :param str path: path to the file to check
    :returns: True if path is file, False if not
    :rtype: bool
    """
    if qrc.is_qrc:
        return pyotherside.qrc_is_file(path)
    else:
        return os.path.isfile(path)

def internal_get_file_contents(path):
    """Internal function for getting file content as bytearray,
    works both on normal files and files bundled in qrc.

    :param str path: path to the file to fetch
    :returns: file contents as bytearray
    :rtype: bytearray
    """

    if qrc.is_qrc:
        return pyotherside.qrc_get_file_contents(path)
    else:
        with open(path, 'rb') as f:
            return bytearray(f.read())

def requirement_found(name):
     """Look for various requirements (utilities or paths).

     :param str name: requirement to look for

     Return ``True`` if `name` can be found on the system.

     `name` can be either a command, in which case it needs to be found in $PATH
     and it needs to be executable, or it can be a full absolute path to a file
     or a directory, in which case it needs to exist.
     """
     if os.path.isabs(name):
         return os.path.exists(name)
     return shutil.which(name) is not None

def path2uri(path):
     """Convert local filepath to URI.

     :param str path: local file path
     """
     return "file://{}".format(urllib_parse.quote(path))
