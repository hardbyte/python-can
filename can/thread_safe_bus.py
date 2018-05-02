#!/usr/bin/env python
# coding: utf-8

"""
"""

from __future__ import print_function, absolute_import

from threading import RLock

from can import BusABC


class NullContextManager(object):
    """
    A context manager that does nothing at all.
    """
    def __init__(self, resource=None):
        self.resource = resource
    def __enter__(self):
        return self.resource
    def __exit__(self, *args):
        pass


class ThreadSafeBus(BusABC):
    """
    Contains a thread safe :class:`~can.BusABC` implementation that
    wraps around an existing interface instance. All methods of that
    base class are now safe to be called from multiple threads.

    This approach assumes that both :meth:`~can.BusABC.send` and
    :meth:`~can.BusABC.recv` of the underlying bus instance can be
    called simultaneously.

    Use this as a drop in replacement for :class:`can.BusABC`.
    """

    @classmethod
    def __new__(cls, channel=None, *args, **kwargs):    
        self = super().__new__(channel=channel, *args, **kwargs)
        return self

    def __init__(self, channel=None, can_filters=None, *args, **config):
        super().__init__(channel=channel, can_filters=can_filters, *args, **config)
        # init a lock for sending and one for receiving
        self._lock_send = RLock()
        self._lock_recv = RLock()
        # now the send periodic does not need a lock anymore, but the
        # implementation still requires a context manager to be able
        # to be called
        self._lock_send_periodic = NullContextManager()

    def recv(self, timeout=None, *args, **kwargs):
        with self._lock_recv:
            return super().recv(timeout=timeout, *args, **kwargs)

    def send(self, msg, timeout=None, *args, **kwargs):
        with self._lock_send:
            return super().send(msg, timeout=timeout, *args, **kwargs)

    def set_filters(self, can_filters=None, *args, **kwargs):
        with self._lock_recv:
            return super().set_filters(can_filters=can_filters, *args, **kwargs)

    def flush_tx_buffer(self, *args, **kwargs):
        with self._lock_send:
            return super().flush_tx_buffer(*args, **kwargs)

    def shutdown(self, *args, **kwargs):
        with self._lock_send, self._lock_recv:
            return super().shutdown(*args, **kwargs)
