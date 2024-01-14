Notifier and Listeners
======================

.. _notifier:

Notifier
--------

The Notifier object is used as a message distributor for a bus. The Notifier
uses an event loop or creates a thread to read messages from the bus and
distributes them to listeners.

.. autoclass:: can.Notifier
    :members:

.. _listeners_doc:

Listener
--------

The Listener class is an "abstract" base class for any objects which wish to
register to receive notifications of new messages on the bus. A Listener can
be used in two ways; the default is to **call** the Listener with a new
message, or by calling the method **on_message_received**.

Listeners are registered with :ref:`notifier` object(s) which ensure they are
notified whenever a new message is received.

.. literalinclude:: ../examples/print_notifier.py
    :language: python
    :linenos:
    :emphasize-lines: 8,9


Subclasses of Listener that do not override **on_message_received** will cause
:class:`NotImplementedError` to be thrown when a message is received on
the CAN bus.

.. autoclass:: can.Listener
    :members:

There are some listeners that already ship together with `python-can`
and are listed below.
Some of them allow messages to be written to files, and the corresponding file
readers are also documented here.

.. note ::

    Please note that writing and the reading a message might not always yield a
    completely unchanged message again, since some properties are not (yet)
    supported by some file formats.

.. note ::

    Additional file formats for both reading/writing log files can be added via
    a plugin reader/writer. An external package can register a new reader
    by using the ``can.io.message_reader`` entry point. Similarly, a writer can
    be added using the ``can.io.message_writer`` entry point.

    The format of the entry point is ``reader_name=module:classname`` where ``classname``
    is a :class:`can.io.generic.BaseIOHandler` concrete implementation.

    ::

     entry_points={
         'can.io.message_reader': [
            '.asc = my_package.io.asc:ASCReader'
        ]
     },


BufferedReader
--------------

.. autoclass:: can.BufferedReader
    :members:

.. autoclass:: can.AsyncBufferedReader
    :members:


RedirectReader
--------------

.. autoclass:: can.RedirectReader
    :members:
