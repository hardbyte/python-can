Bit Timing Configuration
========================

.. attention::
    This feature is experimental. The implementation might change in future
    versions.

The CAN protocol, specified in ISO 11898, allows the bitrate, sample point
and number of samples to be optimized for a given application. These
parameters, known as bit timings, can be adjusted to meet the requirements
of the communication system and the physical communication channel.

These parameters include:

* **tseg1**: The time segment (TSEG1) is the amount of time from the start
  of the bit until the sample point. It is expressed in time quanta (TQ).
* **tseg2**: The time segment (TSEG2) is the amount of time from the
  sample point until the end of the bit. It is expressed in TQ.
* **sjw**: The synchronization jump width (SJW) is the maximum number
  of TQ that the controller can resynchronize every bit.
* **sample point**: The sample point is defined as the point in time
  within a bit where the bus controller samples the bus for dominant or
  recessive levels. It is typically expressed as a percentage of the bit time.
  The sample point depends on the bus length and propagation time as well
  as the information processing time of the nodes.

For example, consider a bit with a total duration of 8 TQ and a sample
point at 75%. The values for TSEG1, TSEG2 and SJW would be 5, 2, and 2,
respectively. The sample point would be 6 TQ after the start of the bit,
leaving 2 TQ for the signal to stabilize before the end of the bit.

.. note::
   The values for TSEG1, TSEG2 and SJW are chosen such that the
   sample point is at least 50% of the total bit time. This ensures that
   there is sufficient time for the signal to stabilize before it is sampled.

.. note::
   In CAN FD, the arbitration (nominal) phase and the data phase can have
   different bit rates. As a result, there are two separate sample points
   to consider.

In most cases, the recommended settings for a predefined set of common
bit rates will work just fine. In some cases, however, it may be necessary
to specify custom bit timings. The :class:`can.BitTiming` and
:class:`can.BitTimingFd` classes can be used for this purpose to specify
bit timings in a relatively interface agnostic manner.

It is possible to specify the same settings for a CAN 2.0 bus
using the config file:


.. code-block:: none

    [default]
    f_clock=8000000
    bitrate=1000000
    tseg1=5
    tseg2=2
    sjw=1
    nof_samples=1

The same is possible for CAN FD:

.. code-block:: none

    [default]
    f_clock=80000000
    nom_bitrate=500000
    nom_tseg1=119
    nom_tseg2=40
    nom_sjw=40
    data_bitrate=2000000
    data_tseg1=29
    data_tseg2=10
    data_sjw=10


.. autoclass:: can.BitTiming
    :class-doc-from: both
    :show-inheritance:
    :members:

.. autoclass:: can.BitTimingFd
    :class-doc-from: both
    :show-inheritance:
    :members:

.. _Wikipedia: https://en.wikipedia.org/wiki/CAN_bus#Bit_timing
.. _Kvaser: https://www.kvaser.com/about-can/the-can-protocol/can-bit-timing/
