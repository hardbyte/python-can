NI-CAN
======

This interface adds support for CAN controllers by `National Instruments`_.


.. warning::

    NI-CAN only seems to support 32-bit architectures so if the driver can't
    be loaded on a 64-bit Python, try using a 32-bit version instead.


.. warning::

    CAN filtering has not been tested thoroughly and may not work as expected.


Bus
---

.. autoclass:: can.interfaces.nican.NicanBus

.. autoexception:: can.interfaces.nican.NicanError


.. _National Instruments: http://www.ni.com/can/
