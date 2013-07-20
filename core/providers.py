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
    # lambda is used to pass all needed arguments to the search function
    # and passing the result to the callback,
    # but not actually executing it until the thread is started
    thread = threads.ModRanaThread(name=constants.THREAD_POI_SEARCH)
    thread.target = lambda: self.search(
      term=term,
      around=around,
      controller=thread
    )
    thread.callback = callback

    # and yet, this really works :)
    # - we need to set the target, and it seems this can only be done in init
    # - passing the thread itself as controller seems to work or at least does
    # not raise any outright exception

    # register the thread by the thread manager
    # (this also starts the thread)
    threads.threadMgr.add(thread)