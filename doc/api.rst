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
   asyncio
   bcm
   bit_timing
   internal-api


Utilities
---------


.. autofunction:: can.detect_available_configs


.. _notifier:

Notifier
--------

The Notifier object is used as a message distributor for a bus. Notifier creates a thread to read messages from the bus and distributes them to listeners.

.. autoclass:: can.Notifier
    :members:


.. _errors:

Errors
------

.. automodule:: can.exceptions
    :members:
    :show-inheritance:
