
Broadcast Manager
=================

The broadcast manager isn't yet supported by all interfaces.
Currently SockerCAN and IXXAT are supported at least partially.
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

.. autoclass:: can.CyclicSendTaskABC
    :members:


.. autoclass:: can.MultiRateCyclicSendTaskABC
    :members:
