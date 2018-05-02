#!/usr/bin/env python
# coding: utf-8

"""
"""

from __future__ import print_function, absolute_import

from threading import RLock

from can import Bus, BusABC


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


class ThreadSafeBus():
    """
    Contains a thread safe :class:`~can.BusABC` implementation that
    wraps around an existing interface instance. All methods of that
    base class are now safe to be called from multiple threads.

    This approach assumes that both :meth:`~can.BusABC.send` and
    :meth:`~can.BusABC.recv` of the underlying bus instance can be
    called simultaneously.

    Use this as a drop in replacement for :class:`can.BusABC`.
    """

    def __init__(self, *args, **kwargs):
        # create the underlying bus
        setattr(self, '_bus', Bus(*args, **kwargs))

        # init a lock for sending and one for receiving
        setattr(self, '_lock_send', RLock())
        setattr(self, '_lock_recv', RLock())

        # now the send periodic does not need a lock anymore, but the
        # implementation still requires a context manager to be able
        # to be called
        self._bus._lock_send_periodic = NullContextManager()

    def __getattribute__(self, name):
        return getattr(self._bus, name)

    def __setattr__(self, name, value):
        setattr(self._bus, name, value)

    def recv(self, timeout=None, *args, **kwargs):
        with self._lock_recv:
            return self._bus.recv(timeout=timeout, *args, **kwargs)

    def send(self, msg, timeout=None, *args, **kwargs):
        with self._lock_send:
            return self._bus.send(msg, timeout=timeout, *args, **kwargs)

    def set_filters(self, can_filters=None, *args, **kwargs):
        with self._lock_recv:
            return self._bus.set_filters(can_filters=can_filters, *args, **kwargs)

    def flush_tx_buffer(self, *args, **kwargs):
        with self._lock_send:
            return self._bus.flush_tx_buffer(*args, **kwargs)

    def shutdown(self, *args, **kwargs):
        with self._lock_send, self._lock_recv:
            return self._bus.shutdown(*args, **kwargs)
