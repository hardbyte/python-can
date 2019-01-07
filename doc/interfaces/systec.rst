.. _systec:

SYSTEC interface
================

Windows interface for the USBCAN devices supporting up to 2 channels based on the
particular product. There is support for the devices also on Linux through the :doc:`socketcan` interface and for Windows using this
``systec`` interface.

Installation
------------

The interface requires installation of the **USBCAN32.dll** library. Download and install the
driver for specific `SYSTEC <https://www.systec-electronic.com/en/products/>`__ device.

Supported devices
-----------------

The interface supports following devices:

- GW-001 (obsolete),
- GW-002 (obsolete),
- Multiport CAN-to-USB G3,
- USB-CANmodul1 G3,
- USB-CANmodul2 G3,
- USB-CANmodul8 G3,
- USB-CANmodul16 G3,
- USB-CANmodul1 G4,
- USB-CANmodul2 G4.

Bus
---

.. autoclass:: can.interfaces.systec.ucanbus.UcanBus
    :members:

Configuration
-------------

The simplest configuration would be::

    interface = systec
    channel = 0

Python-can will search for the first device found if not specified explicitly by the
``device_number`` parameter. The ``interface`` and ``channel`` are the only mandatory
parameters. The interface supports two channels 0 and 1. The maximum number of entries in the receive and transmit buffer can be set by the
parameters ``rx_buffer_entries`` and ``tx_buffer_entries``, with default value 4096
set for both.

Optional parameters:

* ``bitrate`` (default 500000) Channel bitrate in bit/s
* ``device_number`` (default first device) The device number of the USB-CAN
* ``rx_buffer_entries`` (default 4096) The maximum number of entries in the receive buffer
* ``tx_buffer_entries`` (default 4096) The maximum number of entries in the transmit buffer
* ``state`` (default BusState.ACTIVE) BusState of the channel
* ``receive_own_messages`` (default False) If messages transmitted should also be received back

Internals
---------

Message filtering
~~~~~~~~~~~~~~~~~

The interface and driver supports only setting of one filter per channel. If one filter
is requested, this is will be handled by the driver itself. If more than one filter is
needed, these will be handled in Python code in the ``recv`` method. If a message does
not match any of the filters, ``recv()`` will return None.

Periodic tasks
~~~~~~~~~~~~~~

The driver supports periodic message sending but without the possibility to set
the interval between messages. Therefore the handling of the periodic messages is done
by the interface using the :class:`~can.broadcastmanager.ThreadBasedCyclicSendTask`.
