.. _ixxatdoc:

IXXAT Virtual CAN Interface
===========================


Bus
---

.. autoclass:: can.interfaces.ixxat.canlib.Bus


Internals
---------

The IXXAT :class:`~can.Bus` object is a farly straightforward interface
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

.. hint:: Module uses ``can.ixxat`` logger and at DEBUG level logs every frame
	sent or received. It may be too verbose for your purposes.

