# modRana - shared utility classes and methods
from __future__ import with_statement # for python 2.5
import threading
import magic
from cStringIO import StringIO

class Empty(Exception):
    "Exception raised by the Synchronized circular stack"
    pass

class SynchronizedCircularStack:
  """
  this should be a synchronized circular stact implementation
  * LIFO
  * once the size limit is reached, items re discarded,
    starting by the oldest ones
  * thread safe using a mutex
  maxItems sets the maximum number of items, 0=infinite size


  """
  def __init__(self,maxItems=0):
    self.list = []
    self.listLock = threading.Lock()
    self.maxItems = maxItems

  def push(self, item):
    """add a new item to the stack, make sure the size stays in bounds"""
    with self.listLock:
      self.list.append(item)
      # check list size
      if self.maxItems:
          # discard olderst items to get back to the limit
          while len(self.list) > self.maxItems:
            del self.list[0]

  def batchPush(self, itemList):
    """batch push items in a smart way"""
    with self.listLock:
      """
      reverse the imput list to simulate stack pushes
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
        return (None,False)
      else:
        return (self.list.pop(),True)

  def isIn(self, item):
    """item existence testing"""
    with self.listLock:
      return item in self.list

#  def isInNonSync(self, item):
#    """nonsynchronized version of item existence testing"""
#    return item in self.list

def isTheStringAnImage(s):
  """test if the string contains an image
  by reading its magic number"""

  # create a file like object
  f = StringIO(s)
  mime = magic.from_buffer(f.read(1024), mime=True)
  # get ists mime
  mimeSplit = mime.split('/')
  mime1 = mimeSplit[0]
  # check if its an image
  if mime1 == 'image':
    return True
  else:
    return False
