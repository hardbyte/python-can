History and Roadmap
===================

Background
----------

Originally written at `Dynamic Controls <https://dynamiccontrols.com>`__
for internal use testing and prototyping wheelchair components.

Maintenance was taken over and the project was open sourced by Brian Thorne in 2010.


Acknowledgements
----------------

Originally written by Ben Powell as a thin wrapper around the Kvaser SDK
to support the leaf device.

Support for linux socketcan was added by Rose Lu as a summer coding
project in 2011. The socketcan interface was helped immensely by Phil Dixon
who wrote a leaf-socketcan driver for Linux.

The pcan interface was contributed by Albert Bloomfield in 2013.

The usb2can interface was contributed by Joshua Villyard in 2015

The IXXAT VCI interface was contributed by Giuseppe Corbelli and funded
by Weightpack in 2016


Support for CAN within Python
-----------------------------

The 'socket' module contains support for SocketCAN from Python 3.3.

From Python 3.4 broadcast management commands are natively supported.
