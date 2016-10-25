NI-CAN
======

This interface adds support for CAN controllers by `National Instruments`_.


Message filtering
-----------------

It seems like only one filter can be used per channel so if more than one is
specified then the filtering will be disabled.


Bus
---

.. autoclass:: can.interfaces.nican.NicanBus

.. autoexception:: can.interfaces.nican.NicanError


.. _National Instruments: http://www.ni.com/can/
