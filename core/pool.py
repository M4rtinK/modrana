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
        if taskBufferSize >= 0:
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

        # we need to keep track of our workers so we can join
        # them in some pool shutdown scenarios
        self._workers = []

        self._terminator = object()
        self._shutdownLock = threading.RLock()
        self._shutdown = False
        self._start()

    def _getQueue(self):
        return queues.PriorityQueue(maxsize=self._queueSize)

    def _handleLeakedItem(self, leakedItem):
        pass

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
            # save the thread ID
            self._workers.append(threads.threadMgr.add(thread))

    def _worker(self):
        """Worker method running in a ModRanaThread"""
        while True:
            item = self._workQueue.get(block=True)[1]
            if item == self._terminator:
                # shutdown
                self._workQueue.task_done()
                break
            else:
                fn, args, kwargs = item
                fn(*args, **kwargs)
                self._workQueue.task_done()

    def submit(self, fn, *args, **kwargs):
        """Submit a function to be called with a thread
        from the thread pool
        """
        leakedItem = None
        with self._shutdownLock:
            if self._shutdown:
                raise RuntimeError
            else:
                # normal work items have priority 1
                leakedItem = self._workQueue.put((1, (fn, args, kwargs)))
                # if the work queue used supports leaking items, we need
                # to strip the leading priority number before returning
                # the leaked item
        return self._handleLeakedItem(leakedItem)


    def shutdown(self, now=False, join=False, asynchronous=True, callback=None):
        """Shutdown the lifo thread pool"""
        with self._shutdownLock:
            if self._shutdown:
                # shutdown already in progress or not running
                return False
            else:
                self._shutdown = True
        # after shutdown is set, all submit calls
        # will throw RuntimeError, so there should be
        # no danger shutdown requests will get mixed up with
        # work requests (not that it mattered BTW, as long as
        # nr shutdown requests >= nr of threads)

        # if the queue is bounded, the shutdown function may block
        # so run it in a thread by default, with the possibility of
        # triggering a callback once it is done
        if asynchronous:
            call = lambda : self._shutdownWrapper(now, join, callback)
            t = threads.ModRanaThread(name=self.name+"Shutdown",
                                      target=call)
            threads.threadMgr.add(t)
        else:
            self._shutdownWrapper(now, join, callback)

        return True


    def _shutdownWrapper(self, now, join, callback):
        self._shutdownHandler(now, join)
        # is there a callback for when we are done ?
        if callback:
            # call it !
            callback()

    def _shutdownHandler(self, now, join):
        priority = 2
        if now:
            priority = 0
        # tuples with index 2 will get delivered after
        # all work requests with index 1 are processed,
        # items with index 0 will get delivered before any
        # work requests (so we can shutdown even if we have
        # some unprocessed items in the queue)
        for index in range(1, self._maxThreads+1):
            self._workQueue.put((priority, self._terminator))
        # if requested, wait for the pool to shutdown
        # import pdb;pdb.set_trace()
        if join:
            # we can't just coin the queue as there might still
            # be work items in it during an explicit shutdown
            for threadId in self._workers:
                threads.threadMgr.wait(threadId)
        # clean the worker list, just in case
        self._workers = []


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

    def _handleLeakedItem(self, leakedItem):
        if leakedItem and leakedItem is not queues.NOTHING:
            # drop the priority prefix
            return leakedItem[1]

    def _shutdownHandler(self, now, join):
        # the stack queue actually only supports shutting
        # down at once so now == False doesn't have any effect
        for index in range(1, self._maxThreads+1):
            self._workQueue.put((1, self._terminator))
        # if requested, wait for the pool to shutdown
        if join:
            self._workQueue.join()