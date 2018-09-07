.. _slcan:

CAN over Serial / SLCAN
========================

A text based interface: compatible to slcan-interfaces (slcan ASCII protocol) should also support LAWICEL direct.
These interfaces can also be used with socketcan and slcand with Linux.
This driver directly uses either the local or remote serial port, it makes slcan-compatible interfaces usable with Windows also.
Remote serial ports will be specified via special URL. Both raw TCP sockets as also RFC2217 ports are supported.

Usage: use ``port or URL[@baurate]`` to open the device.
For example use ``/dev/ttyUSB0@115200`` or ``COM4@9600`` for local serial ports and
``socket://192.168.254.254:5000`` or ``rfc2217://192.168.254.254:5000`` for remote ports.

.. note:
    An Arduino-Interface could easily be build with this:
    https://github.com/latonita/arduino-canbus-monitor


Supported devices
-----------------

.. todo:: Document this.


Bus
---

.. autoclass:: can.interfaces.slcan.slcanBus
    :members:


Internals
---------

.. todo:: Document the internals of slcan interface.
