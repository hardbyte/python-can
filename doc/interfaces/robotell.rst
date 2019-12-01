.. _robotell:

Chinese CAN-USB interface (mfg. Robotell etc.)
==============================================

A USB to CAN adapter sold on Aliexpress and other online vendors with the manufacturer name Robotell printed on the case.
There is also a USB stick version with a clear case. See if the description or screenshots refers to ``EmbededDebug`` or ``EmbededConfig``.
Thesus USB devices are based on a STM32 controller with a CH340 serial interface and use a binary protocol - NOT compatible with SLCAN
This driver directly uses either the local or remote (not tested) serial port.
Remote serial ports will be specified via special URL. Both raw TCP sockets as also RFC2217 ports are supported.

See ``https://www.amobbs.com/thread-4651667-1-1.html`` for some background on these devices.

Usage: use ``port or URL[@baurate]`` to open the device.
For example use ``/dev/ttyUSB0@115200`` or ``COM4@9600`` for local serial ports and
``socket://192.168.254.254:5000`` or ``rfc2217://192.168.254.254:5000`` for remote ports.


Supported devices
-----------------

.. todo:: Document this.


Bus
---

.. autoclass:: can.interfaces.robotell.robotellBus
    :members:


Internals
---------

.. todo:: Document the internals of robotell interface.
