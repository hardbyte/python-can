#!/usr/bin/env python
# coding: utf-8

"""
This module contains the implementation of `can.Listener` and some readers.
"""

from abc import ABCMeta, abstractmethod

try:
    # Python 3.7
    from queue import SimpleQueue, Empty
except ImportError:
    try:
        # Python 3.0 - 3.6
        from queue import Queue as SimpleQueue, Empty
    except ImportError:
        # Python 2
        from Queue import Queue as SimpleQueue, Empty

try:
    import asyncio
except ImportError:
    asyncio = None


class Listener(object):
    """The basic listener that can be called directly to handle some
    CAN message::

        listener = SomeListener()
        msg = my_bus.recv()

        # now either call
        listener(msg)
        # or
        listener.on_message_received(msg)

    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def on_message_received(self, msg):
        """This method is called to handle the given message.

        :param can.Message msg: the delivered message

        """
        pass

    def __call__(self, msg):
        return self.on_message_received(msg)

    def on_error(self, exc):
        """This method is called to handle any exception in the receive thread.

        :param Exception exc: The exception causing the thread to stop
        """

    def stop(self):
        """
        Override to cleanup any open resources.
        """


class RedirectReader(Listener):
    """
    A RedirectReader sends all received messages to another Bus.

    """

    def __init__(self, bus):
        self.bus = bus

    def on_message_received(self, msg):
        self.bus.send(msg)


class BufferedReader(Listener):
    """
    A BufferedReader is a subclass of :class:`~can.Listener` which implements a
    **message buffer**: that is, when the :class:`can.BufferedReader` instance is
    notified of a new message it pushes it into a queue of messages waiting to
    be serviced. The messages can then be fetched with
    :meth:`~can.BufferedReader.get_message`.

    Putting in messages after :meth:`~can.BufferedReader.stop` has be called will raise
    an exception, see :meth:`~can.BufferedReader.on_message_received`.

    :attr bool is_stopped: ``True`` iff the reader has been stopped
    """

    def __init__(self):
        # set to "infinite" size
        self.buffer = SimpleQueue()
        self.is_stopped = False

    def on_message_received(self, msg):
        """Append a message to the buffer.

        :raises: BufferError
            if the reader has already been stopped
        """
        if self.is_stopped:
            raise RuntimeError("reader has already been stopped")
        else:
            self.buffer.put(msg)

    def get_message(self, timeout=0.5):
        """
        Attempts to retrieve the latest message received by the instance. If no message is
        available it blocks for given timeout or until a message is received, or else
        returns None (whichever is shorter). This method does not block after
        :meth:`can.BufferedReader.stop` has been called.

        :param float timeout: The number of seconds to wait for a new message.
        :rytpe: can.Message or None
        :return: the message if there is one, or None if there is not.
        """
        try:
            return self.buffer.get(block=not self.is_stopped, timeout=timeout)
        except Empty:
            return None

    def stop(self):
        """Prohibits any more additions to this reader.
        """
        self.is_stopped = True


if asyncio is not None:
    class AsyncBufferedReader(Listener):
        """A message buffer for use with :mod:`asyncio`.

        See :ref:`asyncio` for how to use with :class:`can.Notifier`.
        
        Can also be used as an asynchronous iterator::

            async for msg in reader:
                print(msg)
        """

        def __init__(self, loop=None):
            # set to "infinite" size
            self.buffer = asyncio.Queue(loop=loop)

        def on_message_received(self, msg):
            """Append a message to the buffer.
            
            Must only be called inside an event loop!
            """
            self.buffer.put_nowait(msg)

        def get_message(self):
            """
            Retrieve the latest message when awaited for::
            
                msg = await reader.get_message()

            :rtype: can.Message
            :return: The CAN message.
            """
            return self.buffer.get()

        def __aiter__(self):
            return self
        
        def __anext__(self):
            return self.buffer.get()
