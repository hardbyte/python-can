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
Support for pcan on Mac was added by Kristian Sloth Lauszus in 2018.

The usb2can interface was contributed by Joshua Villyard in 2015.

The IXXAT VCI interface was contributed by Giuseppe Corbelli and funded
by `Weightpack <http://www.weightpack.com>`__ in 2016.

The NI-CAN and virtual interfaces plus the ASCII and BLF loggers were
contributed by Christian Sandberg in 2016 and 2017. The BLF format is based on
a C++ library by Toby Lorenz.

The slcan interface, ASCII listener and log logger and listener were contributed
by Eduard Bröcker in 2017.

The NeoVi interface for ICS (Intrepid Control Systems) devices was contributed
by Pierre-Luc Tessier Gagné in 2017.

Many improvements all over the library, cleanups, unifications as well as more
comprehensive documentation and CI testing was contributed by Felix Divo in 2017
and 2018.

The CAN viewer terminal script was contributed by Kristian Sloth Lauszus in 2018.

The CANalyst-II interface was contributed by Shaoyu Meng in 2018.

Support for CAN within Python
-----------------------------

Python natively supports the CAN protocol from version 3.3 on, if running on Linux:

==============  ==============================================================  ====
Python version  Feature                                                         Link
==============  ==============================================================  ====
3.3             Initial SocketCAN support                                       `Docs <https://docs.python.org/3/library/socket.html#socket.AF_CAN>`__
3.4             Broadcast Management (BCM) commands are natively supported      `Docs <https://docs.python.org/3/library/socket.html#socket.CAN_BCM>`__
3.5             CAN FD support                                                  `Docs <https://docs.python.org/3/library/socket.html#socket.CAN_RAW_FD_FRAMES>`__
3.7             Support for CAN ISO-TP                                          `Docs <https://docs.python.org/3/library/socket.html#socket.CAN_ISOTP>`__
==============  ==============================================================  ====
