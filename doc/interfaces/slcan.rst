CAN over Serial / SLCAN
========================

A text based interface: compatible to SLCAN / LAWICEL / CAN232 interfaces (ASCII protocols). For example use over
serial ports like ``/dev/ttyS1`` or ``/dev/ttyUSB0`` on Linux machines or ``COM1`` on Windows.
This driver directly uses the serial port, it makes SLCAN compatible interfaces usable with Windows also.

.. note::
    Arduino-Interface could easily be build with https://github.com/latonita/arduino-canbus-monitor

.. note::
    These interfaces can also be used with socketcan and slcand with Linux.

Bus
---

.. autoclass:: can.interfaces.serial.slcan.SlcanBus

Internals
---------

At the moment only the send and receive methods from the interface are available.

.. note::
    Specification: http://www.can232.com/docs/can232_v3.pdf

.. TODO:: Document internals of slcan interface.
