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


Logger
------

The :class:`can.Logger` uses the following :class:`can.Listener` types to
create *.asc*, *.csv* and *.db* files with the messages received.

.. autoclass:: can.Logger
    :members:


Printer
-------

.. autoclass:: can.Printer
    :members:


CSVWriter
---------

.. autoclass:: can.CSVWriter
    :members:


SqliteWriter
------------

.. autoclass:: can.SqliteWriter
    :members:


ASCWriter
---------

Logs CAN data to an ASCII log file compatible with other CAN tools such as
Vector CANalyzer/CANoe and other.
Since no official specification exists for the format, it has been reverse-
engineered from existing log files. One description of the format can be found `here
<http://zone.ni.com/reference/en-XX/help/370859J-01/dlgcanconverter/dlgcanconverter/canconverter_ascii_logfiles/>`_.

.. autoclass:: can.ASCWriter
    :members:


BLF (Binary Logging Format)
---------------------------

Implements support for BLF (Binary Logging Format) which is a proprietary
CAN log format from Vector Informatik GmbH.

The data is stored in a compressed format which makes it very compact.

.. autoclass:: can.BLFWriter
    :members:

.. autoclass:: can.BLFReader
    :members:
