Bit Timing Configuration
========================

The CAN protocol allows the bitrate, sample point and number of samples to be
optimized for a given application. You can read more on Wikipedia_, Kvaser_
and other sources.

In most cases the recommended settings for a predefined set of common
bitrates will work just fine. In some cases it may however be necessary to specify
custom settings. The :class:`can.BitTiming` class can be used for this purpose to
specify them in a relatively interface agnostic manner.

It is also possible to specify the same settings for a CAN 2.0 bus
using the config file:


.. code-block:: none

    [default]
    bitrate=1000000
    f_clock=8000000
    tseg1=5
    tseg2=2
    sjw=1
    nof_samples=1


.. code-block:: none

    [default]
    brp=1
    tseg1=5
    tseg2=2
    sjw=1
    nof_samples=1


.. code-block:: none

    [default]
    btr0=0x00
    btr1=0x14


.. autoclass:: can.BitTiming


.. _Wikipedia: https://en.wikipedia.org/wiki/CAN_bus#Bit_timing
.. _Kvaser: https://www.kvaser.com/about-can/the-can-protocol/can-bit-timing/
