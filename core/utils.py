# -*- coding: utf-8 -*-
# modRana - shared utility classes and methods
from __future__ import with_statement # for python 2.5
import threading
import os
import sys

from core import constants
from core.backports.six import b
from core.backports import six

StringIO = six.moves.cStringIO

PYTHON3 = sys.version_info[0] > 2


#import time

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
    maxItems sets the maximum number of items, 0=infinite size
    """

    def __init__(self, maxItems=0):
        self.list = []
        self.listLock = threading.Lock()
        self.maxItems = maxItems

    def push(self, item):
        """add a new item to the stack, make sure the size stays in bounds"""
        with self.listLock:
            self.list.append(item)
            # check list size
            if self.maxItems:
                # discard oldest items to get back to the limit
                while len(self.list) > self.maxItems:
                    del self.list[0]

    def batchPush(self, itemList):
        """batch push items in a smart way"""
        with self.listLock:
            # reverse the input list to simulate stack pushes
            # then combine the old list and the new one
            # and finally slice it to fit to the size limit
            itemList.reverse()
            self.list.extend(itemList)
            self.list = self.list[-self.maxItems:]

    def pop(self):
        """
        NOTE: when the queue is empty, the Empty exception is raised
        """
        with self.listLock:
            if len(self.list) == 0:
                raise Empty
            else:
                return self.list.pop()

    def popValid(self):
        """
        if the stack is not empty and the item is valid, return
        (popped_item, True)
        if the stack is empty and no items are available, return
        (None, True)

        this basically enables easy consuming
        th queue without having to handle the
        Empty exception
        """
        with self.listLock:
            if len(self.list) == 0:
                return None, False
            else:
                return self.list.pop(), True

    def isIn(self, item):
        """item existence testing"""
        with self.listLock:
            return item in self.list

#  def isInNonSync(self, item):
#    """non-synchronized version of item existence testing"""
#    return item in self.list

class ListContainer(object):
    """a WIP efficient list container, that does not need to actually store the
    whole list in memory"""

    def __init__(self):
        pass

    def getItem(self, index):
        """return item with a given index"""
        pass

    def getItemsInRange(self, startIndex, stopIndex):
        """return all items in range"""
        pass

    def getLength(self):
        """-1 indicates unknown item count"""
        pass


class SimpleListContainer(ListContainer):
    def __init__(self, items=None):
        if not items: items = []
        ListContainer.__init__(self)
        self.items = items

    def getItem(self, index):
        return self.items[index]

    def getItemsInRange(self, startIndex, stopIndex):
        return self.items[startIndex:stopIndex]

    def getLength(self):
        return len(self.items)


class PointListContainer(ListContainer):
    def __init__(self, points=None):
        if not points: points = []
        ListContainer.__init__(self)
        self.points = points

    def getItem(self, index):
        return self.points[index]

    def getItemsInRange(self, startIndex, stopIndex):
        return self.points[startIndex:stopIndex]

    def getLength(self):
        return len(self.points)


def isTheStringAnImage(s):
    """test if the string contains an image
    by reading its magic number"""

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


def createFolderPath(newPath):
    """Create a path for a directory and all needed parent folders
    -> parent directories will be created
    -> if directory already exists, then do nothing
    -> if there is another filesystem object (like a file)
    with the same name, raise an exception"""
    if not newPath:
        print("cannot create folder, wrong path: ", newPath)
        return False
    if os.path.isdir(newPath):
        return True
    elif os.path.isfile(newPath):
        print("cannot create directory, file already exists: '%s'" % newPath)
        return False
    else:
        print("creating path: %s" % newPath)
        try:
            head, tail = os.path.split(newPath)
            if head and not os.path.isdir(head):
                os.makedirs(head)
            if tail:
                os.mkdir(newPath)
            return True
        except Exception:
            print("path creation failed")
            import sys
            e = sys.exc_info()[1]
            print(e)
            return False

#from
# http://stackoverflow.com/questions/3167154/
# how-to-split-a-dos-path-into-its-components-in-python
def SplitPath(split_path):
    pathSplit_lst = []
    while os.path.basename(split_path):
        pathSplit_lst.append(os.path.basename(split_path))
        split_path = os.path.dirname(split_path)
    pathSplit_lst.reverse()
    return pathSplit_lst

# from:
# http://www.5dollarwhitebox.org/drupal/node/84
def bytes2PrettyUnitString(bytes):
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

def freeSpaceInPath(path):
    """Return free space in the given path in bytes

    :param string path: path to check
    :returns: free space in path in bytes
    :rtype: int
    """
    f = os.statvfs(path)
    return f.f_bsize * f.f_bavail

def createConnectionPool(url, maxThreads=1):
    """Create the connection pool -> to facilitate socket reuse

    :param string url: root URL for the threadpool
    :param int maxThreads: pool capacity
    """
    # only import urllib3 once needed
    if sys.version_info[:2] <= (2, 5):
        from core.backports import urllib3_python25 as urllib3
    else:
        from core.bundle import urllib3
    return urllib3.connection_from_url(url, timeout=constants.INTERNET_CONNECTIVITY_TIMEOUT,
                                       maxsize=maxThreads, block=False)