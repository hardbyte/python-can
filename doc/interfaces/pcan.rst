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

macOS timestamps after system sleep
-----------------------------------

On macOS, the PCAN interface uses the third-party
`PCBUSB library <https://github.com/mac-can/PCBUSB-Library>`__.
With PCBUSB 0.13, received message timestamps have been reported to lag
wall-clock time after system sleep. The reported offset grows with the
accumulated sleep duration since boot, including sleep before the bus was
opened. Disconnecting and reconnecting the adapter did not correct the offset
in the reported test.

When boot time is available, the PCAN backend converts the driver's elapsed
timestamp to Unix time by adding the system boot time. If that elapsed counter excludes system sleep, this
conversion produces an incorrect date. BLF and CSV logging preserve the
received message timestamp, so changing the log format does not correct it.
See :issue:`2092` and the related
`PCBUSB report <https://github.com/mac-can/PCBUSB-Library/issues/26>`__
for the observations and the library maintainer's response.

To investigate on an affected Mac, receive continuous traffic from a known
source, consume messages promptly, and compare ``message.timestamp`` with
``time.time()`` before and after a recorded system sleep. Also test a capture
started after the Mac has already slept since boot. Record the macOS, Python,
python-can and PCBUSB versions, the adapter model, and the sleep duration.
Account for receive-queue delays: the time at which an application reads a
message can be later than the time at which the message was received.

When accurate calendar timestamps are required, avoid system sleep from boot
through the end of the capture and verify the timestamps against an independent
reference. This limitation has been reported on macOS; the linked reports do
not establish the behavior on Windows or Linux.

Bus
---

.. autoclass:: can.interfaces.pcan.PcanBus
    :members:
