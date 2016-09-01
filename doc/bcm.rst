
Broadcast Manager
=================

The broadcast manager isn't yet supported by all interfaces. It allows the user
to setup periodic message jobs.

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
