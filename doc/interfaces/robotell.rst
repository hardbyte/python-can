.. _robotell:

Robotell CAN-USB interface
==========================

An USB to CAN adapter sold on Aliexpress, etc. with the manufacturer name Robotell printed on the case.
There is also a USB stick version with a clear case. If the description or screenshots refer to ``EmbededDebug`` or ``EmbededConfig``
the device should be compatible with this driver.
These USB devices are based on a STM32 controller with a CH340 serial interface and use a binary protocol - NOT compatible with SLCAN

See `https://www.amobbs.com/thread-4651667-1-1.html <https://www.amobbs.com/thread-4651667-1-1.html>`_ for some background on these devices.

This driver directly uses either the local or remote (not tested) serial port.
Remote serial ports will be specified via special URL. Both raw TCP sockets as also RFC2217 ports are supported.

Usage: use ``port or URL[@baurate]`` to open the device.
For example use ``/dev/ttyUSB0@115200`` or ``COM4@9600`` for local serial ports and
``socket://192.168.254.254:5000`` or ``rfc2217://192.168.254.254:5000`` for remote ports.



Bus
---

.. autoclass:: can.interfaces.robotell.robotellBus
    :members:

