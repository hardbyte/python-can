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

Python 3
--------

The Python 'socket' module contains support for SocketCAN in version 3.3.
This library started targeting Python 3 as it was released as open source
in 2013.

Broadcast Connection Manager
----------------------------

From Python 3.4 BCM is natively supported so the plan is to integrate natively
when Python 3.4 is more widespread. For now BCM is possible with the socketcan
ctypes backend.
