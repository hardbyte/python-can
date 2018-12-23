.. _asyncio:

Asyncio support
===============

The :mod:`asyncio` module built into Python 3.4 and later can be used to write
asynchronous code in a single thread. This library supports receiving messages
asynchronously in an event loop using the :class:`can.Notifier` class.

There will still be one thread per CAN bus but the user application will execute
entirely in the event loop, allowing simpler concurrency without worrying about
threading issues. Interfaces that have a valid file descriptor will however be
supported natively without a thread.

You can also use the :class:`can.AsyncBufferedReader` listener if you prefer
to write coroutine based code instead of using callbacks.


Example
-------

Here is an example using both callback and coroutine based code:

.. literalinclude:: ../examples/asyncio_demo.py
    :language: python
