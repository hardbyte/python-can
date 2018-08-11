.. _asyncio:

Asyncio support
===============

The :mod:`asyncio` module built into Python 3.4 and later can be used to write
asynchronos code in a single thread. This library supports receiving messages
asynchronosly in an event loop using the :class:`can.Notifier` class.
There will still be one thread per CAN bus but the user application will execute
entirely in the event loop, allowing simpler concurrency without worrying about
threading issues.

You can also use the :class:`can.AsyncBufferedReader` listener if you prefer
to write coroutine based code instead of using callbacks.


Example
-------

Here is an example using both callback and coroutine based code:

.. literalinclude:: ../examples/asyncio_demo.py
    :language: python


Native SocketCAN usage
----------------------

If only SocketCAN is expected to be used, it can be used without the extra
reader thread in the Notifier class.
Use the event loop's :meth:`~asyncio.AbstractEventLoop.add_reader` method to get
notified when new messages are available:

.. literalinclude:: ../examples/asyncio_socketcan.py
    :language: python
