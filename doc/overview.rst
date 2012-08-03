Overview
=============

Code Structure
--------------

The modules in pycanlib-socketcan are:

+--------------------+------------------------------------------------------+
|Module              | Description                                          |
+====================+======================================================+
|:doc:`CAN.py <\can>`| Contains modules to emulate a CAN system, such as a  |
|                    | CAN bus, messages, time stamps, read/write streams   |
|                    | and listeners.                                       |
+--------------------+------------------------------------------------------+
|:doc:`socketcanlib. | Wraps libc, which contains linux SocketCAN. This is  |
|py <\socketcanlib>` | used to create CAN sockets and read from them.       |
+--------------------+------------------------------------------------------+

Differences from pycanlib
-------------------------

=====================       ===================================================
Module                      Modifications
=====================       ===================================================
CAN.py                      Major changes to Message and Bus. Removal of all
                            references to InputValidation. 
socketcanlib.py             Replaces canlib.
canlib.py                   Removed.
InputValidation.py          Removed.
can_logger.py               A lot of input options are no longer supported.
=====================       ===================================================
