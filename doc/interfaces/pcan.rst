.. _pcandoc:

PCAN Basic API
==============

Interface to `Peak-System <https://www.peak-system.com/?&L=1/>`__'s PCAN-Basic API.

Windows driver: https://www.peak-system.com/Downloads.76.0.html?&L=1

Linux driver: https://www.peak-system.com/fileadmin/media/linux/index.htm#download and https://www.peak-system.com/Downloads.76.0.html?&L=1 (PCAN-Basic API (Linux))

Mac driver: http://www.mac-can.com

Configuration
-------------

Here is an example configuration file for using `PCAN-USB <https://www.peak-system.com/PCAN-USB.199.0.html?&L=1>`_:

::

    [default]
    interface = pcan
    channel = PCAN_USBBUS1
    state = can.bus.BusState.PASSIVE
    bitrate = 500000

``channel``: (default PCAN_USBBUS1) CAN interface name

``state``: (default can.bus.BusState.ACTIVE) BusState of the channel

``bitrate``: (default 500000) Channel bitrate

Valid ``channel`` values:

::

    PCAN_ISABUSx
    PCAN_DNGBUSx
    PCAN_PCIBUSx
    PCAN_USBBUSx
    PCAN_PCCBUSx
    PCAN_LANBUSx

Where ``x`` should be replaced with the desired channel number starting at 1.

Linux installation
------------------

Kernels >= 3.4 supports the PCAN adapters natively via :doc:`/interfaces/socketcan`, refer to: :ref:`socketcan-pcan`.

Bus
---

.. autoclass:: can.interfaces.pcan.PcanBus
