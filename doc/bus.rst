.. _bus:

Bus
---

The :class:`~can.BusABC` class, as the name suggests, provides an abstraction of a CAN bus.
The bus provides a wrapper around a physical or virtual CAN Bus.
An interface specific instance of the :class:`~can.BusABC` is created by the :class:`~can.Bus`
class, for example::

    vector_bus = can.Bus(interface='vector', ...)

That bus is then able to handle the interface specific software/hardware interactions
and implements the :class:`~can.BusABC` API.

A thread safe bus wrapper is also available, see `Thread safe bus`_.

Autoconfig Bus
''''''''''''''

.. autoclass:: can.Bus
    :members:
    :undoc-members:


API
'''

.. autoclass:: can.BusABC
    :members:
    :undoc-members:

    .. automethod:: __iter__

Transmitting
''''''''''''

Writing individual messages to the bus is done by calling the :meth:`~can.BusABC.send` method
and passing a :class:`~can.Message` instance. Periodic sending is controlled by the
:ref:`broadcast manager <bcm>`.


Receiving
'''''''''

Reading from the bus is achieved by either calling the :meth:`~can.BusABC.recv` method or
by directly iterating over the bus::

    for msg in bus:
        print(msg.data)

Alternatively the :class:`~can.Listener` api can be used, which is a list of :class:`~can.Listener`
subclasses that receive notifications when new messages arrive.


Filtering
'''''''''

Message filtering can be set up for each bus. Where the interface supports it, this is carried
out in the hardware or kernel layer - not in Python.


Thread safe bus
---------------

This thread safe version of the :class:`~can.BusABC` class can be used by multiple threads at once.
Sending and receiving is locked separately to avoid unnecessary delays.
Conflicting calls are executed by blocking until the bus is accessible.

It can be used exactly like the normal :class:`~can.BusABC`:

    # 'socketcan' is only an example interface, it works with all the others too
    my_bus = can.ThreadSafeBus(interface='socketcan', channel='vcan0')
    my_bus.send(...)
    my_bus.recv(...)

.. autoclass:: can.ThreadSafeBus
    :members:
