.. _can.bus:

Bus
---

The :class:`~can.Bus` class, as the name suggests, provides an abstraction of a CAN bus.
The bus provides a wrapper around a physical or virtual CAN Bus. Where the interface
supports it, message filtering is carried out for each bus.


API
''''

.. autoclass:: can.BusABC
    :members:


Transmitting
''''''''''''

Writing to the bus is done by calling the :meth:`~can.Bus.send` method and
passing a :class:`~can.Message` object.

Receiving
'''''''''

Reading from the bus is achieved by either calling the :meth:`~can.BusABC.recv` method or
by directly iterating over the bus::

    for msg in bus:
        print(msg.data)

Alternatively the :class:`~can.Listener` api can be used, which is a list of :class:`~can.Listener`
subclasses that receive notifications when new messages arrive.
