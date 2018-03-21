CAN over Serial / SLCAN
========================

A text based interface: compatible to slcan-interfaces (slcan ASCII protocol) should also support LAWICEL direct.
These interfaces can also be used with socketcan and slcand with Linux.
This driver directly uses the serial port, it makes slcan-compatible interfaces usable with Windows also.
Hint: Arduino-Interface could easyly be build https://github.com/latonita/arduino-canbus-monitor


Bus
---

.. autoclass:: can.interfaces.serial.slcan.SlcanBus

Internals
---------

.. TODO:: Document internals of slcan interface.
