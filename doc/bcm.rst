.. _bcm:

Broadcast Manager
=================

.. module:: can.broadcastmanager

The broadcast manager allows the user to setup periodic message jobs.
For example sending a particular message at a given period. The broadcast
manager supported natively by several interfaces and a software thread
based scheduler is used as a fallback.

This example shows the socketcan backend using the broadcast manager:

.. literalinclude:: ../examples/cyclic.py
    :language: python
    :linenos:


Message Sending Tasks
~~~~~~~~~~~~~~~~~~~~~

The class based api for the broadcast manager uses a series of
`mixin classes <https://www.ianlewis.org/en/mixins-and-python>`_.
All mixins inherit from :class:`~can.broadcastmanager.CyclicSendTaskABC`
which inherits from :class:`~can.broadcastmanager.CyclicTask`.

.. autoclass:: can.broadcastmanager.CyclicTask
    :members:

.. autoclass:: can.broadcastmanager.CyclicSendTaskABC
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
    and will be removed in version 4.0.
    Use the object oriented API via :meth:`can.BusABC.send_periodic` instead.

.. autofunction:: can.broadcastmanager.send_periodic
