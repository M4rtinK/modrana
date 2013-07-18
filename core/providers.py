# -*- coding: utf-8 -*-
# Geographic information providers

from core import threads, constants

class DummyController(object):
  """A default dummy object that implements the
  task controller interface that modRanaThreads have"""
  def __init__(self):
    self.status = None
    self.progress = None

class POIProvider(object):
  def __init__(self):
    pass

  def search(self, term=None, around=None, controller=DummyController()):
    """Search for POI using a textual search query
    :param term: search term
    :type term: str
    :param around: optional location bias
    :type around: Point instance
    :param controller: task controller
    :returns: a list of points, None if search failed
    :rtype: list
    """
    pass

  def searchAsync(self, callback, term=None, around=None):
    """Perform asynchronous search
    :param callback: result handler
    :type term: a callable
    :param term: search term
    :type term: str
    :param around: optional location bias
    :type around: Point instance
    """
    thread = threads.ModRanaThread()
    thread.name = constants.THREAD_POI_SEARCH
    # lambda is used to pass all needed arguments to the search function
    # and passing the result to the callback,
    # but not actually executing it until the thread is started
    thread.run = lambda: callback(
      self.search(
        term=term,
        around=around,
        controller=thread
      )
    )
    # register the thread by the thread manager
    # (this also starts the thread)
    threads.threadMgr.add(thread)