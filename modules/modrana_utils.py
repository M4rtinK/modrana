# -*- coding: utf-8 -*-
# modRana - shared utility classes and methods
from __future__ import with_statement # for python 2.5
import threading
import os
from cStringIO import StringIO
#import time

class Empty(Exception):
  """Exception raised by the Synchronized circular stack"""
  pass


class SynchronizedCircularStack:
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
      """
      reverse the input list to simulate stack pushes
      then combine the old list and the new one
      and finally slice it to fit to the size limit
      """
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

class ListContainer:
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

  # create a file-like object
  f = StringIO(s)
  # read the header from it
  h = f.read(32)
  # cleanup
  f.close()

  # NOTE: magic numbers taken from imghdr source code

  # as most tiles are PNGs, check for PNG first
  if h[:8] == "\211PNG\r\n\032\n":
    return True
  elif h[6:10] in ('JFIF', 'Exif'): # JPEG in JFIF or Exif format
    return True
  elif h[:6] in ('GIF87a', 'GIF89a'): # GIF ('87 and '89 variants)
    return True
  elif h[:2] in ('MM', 'II', 'BM'): # tiff or BMP
    return True
  else: # probably not an image file
    return False

def createFolderPath(newPath):
  """Create a path for a directory and all needed parent folders
  -> parent directories will be created
  -> if directory already exists, then do nothing
  -> if there is another filesystem object (like a file)
  with the same name exists, return False"""
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
    head, tail = os.path.split(newPath)
    if head and not os.path.isdir(head):
      createFolderPath(head) # NOTE: recursion
    if tail:
      os.mkdir(newPath)
    return True

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