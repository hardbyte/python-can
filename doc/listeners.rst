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


BufferedReader
--------------

.. autoclass:: can.BufferedReader
    :members:

.. autoclass:: can.AsyncBufferedReader
    :members:


Logger
------

The :class:`can.Logger` uses the following :class:`can.Listener` types to
create log files with different file types of the messages received.

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

.. autoclass:: can.CSVReader
    :members:


SqliteWriter
------------

.. autoclass:: can.SqliteWriter
    :members:

.. autoclass:: can.SqliteReader
    :members:


Database table format
~~~~~~~~~~~~~~~~~~~~~

The messages are written to the table ``messages`` in the sqlite database
by default. The table is created if it does not already exist.

The entries are as follows:

==============  ==============  ==============
Name            Data type       Note
--------------  --------------  --------------
ts              REAL            The timestamp of the message
arbitration_id  INTEGER         The arbitration id, might use the extended format
extended        INTEGER         ``1`` if the arbitration id uses the extended format, else ``0``
remote          INTEGER         ``1`` if the message is a remote frame, else ``0``
error           INTEGER         ``1`` if the message is an error frame, else ``0``
dlc             INTEGER         The data length code (DLC)
data            BLOB            The content of the message
==============  ==============  ==============


ASC (.asc Logging format)
-------------------------
ASCWriter logs CAN data to an ASCII log file compatible with other CAN tools such as
Vector CANalyzer/CANoe and other.
Since no official specification exists for the format, it has been reverse-
engineered from existing log files. One description of the format can be found `here
<http://zone.ni.com/reference/en-XX/help/370859J-01/dlgcanconverter/dlgcanconverter/canconverter_ascii_logfiles/>`_.


.. note::

    Channels will be converted to integers.


.. autoclass:: can.ASCWriter
    :members:

ASCReader reads CAN data from ASCII log files .asc,
as further references can-utils can be used: 
`asc2log <https://github.com/linux-can/can-utils/blob/master/asc2log.c>`_,
`log2asc <https://github.com/linux-can/can-utils/blob/master/log2asc.c>`_.

.. autoclass:: can.ASCReader
    :members:


Log (.log can-utils Logging format)
-----------------------------------

CanutilsLogWriter logs CAN data to an ASCII log file compatible with `can-utils <https://github.com/linux-can/can-utils>`
As specification following references can-utils can be used: 
`asc2log <https://github.com/linux-can/can-utils/blob/master/asc2log.c>`_,
`log2asc <https://github.com/linux-can/can-utils/blob/master/log2asc.c>`_.


.. autoclass:: can.CanutilsLogWriter
    :members:

**CanutilsLogReader** reads CAN data from ASCII log files .log

.. autoclass:: can.CanutilsLogReader
    :members:


BLF (Binary Logging Format)
---------------------------

Implements support for BLF (Binary Logging Format) which is a proprietary
CAN log format from Vector Informatik GmbH.

The data is stored in a compressed format which makes it very compact.

.. note:: Channels will be converted to integers.

.. autoclass:: can.BLFWriter
    :members:

The following class can be used to read messages from BLF file:

.. autoclass:: can.BLFReader
    :members:
