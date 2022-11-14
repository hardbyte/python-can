"""
This module contains the implementation of `can.Listener` and some readers.
"""

import sys
import warnings
import asyncio
from abc import ABCMeta, abstractmethod
from queue import SimpleQueue, Empty
from typing import Any, AsyncIterator, Awaitable, Optional

from can.message import Message
from can.bus import BusABC


class Listener(metaclass=ABCMeta):
    """The basic listener that can be called directly to handle some
    CAN message::

        listener = SomeListener()
        msg = my_bus.recv()

        # now either call
        listener(msg)
        # or
        listener.on_message_received(msg)

        # Important to ensure all outputs are flushed
        listener.stop()
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def on_message_received(self, msg: Message) -> None:
        """This method is called to handle the given message.

        :param msg: the delivered message
        """

    def __call__(self, msg: Message) -> None:
        self.on_message_received(msg)

    def on_error(self, exc: Exception) -> None:
        """This method is called to handle any exception in the receive thread.

        :param exc: The exception causing the thread to stop
        """
        raise NotImplementedError()

    def stop(self) -> None:
        """
        Stop handling new messages, carry out any final tasks to ensure
        data is persisted and cleanup any open resources.

        Concrete implementations override.
        """


class RedirectReader(Listener):  # pylint: disable=abstract-method
    """
    A RedirectReader sends all received messages to another Bus.
    """

    def __init__(self, bus: BusABC, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.bus = bus

    def on_message_received(self, msg: Message) -> None:
        self.bus.send(msg)


class BufferedReader(Listener):  # pylint: disable=abstract-method
    """
    A BufferedReader is a subclass of :class:`~can.Listener` which implements a
    **message buffer**: that is, when the :class:`can.BufferedReader` instance is
    notified of a new message it pushes it into a queue of messages waiting to
    be serviced. The messages can then be fetched with
    :meth:`~can.BufferedReader.get_message`.

    Putting in messages after :meth:`~can.BufferedReader.stop` has been called will raise
    an exception, see :meth:`~can.BufferedReader.on_message_received`.

    :attr is_stopped: ``True`` if the reader has been stopped
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # set to "infinite" size
        self.buffer: SimpleQueue[Message] = SimpleQueue()
        self.is_stopped: bool = False

    def on_message_received(self, msg: Message) -> None:
        """Append a message to the buffer.

        :raises: BufferError
            if the reader has already been stopped
        """
        if self.is_stopped:
            raise RuntimeError("reader has already been stopped")
        else:
            self.buffer.put(msg)

    def get_message(self, timeout: float = 0.5) -> Optional[Message]:
        """
        Attempts to retrieve the message that has been in the queue for the longest amount
        of time (FIFO). If no message is available, it blocks for given timeout or until a
        message is received (whichever is shorter), or else returns None. This method does
        not block after :meth:`can.BufferedReader.stop` has been called.

        :param timeout: The number of seconds to wait for a new message.
        :return: the received :class:`can.Message` or `None`, if the queue is empty.
        """
        try:
            if self.is_stopped:
                return self.buffer.get(block=False)
            else:
                return self.buffer.get(block=True, timeout=timeout)
        except Empty:
            return None

    def stop(self) -> None:
        """Prohibits any more additions to this reader."""
        self.is_stopped = True


class AsyncBufferedReader(Listener):  # pylint: disable=abstract-method
    """A message buffer for use with :mod:`asyncio`.

    See :ref:`asyncio` for how to use with :class:`can.Notifier`.

    Can also be used as an asynchronous iterator::

        async for msg in reader:
            print(msg)
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.buffer: "asyncio.Queue[Message]"

        if "loop" in kwargs:
            warnings.warn(
                "The 'loop' argument is deprecated since python-can 4.0.0 "
                "and has no effect starting with Python 3.10",
                DeprecationWarning,
            )
            if sys.version_info < (3, 10):
                self.buffer = asyncio.Queue(loop=kwargs["loop"])
                return

        self.buffer = asyncio.Queue()

    def on_message_received(self, msg: Message) -> None:
        """Append a message to the buffer.

        Must only be called inside an event loop!
        """
        self.buffer.put_nowait(msg)

    async def get_message(self) -> Message:
        """
        Retrieve the latest message when awaited for::

            msg = await reader.get_message()

        :return: The CAN message.
        """
        return await self.buffer.get()

    def __aiter__(self) -> AsyncIterator[Message]:
        return self

    def __anext__(self) -> Awaitable[Message]:
        return self.buffer.get()
