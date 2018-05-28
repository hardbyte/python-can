Broadcast Manager
=================

The broadcast manager isn't yet supported by all interfaces.
Currently SockerCAN and IXXAT are supported at least partially.
It allows the user to setup periodic message jobs.

If periodic transmission is not supported natively, a software thread
based scheduler is used as a fallback.

This example shows the socketcan_ctypes backend using the broadcast manager:


.. literalinclude:: ../examples/cyclic.py
    :language: python
    :linenos:


.. note::
    The functional APi in :meth:`can.send_periodic` is now deprected.
    Use the object oriented APi in :meth:`can.BusABC.send_periodic` instead.


Class based API
---------------

.. autoclass:: can.CyclicSendTaskABC
    :members:


.. autoclass:: can.MultiRateCyclicSendTaskABC
    :members:
