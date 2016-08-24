History and Roadmap
===================

Background
----------

Dynamic Controls has been using and maintaining this library since 2009.
Originally written by Ben Powell as a thin wrapper around the Kvaser SDK
to support the leaf device. Maintenance was taken over and the project was
open sourced by Brian Thorne in 2010.

Original support for linux socketcan was added by Rose Lu as a summer coding
project in 2011.

The socketcan interface was helped immensely by Phil Dixon who wrote a 
leaf-socketcan driver for Linux.

The pcan interface was contributed by Albert Bloomfield in 2013.

The usb2can interface was contributed by Joshua Villyard in 2015

The IXXAT VCI interface was contributed by Giuseppe Corbelli and funded
by Weightpack in 2016


Python 3
--------

The Python 'socket' module contains support for SocketCAN from version 3.3.
This library has supported Python 3 from initial open source release in
2013.

Broadcast Connection Manager
----------------------------

From Python 3.4 BCM is natively supported, BCM is also possible with the socketcan
ctypes backend.
