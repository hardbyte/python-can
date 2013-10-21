Library API
===========

The main objects are the :class:`~can.Bus` and the :class:`~can.Message`.
A form of CAN interface is also required.


.. toctree::
   :maxdepth: 2
   
   bus
   message
   listeners
   bcm


.. _notifier:
   
Notifier
--------

The Notifier object is used as a message distributor for a bus.

.. autoclass:: can.Notifier
    :members:

