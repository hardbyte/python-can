.. _bus:

Bus
---

The :class:`~can.Bus` class, as the name suggests, provides an abstraction of a CAN bus.
The bus provides an abstract wrapper around a physical or virtual CAN Bus.

A thread safe bus wrapper is also available, see `Thread safe bus`_.


Filtering
'''''''''

Message filtering can be set up for each bus. Where the interface supports it, this is carried
out in the hardware or kernel layer - not in Python.


API
''''

.. autoclass:: can.BusABC
    :members:
    :special-members: __iter__

.. autoclass:: can.interface.Bus
    :members:
    :special-members: __iter__


Transmitting
''''''''''''

Writing to the bus is done by calling the :meth:`~can.BusABC.send()` method and
passing a :class:`~can.Message` object.


Receiving
'''''''''

Reading from the bus is achieved by either calling the :meth:`~can.BusABC.recv` method or
by directly iterating over the bus::

    for msg in bus:
        print(msg.data)

Alternatively the :class:`~can.Listener` api can be used, which is a list of :class:`~can.Listener`
subclasses that receive notifications when new messages arrive.


Thread safe bus
---------------

This thread safe version of the :class:`~can.Bus` class can be used by multiple threads at once.
Sending and receiving is locked seperatly to avoid unnessesary delays.
Conflicting calls are executed by blocking until the bus is accessible.

It can be used exactly like the normal :class:`~can.Bus`:

    # 'socketcan' is only an exemple interface, it works with all the others too
    my_bus = can.ThreadSafeBus(interface='socketcan', channel='vcan0')
    my_bus.send(...)
    my_bus.recv(...)

.. autoclass:: can.ThreadSafeBus
    :members:
