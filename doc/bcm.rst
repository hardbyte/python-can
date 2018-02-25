
Broadcast Manager
=================

.. module:: can.broadcastmanager


The broadcast manager isn't yet supported by all interfaces.
Currently SocketCAN and IXXAT are supported at least partially.
It allows the user to setup periodic message jobs.

If periodic transmission is not supported natively, a software thread based
scheduler is used as a fallback.

This example shows the ctypes socketcan using the broadcast manager:


.. literalinclude:: ../examples/cyclic.py
    :language: python
    :linenos:


Functional API
--------------

.. autofunction:: can.send_periodic


Class based API
---------------


.. autoclass:: can.broadcastmanager.CyclicTask
    :members:


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


.. autoclass:: can.MultiRateCyclicSendTaskABC
    :members:


.. autoclass:: can.RestartableCyclicTaskABC
    :members:
