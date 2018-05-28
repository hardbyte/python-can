#!/usr/bin/env python
# coding: utf-8

"""
"""

from __future__ import print_function, absolute_import

from threading import RLock

from wrapt import ObjectProxy, synchronized

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


class ThreadSafeBus(ObjectProxy, BusABC):
    """
    Contains a thread safe :class:`can.BusABC` implementation that
    wraps around an existing interface instance. All public methods
    of that base class are now safe to be called from multiple threads.

    Use this as a drop in replacement for :class:`~can.BusABC`.

    .. note::

        This approach assumes that both :meth:`~can.BusABC.send` and
        :meth:`~can.BusABC._recv_internal` of the underlying bus instance can be
        called simultaneously, and that the methods uses :meth:`~can.BusABC._recv_internal`
        instead of :meth:`~can.BusABC.recv` directly.
    """

    # init locks for sending and receiving
    _lock_send = RLock()
    _lock_recv = RLock()

    def __init__(self, *args, **kwargs):
        # now, BusABC.send_periodic() does not need a lock anymore, but the
        # implementation still requires a context manager
        self.__wrapped__._lock_send_periodic = NullContextManager()

    def recv(self, timeout=None, *args, **kwargs):
        with self._lock_recv:
            return self.__wrapped__.recv(timeout=timeout, *args, **kwargs)

    def send(self, msg, timeout=None, *args, **kwargs):
        with self._lock_send:
            return self.__wrapped__.send(msg, timeout=timeout, *args, **kwargs)

    # send_periodic does not need a lock, see that method and the comment in this __init__

    @property
    def filters(self):
        with self._lock_recv:
            return self.__wrapped__.filters

    @filters.setter
    def filters(self, filters):
        with self._lock_recv:
            self.__wrapped__.filters = filters

    def set_filters(self, can_filters=None, *args, **kwargs):
        with self._lock_recv:
            return self.__wrapped__.set_filters(can_filters=can_filters, *args, **kwargs)

    def flush_tx_buffer(self, *args, **kwargs):
        with self._lock_send:
            return self.__wrapped__.flush_tx_buffer(*args, **kwargs)

    def shutdown(self, *args, **kwargs):
        with self._lock_send, self._lock_recv:
            return self.__wrapped__.shutdown(*args, **kwargs)

    @property
    def state(self):
        with self._lock_send, self._lock_recv:
            return self.__wrapped__.state

    @state.setter
    def state(self, new_state):
        with self._lock_send, self._lock_recv:
            self.__wrapped__.state = new_state
