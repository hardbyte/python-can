.. _slcan:

CAN over Serial / SLCAN
========================

A text based interface: compatible to slcan-interfaces (slcan ASCII protocol) should also support LAWICEL direct.
These interfaces can also be used with socketcan and slcand with Linux.
This driver directly uses the serial port, it makes slcan-compatible interfaces usable with Windows also.
Hint: Arduino-Interface could easyly be build https://github.com/latonita/arduino-canbus-monitor

Usage: use ``port[@baurate]`` to open the device.
For example use ``/dev/ttyUSB0@115200`` or ``COM4@9600``


Bus
---

.. autoclass:: can.interfaces.slcan.slcanBus

Internals
---------

.. TODO:: Implement and document slcan interface.
