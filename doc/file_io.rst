File IO
=======


Reading and Writing Files
-------------------------

.. autofunction:: can.LogReader
.. autofunction:: can.Logger
.. autodata:: can.io.logger.MESSAGE_WRITERS
.. autodata:: can.io.player.MESSAGE_READERS

Printer
-------

.. autoclass:: can.Printer
    :show-inheritance:
    :members:


CSVWriter
---------

.. autoclass:: can.CSVWriter
    :show-inheritance:
    :members:

.. autoclass:: can.CSVReader
    :show-inheritance:
    :members:


SqliteWriter
------------

.. autoclass:: can.SqliteWriter
    :show-inheritance:
    :members:

.. autoclass:: can.SqliteReader
    :show-inheritance:
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
    :show-inheritance:
    :members:

ASCReader reads CAN data from ASCII log files .asc,
as further references can-utils can be used: 
`asc2log <https://github.com/linux-can/can-utils/blob/master/asc2log.c>`_,
`log2asc <https://github.com/linux-can/can-utils/blob/master/log2asc.c>`_.

.. autoclass:: can.ASCReader
    :show-inheritance:
    :members:


Log (.log can-utils Logging format)
-----------------------------------

CanutilsLogWriter logs CAN data to an ASCII log file compatible with `can-utils <https://github.com/linux-can/can-utils>`
As specification following references can-utils can be used: 
`asc2log <https://github.com/linux-can/can-utils/blob/master/asc2log.c>`_,
`log2asc <https://github.com/linux-can/can-utils/blob/master/log2asc.c>`_.


.. autoclass:: can.CanutilsLogWriter
    :show-inheritance:
    :members:

**CanutilsLogReader** reads CAN data from ASCII log files .log

.. autoclass:: can.CanutilsLogReader
    :show-inheritance:
    :members:


BLF (Binary Logging Format)
---------------------------

Implements support for BLF (Binary Logging Format) which is a proprietary
CAN log format from Vector Informatik GmbH.

The data is stored in a compressed format which makes it very compact.

.. note:: Channels will be converted to integers.

.. autoclass:: can.BLFWriter
    :show-inheritance:
    :members:

The following class can be used to read messages from BLF file:

.. autoclass:: can.BLFReader
    :show-inheritance:
    :members:


MF4 (Measurement Data Format v4)
--------------------------------

Implements support for MF4 (Measurement Data Format v4) which is a proprietary
format from ASAM (Association for Standardization of Automation and Measuring Systems), widely used in 
many automotive software (Vector CANape, ETAS INCA, dSPACE ControlDesk, etc.).

The data is stored in a compressed format which makes it compact.

.. note:: MF4 support has to be installed as an extra with for example ``pip install python-can[mf4]``.

.. note:: Channels will be converted to integers.

.. note:: MF4Writer does not suppport the append mode.


.. autoclass:: can.MF4Writer
    :show-inheritance:
    :members:

The MDF format is very flexible regarding the internal structure and it is used to handle data from multiple sources, not just CAN bus logging.
MDF4Writer will always create a fixed internal file structure where there will be three channel groups (for standard, error and remote frames). 
Using this fixed file structure allows for a simple implementation of MDF4Writer and MF4Reader classes.
Therefor MF4Reader can only replay files created with MF4Writer. 

The following class can be used to read messages from MF4 file:

.. autoclass:: can.MF4Reader
    :show-inheritance:
    :members:


TRC
----

Implements basic support for the TRC file format.


.. note::
   Comments and contributions are welcome on what file versions might be relevant.

.. autoclass:: can.TRCWriter
    :show-inheritance:
    :members:

The following class can be used to read messages from TRC file:

.. autoclass:: can.TRCReader
    :show-inheritance:
    :members:


Rotating Loggers
----------------

.. autoclass:: can.io.BaseRotatingLogger
    :show-inheritance:
    :members:

.. autoclass:: can.SizedRotatingLogger
    :show-inheritance:
    :members:


Replaying Files
---------------

.. autoclass:: can.MessageSync
    :members:

