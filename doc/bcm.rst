Broadcast Manager
=================

.. module:: can.broadcastmanager

The broadcast manager isn't yet supported by all interfaces.
Currently SocketCAN and IXXAT are supported at least partially.
It allows the user to setup periodic message jobs.

If periodic transmission is not supported natively, a software thread
based scheduler is used as a fallback.

This example shows the socketcan_ctypes backend using the broadcast manager:

.. literalinclude:: ../examples/cyclic.py
    :language: python
    :linenos:


Message Sending Tasks
~~~~~~~~~~~~~~~~~~~~~

The class based api for the broadcast manager uses a series of
`mixin classes <https://www.ianlewis.org/en/mixins-and-python>`_.
All mixins inherit from :class:`~can.CyclicSendTaskABC`

.. autoclass:: CyclicSendTaskABC
    :members:

.. autoclass:: LimitedDurationCyclicSendTaskABC
    :members:

.. autoclass:: MultiRateCyclicSendTaskABC
    :members:

.. autoclass:: can.ModifiableCyclicTaskABC
    :members:

.. autoclass:: can.RestartableCyclicTaskABC
    :members:


Functional API
--------------

.. warning::
    The functional API in :func:`can.broadcastmanager.send_periodic` is now deprecated
    and will be removed in version 2.3.
    Use the object oriented API via :meth:`can.BusABC.send_periodic` instead.

.. autofunction:: can.broadcastmanager.send_periodic
