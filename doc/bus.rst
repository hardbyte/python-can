Bus
---

The :class:`~can.Bus` class, as the name suggests, provides an abstraction of a CAN bus.
The bus can provide a wrapper around a physical CAN Bus using a Kvaser, or
it can wrap a virtual CAN Bus.

Transmitting
''''''''''''

Writing to the bus is done by calling the :meth:`~can.Bus.send` method and
passing a :class:`~can.Message` object.

Receiving
'''''''''

Reading from the bus is achieved by either calling the :meth:`~can.Bus.recv` method or
by directly iterating over the bus::

    for msg in bus:
        print(msg.data)

Alternatively the :class:`~can.Listener` api can be used, which is a list of :class:`~can.Listener`
subclasses that receive notifications when new messages arrive.

API
''''

.. autoclass:: can.bus.BusABC
    :members:

