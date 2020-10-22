.. _gs_usb:

CAN driver based on WCID for Geschwister Schneider USB/CAN devices and bytewerk.org candleLight USB CAN interfaces
==================================================================================================================

Windows/Linux/Mac CAN driver based on WCID for Geschwister Schneider USB/CAN devices and candleLight USB CAN interfaces.

Install: ``pip install "python-can[gs_usb]"``

Usage: pass ``bus`` and ``address`` to open the device. The parameters can be got by ``pyusb`` as shown below:

::

    import usb
    import can

    dev = usb.core.find(idVendor=0x1D50, idProduct=0x606F)
    bus = can.Bus(bustype="gs_usb", channel=dev.product, bus=dev.bus, address=dev.address, bitrate=250000)


Supported devices
-----------------

Geschwister Schneider USB/CAN devices and bytewerk.org candleLight USB CAN interfaces such as candleLight, canable, cantact, etc.


Supported platform
------------------

Windows, Linux and Mac.

Note: Since ``pyusb`` is used, ``libusb-win32`` usb driver is required to be installed in Windows

Bus
---

.. autoclass:: can.interfaces.gs_usb.GsUsbBus
    :members:
