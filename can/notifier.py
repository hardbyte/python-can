#!/usr/bin/env python
# coding: utf-8

"""
This module contains the implementation of :class:`~can.Notifier`.
"""

import threading
import logging
import time
try:
    import asyncio
except ImportError:
    asyncio = None

logger = logging.getLogger('can.Notifier')


class Notifier(object):

    def __init__(self, bus, listeners, timeout=1.0, loop=None):
        """Manages the distribution of **Messages** from a given bus/buses to a
        list of listeners.

        :param can.BusABC bus: A :ref:`bus` or a list of buses to listen to.
        :param list listeners: An iterable of :class:`~can.Listener`
        :param float timeout: An optional maximum number of seconds to wait for any message.
        :param asyncio.AbstractEventLoop loop:
            An :mod:`asyncio` event loop to schedule listeners in.
        """
        self.listeners = listeners
        self.bus = bus
        self.timeout = timeout
        self._loop = loop

        #: Exception raised in thread
        self.exception = None

        self._running = True
        self._lock = threading.Lock()

        self._readers = []
        buses = self.bus if isinstance(self.bus, list) else [self.bus]
        for bus in buses:
            if loop is not None and hasattr(bus, 'fileno'):
                # Use file descriptor to watch for messages
                reader = bus.fileno()
                loop.add_reader(reader, self.on_message_available, bus)
            else:
                reader = threading.Thread(target=self._rx_thread, args=(bus,),
                    name='can.notifier for bus "{}"'.format(bus.channel_info))
                reader.daemon = True
                reader.start()
            self._readers.append(reader)

    def stop(self, timeout=5):
        """Stop notifying Listeners when new :class:`~can.Message` objects arrive
        and call :meth:`~can.Listener.stop` on each Listener.

        :param float timeout:
            Max time in seconds to wait for receive threads to finish.
            Should be longer than timeout given at instantiation.
        """
        self._running = False
        end_time = time.time() + timeout
        for reader in self._readers:
            if isinstance(reader, threading.Thread):
                now = time.time()
                if now < end_time:
                    reader.join(end_time - now)
            else:
                # reader is a file descriptor
                self._loop.remove_reader(reader)
        for listener in self.listeners:
            if hasattr(listener, 'stop'):
                listener.stop()

    def _rx_thread(self, bus):
        msg = None
        try:
            while self._running:
                if msg is not None:
                    with self._lock:
                        self.on_message_received(msg)
                msg = bus.recv(self.timeout)
        except Exception as exc:
            self.exception = exc
            raise

    def on_message_received(self, msg):
        for callback in self.listeners:
            if self._loop is not None:
                if asyncio.iscoroutinefunction(callback):
                    coro = callback(msg)
                    asyncio.run_coroutine_threadsafe(coro, self._loop)
                else:
                    self._loop.call_soon_threadsafe(callback, msg)
            else:
                callback(msg)

    def on_message_available(self, bus):
        msg = bus.recv(0)
        if msg is not None:
            for callback in self.listeners:
                if asyncio.iscoroutinefunction(callback):
                    self._loop.create_task(callback(msg))
                else:
                    self._loop.call_soon(callback, msg)

    def add_listener(self, listener):
        """Add new Listener to the notification list. 
        If it is already present, it will be called two times
        each time a message arrives.

        :param can.Listener listener: Listener to be added to
                         the list to be notified
        """
        self.listeners.append(listener)

    def remove_listener(self, listener):
        """Remove a listener from the notification list. This method
        trows an exception if the given listener is not part of the
        stored listeners.

        :param can.Listener listener: Listener to be removed from
                         the list to be notified
        :raises ValueError: if `listener` was never added to this notifier
        """
        self.listeners.remove(listener)
