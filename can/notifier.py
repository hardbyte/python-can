#!/usr/bin/env python
# coding: utf-8

"""
This module contains the implementation of :class:`~can.Notifier`.
"""

import threading
import logging

logger = logging.getLogger('can.Notifier')


class Notifier(object):

    def __init__(self, bus, listeners, timeout=None):
        """Manages the distribution of **Messages** from a given bus to a
        list of listeners.

        :param bus: The :ref:`bus` to listen too.
        :param listeners: An iterable of :class:`~can.Listener`s
        :param timeout: An optional maximum number of seconds to wait for any message.
        """
        self.listeners = listeners
        self.bus = bus
        self.timeout = timeout

        # exception raised in thread
        self.exception = None

        self._running = threading.Event()
        self._running.set()

        self._reader = threading.Thread(target=self._rx_thread,
                                        name='can.notifier for bus "{}"'.format(self.bus.channel_info))
        self._reader.daemon = True
        self._reader.start()

    def stop(self):
        """Stop notifying Listeners when new :class:`~can.Message` objects arrive
        and call :meth:`~can.Listener.stop` on each Listener.
        """
        self._running.clear()
        if self.timeout is not None:
            self._reader.join(self.timeout + 0.1)

    def _rx_thread(self):
        try:
            while self._running.is_set():
                msg = self.bus.recv(self.timeout)
                if msg is not None:
                    for callback in self.listeners:
                        callback(msg)
        except Exception as exc:
            self.exception = exc
            raise
        finally:
            for listener in self.listeners:
                listener.stop()

    def add_listener(self, listener):
        """Add new Listener to the notification list. 
        If it is already present, it will be called two times
        each time a message arrives.

        :param listener: a :class:`~can.Listener` object to be added to
                         the list to be notified
        """
        self.listeners.append(listener)

    def remove_listener(self, listener):
        """Remove a listener from the notification list. This method
        trows an exception if the given listener is not part of the
        stored listeners.

        :param listener: a :class:`~can.Listener` object to be removed from
                         the list to be notified
        :raises ValueError: if `listener` was never added to this notifier
        """
        self.listeners.remove(listener)
