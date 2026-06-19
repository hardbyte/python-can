USB2CAN Interface
=================

OVERVIEW
--------

The `USB2CAN <http://www.8devices.com/products/usb2can>`_ is a cheap CAN interface. Two versions exist, "Korlan" and a previous edition.
Both are based on STM32 chips.

There is support for this device on Linux through the :doc:`socketcan` interface and for Windows using the
``usb2can`` interface.

This interface supports any platform with a working "pyusb".

The device has been tested on OS X at 500kbaud against a device spamming 300+ messages/second, so it should be decently robust.

INSTALL
_______

Install `pyusb` and a working pyusb backend (on most platforms, this is `libusb1`).

This should be the only required action.

Interface Layout
----------------

`USB2CanLibUsbBus` implements the basic `python-can` Bus for this device.

`Can8DevUSBDevice` implements an abstract device driver for the hardware, based on `pyusb` and the SocketCAN kernel module for the device.

`Can8DevUSBDevice` uses a Queue and a read thread to ensure that messages are read into host hardware before they overflow the internal buffers in the device. The `recv` methods simply poll the read queue for available messages.
 
Interface Specific Items
------------------------

This device is really an oddball. It works well, but documentation is quite sparse.

Filtering is not implemented because the details of how to use it are not documented in any way.


.. warning::

    Currently message filtering is not implemented. Contributions are most welcome!


Bus
---

.. autoclass:: can.interfaces.usb2can_libusb.Usb2CanLibUsbBus


Internals
---------

.. autoclass:: can.interfaces.usb2can_libusb.Can8DevUSBDevice
   :members:
   :undoc-members:
