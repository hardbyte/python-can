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


Class based API
---------------

.. autoclass:: can.broadcastmanager.CyclicTask
    :members:


.. autoclass:: can.broadcastmanager.CyclicSendTaskABC
    :members:

.. autoclass:: can.broadcastmanager.LimitedDurationCyclicSendTaskABC
    :members:


.. autoclass:: can.broadcastmanager.RestartableCyclicTaskABC
    :members:


.. autoclass:: can.broadcastmanager.ModifiableCyclicTaskABC
    :members:

.. autoclass:: can.broadcastmanager.MultiRateCyclicSendTaskABC
    :members:

.. autoclass:: can.broadcastmanager.ThreadBasedCyclicSendTask
    :members:



Functional API
--------------

.. note::
    The functional API in :func:`can.broadcastmanager.send_periodic` is now deprecated.
    Use the object oriented API via :meth:`can.BusABC.send_periodic` instead.


.. autofunction:: can.broadcastmanager.send_periodic

