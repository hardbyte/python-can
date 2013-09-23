Developer's Overview
===================

Explore the source code on bitbucket:
https://bitbucket.org/hardbyte/python-can


Code Structure
--------------

The modules in ``python-can`` are:

+---------------------------------+------------------------------------------------------+
|Module                           | Description                                          |
+=================================+======================================================+
|:doc:`broadcastmanager.py <bcm>` | Contains interface independent broadcast manager     |
|                                 | code.                                                |
+---------------------------------+------------------------------------------------------+
|:doc:`bus.py <bus>`              | Contains the interface independent Bus object.       |
+---------------------------------+------------------------------------------------------+
|:doc:`CAN.py <api>`              | Contains modules to emulate a CAN system, such as a  |
|                                 | time stamps, read/write streams and listeners.       |
+---------------------------------+------------------------------------------------------+
|:doc:`message.py <message>`      | Contains the interface independent Message object.   |
+---------------------------------+------------------------------------------------------+
|:doc:`notifier.py <api>`         | An object which can be used to notify listeners.     |
+---------------------------------+------------------------------------------------------+


