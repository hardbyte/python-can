.. _ixxatdoc:

IXXAT Virtual CAN Interface
===========================

Interface to `IXXAT <http://www.ixxat.com/>`__ Virtual CAN Interface V3 SDK. Works on Windows.

The Linux ECI SDK is currently unsupported, however on Linux some devices are
supported with :doc:`socketcan`.

The :meth:`~can.interfaces.ixxat.canlib.IXXATBus.send_periodic` method is supported
natively through the on-board cyclic transmit list.
Modifying cyclic messages is not possible. You will need to stop it, and then
start a new periodic message.


Bus
---

.. autoclass:: can.interfaces.ixxat.IXXATBus
    :members:

.. autoclass:: can.interfaces.ixxat.canlib.CyclicSendTask
    :members:


Configuration file
------------------
The simplest configuration file would be::

    [default]
    interface = ixxat
    channel = 0

Python-can will search for the first IXXAT device available and open the first channel.
``interface`` and ``channel`` parameters are interpreted by frontend ``can.interfaces.interface``
module, while the following parameters are optional and are interpreted by IXXAT implementation.

* ``bitrate`` (default 500000) Channel bitrate
* ``UniqueHardwareId`` (default first device) Unique hardware ID of the IXXAT device
* ``rxFifoSize`` (default 16) Number of RX mailboxes
* ``txFifoSize`` (default 16) Number of TX mailboxes
* ``extended`` (default False) Allow usage of extended IDs


Internals
---------

The IXXAT :class:`~can.BusABC` object is a fairly straightforward interface
to the IXXAT VCI library. It can open a specific device ID or use the
first one found.

The frame exchange *do not involve threads* in the background but is
explicitly instantiated by the caller.

- ``recv()`` is a blocking call with optional timeout.
- ``send()`` is not blocking but may raise a VCIError if the TX FIFO is full

RX and TX FIFO sizes are configurable with ``rxFifoSize`` and ``txFifoSize``
options, defaulting at 16 for both.

The CAN filters act as a "whitelist" in IXXAT implementation, that is if you
supply a non-empty filter list you must explicitly state EVERY frame you want
to receive (including RTR field).
The can_id/mask must be specified according to IXXAT behaviour, that is
bit 0 of can_id/mask parameters represents the RTR field in CAN frame. See IXXAT
VCI documentation, section "Message filters" for more info.
