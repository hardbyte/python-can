.. _slcan:

CANine libusb Driver
========================

A USB-based (via libusb) binary interface that is compatible with the CANine and Canable (v0.4) adapters. Offers better perfromance than slcan, especially in some Windows machines where there are issues with serial port performance.

Windows users will need to install the libusb driver for their device. The easiest way to do this is using `Zadig <https://zadig.akeo.ie/>`.

Supported devices
-----------------

- `CANine <https://github.com/tinymovr/CANine>`
- `Canable <https://github.com/normaldotcom/canable-fw>`


Bus
---

.. autoclass:: can.interfaces.canine.CANineBus
    :members:


Internals
---------

The interface adopts the same commands as slcan. However, the commands and data are transferred as binary packets of predefined length. The adapter firmware is derived from slcan, but exchanges the serial communication and VCP identification for USB CDC comms.

.. todo:: Document packet structure.