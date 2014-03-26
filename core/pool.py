# -*- coding: utf-8 -*-
# At the moment just a thread pool implementation
from __future__ import with_statement  # Python 2.5

import threading

from core import threads
from core import queues

DEFAULT_THREAD_POOL_NAME = "modRanaThreadPool"
_threadPoolIndex = 1

def _getThreadPoolName():
    global _threadPoolIndex
    name = "%s%d" % (DEFAULT_THREAD_POOL_NAME, _threadPoolIndex)
    _threadPoolIndex+=1
    return name

class ThreadPool(object):
    """A simple thread pool"""

    def __init__(self, maxThreads, name=None,
                 taskBufferSize=0):
        self._maxThreads = maxThreads
        if name is None:
            self._name = _getThreadPoolName()
        else:
            self._name = name

        self._queueSize = 0  # not bounded by default
        if taskBufferSize > 0:
            # if task buffer size is specified we set the queue
            # size to maxThread + task buffer size
            # meaning there can be at any time maxThreads*tasks in progress
            # and taskBufferSize*tasks waiting to be processed
            self._queueSize = maxThreads+taskBufferSize

        # we use priority queue so that we can easily shutdown
        # threads even if there are still unprocessed work requests
        # by putting a priority shutdown tuple to the queue
        self._workQueue = self._getQueue()
        # as object instances have unique ids, by
        # calling object() we get an unique id that
        # shouldn't get mixed up with any other work item

        self._terminator = object()
        self._shutdownLock = threading.RLock()
        self._shutdown = False
        self._start()

    def _getQueue(self):
        return queues.PriorityQueue(maxsize=self._queueSize)

    @property
    def name(self):
        return self._name

    @property
    def maxThreads(self):
        return self._maxThreads

    @property
    def qsize(self):
        return self._workQueue.qsize

    def _start(self):
        """Start the thread pool"""
        for index in range(1, self._maxThreads+1):
            threadName = "%sWorker%d" % (self.name, index)
            thread = threads.ModRanaThread(
                name=threadName,
                target=self._worker
            )
            threads.threadMgr.add(thread)

    def _worker(self):
        """Worker method running in a ModRanaThread"""
        while True:
            item = self._workQueue.get(block=True)[1]
            if item == self._terminator:
                # shutdown
                self._workQueue.task_done()
                return
            else:
                fn, args, kwargs = item
                fn(*args, **kwargs)
                self._workQueue.task_done()

    def submit(self, fn, *args, **kwargs):
        """Submit a function to be called with a thread
        from the thread pool
        """
        with self._shutdownLock:
            if self._shutdown:
                raise RuntimeError
            else:
                # normal work items have priority 1
                self._workQueue.put((1, (fn, args, kwargs)))

    def shutdown(self, now=False, join=False):
        """Shutdown the thread pool"""
        with self._shutdownLock:
            self._shutdown = True
        # after shutdown is set, all submit calls
        # will throw RuntimeError, so there should be
        # no danger shutdown requests will get mixed up with
        # work requests (not that it mattered BTW, as long as
        # nr shutdown requests >= nr of threads)

        priority = 1
        if now:
            priority = 0
        # tuples with index 1 will get delivered after
        # all work requests are processed, items
        # with index 0 will get delivered before any
        # work requests (so we can shutdown even if we have
        # some unprocessed items in the queue)
        for index in range(1, self._maxThreads+1):
            self._workQueue.put((priority, self._terminator))
        # if requested, wait for the pool to shutdown
        if join:
            self._workQueue.join()


class LifoThreadPool(ThreadPool):
    """A thread pool variant that uses a lifo task queue
    and supports "leaking" tasks from the bottom of the stack
    onc the work queue becomes full
    """

    def __init__(self, maxThreads, name=None, taskBufferSize=0, leak=False):
        # set the self._leak variable before calling parent class __init__
        # as that calls _getQueue, which needs self._leak to be set
        self._leak = leak
        ThreadPool.__init__(self, maxThreads, name, taskBufferSize)

    def _getQueue(self):
        # we use a special lifo queue (stack) that supports leaking
        # tasks once the task becomes full as the work queue
        return queues.LeakyLifoQueue(maxsize=self._queueSize, leak=self._leak)

    def shutdown(self, now=False, join=False):
        """Shutdown the lifo thread pool"""
        with self._shutdownLock:
            self._shutdown = True
        # after shutdown is set, all submit calls
        # will throw RuntimeError, so there should be
        # no danger shutdown requests will get mixed up with
        # work requests (not that it mattered BTW, as long as
        # nr shutdown requests >= nr of threads)

        # the stack queue actually only supports shutting
        # down at once so now == False doesn't have any effect
        for index in range(1, self._maxThreads+1):
            self._workQueue.put((1, self._terminator))
        # if requested, wait for the pool to shutdown
        if join:
            self._workQueue.join()












