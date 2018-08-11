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
