Library API
===========

The main objects are the :class:`~can.BusABC` and the :class:`~can.Message`.
A form of CAN interface is also required.

.. hint::

    Check the backend specific documentation for any implementation specific details.


.. toctree::
   :maxdepth: 1
   
   bus
   message
   listeners
   bcm



Utilities
---------

.. automodule:: can.util
    :members:


.. _notifier:
   
Notifier
--------

The Notifier object is used as a message distributor for a bus.

.. autoclass:: can.Notifier
    :members:

