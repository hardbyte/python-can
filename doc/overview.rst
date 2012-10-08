Developers Overview
===================

Code Structure
--------------

The modules in ``python-can`` are:

+----------------------------+------------------------------------------------------+
|Module                      | Description                                          |
+============================+======================================================+
|:doc:`CAN.py <api>`         | Contains modules to emulate a CAN system, such as a  |
|                            | time stamps, read/write streams and listeners.       |
+----------------------------+------------------------------------------------------+
|:doc:`bus.py <\bus>`        |Contains the interface independent Bus object.        |
+----------------------------+------------------------------------------------------+
|:doc:`message.py <\message>`|Contains the interface independent Message object.    |
+----------------------------+------------------------------------------------------+
|constants.py                | Contains the linux header constants.                 |
+----------------------------+------------------------------------------------------+


CAN Interface Modules
---------------------

Found under ``can.interfaces`` are the imlementations for each backend:

.. toctree::
   :maxdepth: 1
   
   socketcan_ctypes
   socketcan_native
