.. _bus:

Bus
---

The :class:`~can.Bus` provides a wrapper around a physical or virtual CAN Bus.

An interface specific instance is created by instantiating the :class:`~can.Bus`
class with a particular ``interface``, for example::

    vector_bus = can.Bus(interface='vector', ...)

The created bus is then able to handle the interface specific software/hardware interactions
while giving the user the same top level API.

A thread safe bus wrapper is also available, see `Thread safe bus`_.


Transmitting
''''''''''''

Writing individual messages to the bus is done by calling the :meth:`~can.BusABC.send` method
and passing a :class:`~can.Message` instance.

.. code-block:: python
   :emphasize-lines: 8

   with can.Bus() as bus:
       msg = can.Message(
           arbitration_id=0xC0FFEE,
           data=[0, 25, 0, 1, 3, 1, 4, 1],
           is_extended_id=True
       )
       try:
           bus.send(msg)
           print(f"Message sent on {bus.channel_info}")
       except can.CanError:
           print("Message NOT sent")


Periodic sending is controlled by the :ref:`broadcast manager <bcm>`.

Receiving
'''''''''

Reading from the bus is achieved by either calling the :meth:`~can.BusABC.recv` method or
by directly iterating over the bus::

    with can.Bus() as bus:
        for msg in bus:
            print(msg.data)

Alternatively the :ref:`listeners_doc` api can be used, which is a list of various
:class:`~can.Listener` implementations that receive and handle messages from a :class:`~can.Notifier`.


Filtering
'''''''''

Message filtering can be set up for each bus. Where the interface supports it, this is carried
out in the hardware or kernel layer - not in Python. All messages that match at least one filter
are returned.

Example defining two filters, one to pass 11-bit ID ``0x451``, the other to pass 29-bit ID ``0xA0000``:

.. code-block:: python

    filters = [
        {"can_id": 0x451, "can_mask": 0x7FF, "extended": False},
        {"can_id": 0xA0000, "can_mask": 0x1FFFFFFF, "extended": True},
    ]
    bus = can.interface.Bus(channel="can0", bustype="socketcan", can_filters=filters)


See :meth:`~can.BusABC.set_filters` for the implementation.

Bus API
'''''''

.. autoclass:: can.Bus
    :class-doc-from: class
    :show-inheritance:
    :members:
    :inherited-members:

.. autoclass:: can.bus.BusState
    :members:
    :undoc-members:


Thread safe bus
'''''''''''''''

This thread safe version of the :class:`~can.BusABC` class can be used by multiple threads at once.
Sending and receiving is locked separately to avoid unnecessary delays.
Conflicting calls are executed by blocking until the bus is accessible.

It can be used exactly like the normal :class:`~can.BusABC`:

.. code-block:: python

    # 'socketcan' is only an example interface, it works with all the others too
    my_bus = can.ThreadSafeBus(interface='socketcan', channel='vcan0')
    my_bus.send(...)
    my_bus.recv(...)

.. autoclass:: can.ThreadSafeBus
    :members:
