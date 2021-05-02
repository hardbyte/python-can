"""
This module contains the implementation of :class:`~can.Notifier`.
"""

from typing import Any, cast, Iterable, List, Optional, Union, Awaitable

from can.bus import BusABC
from can.listener import Listener
from can.message import Message

import threading
import logging
import time
import asyncio

logger = logging.getLogger("can.Notifier")


class Notifier:
    def __init__(
        self,
        bus: Union[BusABC, List[BusABC]],
        listeners: Iterable[Listener],
        timeout: float = 1.0,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Manages the distribution of :class:`can.Message` instances to listeners.

        Supports multiple buses and listeners.

        .. Note::

            Remember to call `stop()` after all messages are received as
            many listeners carry out flush operations to persist data.


        :param bus: A :ref:`bus` or a list of buses to listen to.
        :param listeners: An iterable of :class:`~can.Listener`
        :param timeout: An optional maximum number of seconds to wait for any message.
        :param loop: An :mod:`asyncio` event loop to schedule listeners in.
        """
        self.listeners: List[Listener] = list(listeners)
        self.bus = bus
        self.timeout = timeout
        self._loop = loop

        #: Exception raised in thread
        self.exception: Optional[Exception] = None

        self._running = True
        self._lock = threading.Lock()

        self._readers: List[Union[int, threading.Thread]] = []
        buses = self.bus if isinstance(self.bus, list) else [self.bus]
        for each_bus in buses:
            self.add_bus(each_bus)

    def add_bus(self, bus: BusABC) -> None:
        """Add a bus for notification.

        :param bus:
            CAN bus instance.
        """
        reader: int = -1
        try:
            reader = bus.fileno()
        except NotImplementedError:
            # Bus doesn't support fileno, we fall back to thread based reader
            pass

        if self._loop is not None and reader >= 0:
            # Use bus file descriptor to watch for messages
            self._loop.add_reader(reader, self._on_message_available, bus)
            self._readers.append(reader)
        else:
            reader_thread = threading.Thread(
                target=self._rx_thread,
                args=(bus,),
                name='can.notifier for bus "{}"'.format(bus.channel_info),
            )
            reader_thread.daemon = True
            reader_thread.start()
            self._readers.append(reader_thread)

    def stop(self, timeout: float = 5) -> None:
        """Stop notifying Listeners when new :class:`~can.Message` objects arrive
        and call :meth:`~can.Listener.stop` on each Listener.

        :param timeout:
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
            elif self._loop:
                # reader is a file descriptor
                self._loop.remove_reader(reader)
        for listener in self.listeners:
            if hasattr(listener, "stop"):
                listener.stop()

    def _rx_thread(self, bus: BusABC) -> None:
        msg = None
        try:
            while self._running:
                if msg is not None:
                    with self._lock:
                        if self._loop is not None:
                            self._loop.call_soon_threadsafe(
                                self._on_message_received, msg
                            )
                        else:
                            self._on_message_received(msg)
                msg = bus.recv(self.timeout)
        except Exception as exc:  # pylint: disable=broad-except
            self.exception = exc
            if self._loop is not None:
                self._loop.call_soon_threadsafe(self._on_error, exc)
                # Raise anyways
                raise
            elif not self._on_error(exc):
                # If it was not handled, raise the exception here
                raise
            else:
                logger.info("suppressed exception: %s", exc)

    def _on_message_available(self, bus: BusABC) -> None:
        msg = bus.recv(0)
        if msg is not None:
            self._on_message_received(msg)

    def _on_message_received(self, msg: Message) -> None:
        for callback in self.listeners:
            res = cast(Union[None, Optional[Awaitable[Any]]], callback(msg))
            if res is not None and self._loop is not None and asyncio.iscoroutine(res):
                # Schedule coroutine
                self._loop.create_task(res)

    def _on_error(self, exc: Exception) -> bool:
        """Calls ``on_error()`` for all listeners if they implement it.

        :returns: ``True`` if and only if at least one handler was called
        """
        listeners_with_on_error = [
            listener for listener in self.listeners if hasattr(listener, "on_error")
        ]

        for listener in listeners_with_on_error:
            listener.on_error(exc)

        return bool(listeners_with_on_error)

    def add_listener(self, listener: Listener) -> None:
        """Add new Listener to the notification list.
        If it is already present, it will be called two times
        each time a message arrives.

        :param listener: Listener to be added to the list to be notified
        """
        self.listeners.append(listener)

    def remove_listener(self, listener: Listener) -> None:
        """Remove a listener from the notification list. This method
        throws an exception if the given listener is not part of the
        stored listeners.

        :param listener: Listener to be removed from the list to be notified
        :raises ValueError: if `listener` was never added to this notifier
        """
        self.listeners.remove(listener)
