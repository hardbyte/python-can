Library API
===========

The main objects are the :class:`~can.Bus` and the :class:`~can.Message`.
A form of CAN interface is also required.


.. toctree::
   :maxdepth: 1
   
   bus
   message
   interfaces


Notifier
--------

The Notifier object is used as a message distributor for a bus.

.. autoclass:: can.Notifier
    :members:


Listener
--------

The Listener class is an "abstract" base class for any objects which wish to
register to receive notifications of new messages on the bus. A Listener can
be used in two ways; the default is to **call** the Listener with a new
message, or by calling the method **on_message_received**.

Listeners are registered with `Notifier`_ object(s) which ensure they are
notified whenever a new message is received.

Subclasses of Listener that do not override **on_message_received** will cause
`NotImplementedError` to be thrown when a message is received on
the CAN bus.


BufferedReader
--------------

The BufferedReader class is a subclass of `Listener`_ which implements a
"message buffer": that is, when a BufferedReader instance is notified of a
new message it pushes it into a queue of messages waiting to be serviced.

.. function:: get_message(timeout=0.5)

    The BufferedReader class provides a **get_message** method, which attempts to
    retrieve the latest message received by the instance. If no message is
    available it blocks for 0.5 seconds or until a message is received (whichever
    is shorter), and returns the message if there is one, or None if there is not.


MessagePrinter
--------------

The MessagePrinter class is a subclass of `Listener`_ which simply prints
any messages it receives to the terminal. The constructor takes an optional
argument **output_file** which will the file passed to print.


CSVWriter & SqliteWriter
------------------------

These Listeners simply create csv and sql files with the messages received.
