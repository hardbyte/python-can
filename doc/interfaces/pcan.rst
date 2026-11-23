.. _pcandoc:

PCAN Basic API
==============

Interface to `Peak-System <https://www.peak-system.com>`__'s PCAN-Basic API.

Configuration
-------------

Here is an example configuration file for using `PCAN-USB <https://www.peak-system.com/PCAN-USB.199.0.html?&L=1>`_:

::

    [default]
    interface = pcan
    channel = PCAN_USBBUS1
    state = PASSIVE
    bitrate = 500000

``channel`` (default ``"PCAN_USBBUS1"``)
 CAN interface name.
 Valid ``channel`` values::

    PCAN_ISABUSx
    PCAN_DNGBUSx
    PCAN_PCIBUSx
    PCAN_USBBUSx
    PCAN_PCCBUSx
    PCAN_LANBUSx

 Where ``x`` should be replaced with the desired channel number starting at ``1``.

``state`` (default ``can.bus.BusState.ACTIVE``)
 BusState of the channel

``bitrate`` (default ``500000``)
 Channel bitrate


.. _pcandoc linux installation:

Linux installation
------------------

Beginning with version 3.4, Linux kernels support the PCAN adapters natively via :doc:`/interfaces/socketcan`, refer to: :ref:`socketcan-pcan`.

Timestamps
----------

PCAN-Basic on Linux provides timestamps relative to the Unix epoch, so no boot-time
offset or ``uptime`` package is needed. On other supported platforms, install
``python-can[pcan]`` to use ``uptime`` for conversion of boot-relative timestamps to
epoch timestamps. Without a known boot time, those platforms retain relative
timestamps.

Bus
---

.. autoclass:: can.interfaces.pcan.PcanBus
    :members:
