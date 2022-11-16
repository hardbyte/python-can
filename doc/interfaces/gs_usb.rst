.. _gs_usb:

Geschwister Schneider and candleLight
=====================================

Windows/Linux/Mac CAN driver based on usbfs or WinUSB WCID for Geschwister Schneider USB/CAN devices
and candleLight USB CAN interfaces.

Install: ``pip install "python-can[gs_usb]"``

Usage: pass device ``index`` (starting from 0) if using automatic device detection:

::

    import can

    bus = can.Bus(bustype="gs_usb", channel=dev.product, index=0, bitrate=250000)

Alternatively, pass ``bus`` and ``address`` to open a specific device. The parameters can be got by ``pyusb`` as shown below:

.. code-block:: python

    import usb
    import can

    dev = usb.core.find(idVendor=0x1D50, idProduct=0x606F)
    bus = can.Bus(
        bustype="gs_usb",
        channel=dev.product,
        bus=dev.bus,
        address=dev.address,
        bitrate=250000
    )


Supported devices
-----------------

Geschwister Schneider USB/CAN devices and bytewerk.org candleLight USB CAN interfaces such as candleLight, canable, cantact, etc.


Supported platform
------------------

Windows, Linux and Mac.

.. note::

   The backend driver depends on `pyusb <https://pyusb.github.io/pyusb/>`_ so a ``pyusb`` backend driver library such as
   ``libusb`` must be installed.

   On Windows a tool such as `Zadig <https://zadig.akeo.ie/>`_ can be used to set the USB device driver to
   ``libusb-win32``.


Supplementary Info
------------------

The firmware implementation for Geschwister Schneider USB/CAN devices and candleLight USB CAN can be found in `candle-usb/candleLight_fw <https://github.com/candle-usb/candleLight_fw>`_.
The Linux kernel driver can be found in `linux/drivers/net/can/usb/gs_usb.c <https://github.com/torvalds/linux/blob/master/drivers/net/can/usb/gs_usb.c>`_.

The ``gs_usb`` interface in ``python-can`` relies on upstream ``gs_usb`` package, which can be found in
`https://pypi.org/project/gs-usb/ <https://pypi.org/project/gs-usb/>`_ or
`https://github.com/jxltom/gs_usb <https://github.com/jxltom/gs_usb>`_.

The ``gs_usb`` package uses ``pyusb`` as backend, which brings better cross-platform compatibility.

Note: The bitrate ``10K``, ``20K``, ``50K``, ``83.333K``, ``100K``, ``125K``, ``250K``, ``500K``, ``800K`` and ``1M`` are supported in this interface, as implemented in the upstream ``gs_usb`` package's ``set_bitrate`` method.

.. warning::
   Message filtering is not supported in Geschwister Schneider USB/CAN devices and bytewerk.org candleLight USB CAN interfaces.

Bus
---

.. autoclass:: can.interfaces.gs_usb.GsUsbBus
    :members:
