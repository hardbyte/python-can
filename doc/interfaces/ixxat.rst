.. _ixxatdoc:

IXXAT Virtual Communication Interface
=====================================

Interface to `IXXAT <http://www.ixxat.com/>`__ Virtual Communication Interface V3 SDK. Works on Windows.

The Linux ECI SDK is currently unsupported, however on Linux some devices are
supported with :doc:`socketcan`.

The :meth:`~can.BusABC.send_periodic` method is supported
natively through the on-board cyclic transmit list.
Modifying cyclic messages is not possible. You will need to stop it, and then
start a new periodic message.


Configuration
-------------
The simplest configuration file would be::

    [default]
    interface = ixxat
    channel = 0

Python-can will search for the first IXXAT device available and open the first channel.
``interface`` and ``channel`` parameters are interpreted by frontend ``can.interfaces.interface``
module, while the following parameters are optional and are interpreted by IXXAT implementation.

* ``receive_own_messages`` (default False) Enable self-reception of sent messages.
* ``unique_hardware_id`` (default first device) Unique hardware ID of the IXXAT device.
* ``extended`` (default True) Allow usage of extended IDs.
* ``fd`` (default False) Enable CAN-FD capabilities.
* ``rx_fifo_size`` (default 16 for CAN, 1024 for CAN-FD) Number of RX mailboxes.
* ``tx_fifo_size`` (default 16 for CAN, 128 for CAN-FD) Number of TX mailboxes.
* ``bitrate`` (default 500000) Channel bitrate.
* ``data_bitrate`` (defaults to 2Mbps) Channel data bitrate (only canfd, to use when message bitrate_switch is used).
* ``sjw_abr`` (optional, only canfd) Bus timing value sample jump width (arbitration).
* ``tseg1_abr`` (optional, only canfd) Bus timing value tseg1 (arbitration).
* ``tseg2_abr`` (optional, only canfd) Bus timing value tseg2 (arbitration).
* ``sjw_dbr`` (optional, only used if baudrate switch enabled) Bus timing value sample jump width (data).
* ``tseg1_dbr`` (optional, only used if baudrate switch enabled) Bus timing value tseg1 (data).
* ``tseg2_dbr`` (optional, only used if baudrate switch enabled) Bus timing value tseg2 (data).
* ``ssp_dbr`` (optional, only used if baudrate switch enabled) Secondary sample point (data).



Filtering
---------

The CAN filters act as an allow list in IXXAT implementation, that is if you
supply a non-empty filter list you must explicitly state EVERY frame you want
to receive (including RTR field).
The can_id/mask must be specified according to IXXAT behaviour, that is
bit 0 of can_id/mask parameters represents the RTR field in CAN frame. See IXXAT
VCI documentation, section "Message filters" for more info.

List available devices
----------------------
In case you have connected multiple IXXAT devices, you have to select them by using their unique hardware id.
To get a list of all connected IXXAT you can use the function ``get_ixxat_hwids()`` as demonstrated below:

    >>> from can.interfaces.ixxat import get_ixxat_hwids
    >>> for hwid in get_ixxat_hwids():
    ...     print("Found IXXAT with hardware id '%s'." % hwid)
    Found IXXAT with hardware id 'HW441489'.
    Found IXXAT with hardware id 'HW107422'.


Bus
---

.. autoclass:: can.interfaces.ixxat.IXXATBus
    :members:

Implementation based on vcinpl.dll
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: can.interfaces.ixxat.canlib_vcinpl.IXXATBus
    :members:

.. autoclass:: can.interfaces.ixxat.canlib_vcinpl.CyclicSendTask
    :members:

Implementation based on vcinpl2.dll
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: can.interfaces.ixxat.canlib_vcinpl2.IXXATBus
    :members:

.. autoclass:: can.interfaces.ixxat.canlib_vcinpl2.CyclicSendTask
    :members:



Internals
---------

The IXXAT :class:`~can.BusABC` object is a fairly straightforward interface
to the IXXAT VCI library. It can open a specific device ID or use the
first one found.

The frame exchange *does not involve threads* in the background but is
explicitly instantiated by the caller.

- ``recv()`` is a blocking call with optional timeout.
- ``send()`` is not blocking but may raise a VCIError if the TX FIFO is full

RX and TX FIFO sizes are configurable with ``rx_fifo_size`` and ``tx_fifo_size``
options, defaulting to 16 for both.

