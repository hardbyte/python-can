Introduction and Installation 
=============================

Background
----------

The pycanlib-socketcan library is built upon the leaf-socketcan driver written
by Phil Dixon (pdixon@dynamiccontrols.com). This driver replaces the functionality of the current Kvaser
provided driver and API, libcanlib. The purpose of the switch is to:

*   Utilise SocketCAN, which is part of the standard system utilities of Linux.  
    A lot of other CAN related applications are built upon SocketCAN. 
*   Speed

Currently, CAN messages can be received but not sent. The implementation 
of this functionality needs to be completed in the leaf-socketcan driver
before it can be added at the pycanlib-leaf level. 

pycanlib-socketcan is completely compatible with py1939lib and pyunidrivelib. 

For those familiar with pycanlib, the main change to it has been the replacement
of canlib.py with socketcanlib.py. Also InputValidation has been removed.  

The Python 'socket' module contains support for SocketCAN in version 3.3. 

.. include:: ../README.txt

