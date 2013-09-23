
Broadcast Manager
=================

The broadcast manager is a work in progress, to date the transmit path has been worked on using
the ctypes socketcan inteface.

This example shows the ctypes socketcan using the broadcast maneger:


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
