Listeners
=========

Listener
--------

The Listener class is an "abstract" base class for any objects which wish to
register to receive notifications of new messages on the bus. A Listener can
be used in two ways; the default is to **call** the Listener with a new
message, or by calling the method **on_message_received**.

Listeners are registered with :ref:`notifier` object(s) which ensure they are
notified whenever a new message is received.

Subclasses of Listener that do not override **on_message_received** will cause
`NotImplementedError` to be thrown when a message is received on
the CAN bus.

.. autoclass:: can.Listener
    :members:


BufferedReader
--------------

.. autoclass:: can.BufferedReader
    :members:


Printer
-------

.. autoclass:: can.Printer
    :members:



CSVWriter & SqliteWriter
------------------------

These Listeners simply create csv and sql files with the messages received.

.. autoclass:: can.CSVWriter
    :members:

.. autoclass:: can.SqliteWriter
    :members:
