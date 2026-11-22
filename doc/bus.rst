.. _bus:

Bus
---

The :class:`~can.BusABC` class provides a wrapper around a physical or virtual CAN Bus.

An interface specific instance is created by calling the :func:`~can.Bus`
function with a particular ``interface``, for example::

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
    bus = can.interface.Bus(channel="can0", interface="socketcan", can_filters=filters)


See :meth:`~can.BusABC.set_filters` for the implementation.

.. _listen_only:

Listen-only mode
''''''''''''''''

A bus opened with ``listen_only=True`` only receives: it never puts frames,
acknowledgements or error frames on the wire, which makes it safe for passively
logging a live bus. Calling :meth:`~can.BusABC.send` on such a bus raises
:class:`~can.exceptions.CanOperationError`.

Listen-only mode corresponds to the bus monitoring mode of ISO 11898-1 (§10.14):
the node receives frames but never drives the bus dominant, so it sends no
acknowledgements, error flags or overload flags. It is not the restricted
operation mode (§10.15), which still acknowledges frames.

.. code-block:: python

    with can.Bus(interface="vector", channel=0, listen_only=True) as bus:
        for msg in bus:
            print(msg)

Listen-only mode is selected when the bus is created. It can also be set
in a :ref:`configuration file <configuration>` with ``listen_only = True``, and the
command line tools accept ``--listen-only``.

The :attr:`~can.BusABC.listen_only` property tells whether a bus is in listen-only
mode. Interfaces that can switch the mode at runtime, currently ``pcan`` and
``systec``, also allow setting it.

An interface supports listen-only mode only if its constructor declares a
``listen_only`` parameter, or forwards ``**kwargs`` to a base class constructor
that does. For any other interface, ``listen_only=True`` raises
:class:`~can.exceptions.CanInterfaceNotImplementedError` before the bus is
created, see :class:`~can.BusABC`. Of the built-in interfaces, ``cantact``,
``kvaser``, ``nixnet``, ``pcan``, ``seeedstudio``, ``slcan``, ``systec``,
``vector`` and ``virtual`` support it.

.. deprecated:: 4.7.0
    The interface specific ways to request listen-only mode are deprecated in favour
    of ``listen_only``: the ``monitor`` argument of ``cantact``, the ``driver_mode``
    argument of ``kvaser``, the ``"silent"`` and ``"loopback_and_silent"`` operation
    modes of ``seeedstudio``, the ``state`` argument and setting ``bus.state`` for
    ``pcan`` and ``systec``, and the ``--passive`` and ``--active`` arguments of
    ``can.logger``.

Bus API
'''''''

.. autofunction:: can.Bus

.. autoclass:: can.BusABC
    :class-doc-from: class
    :members:
    :inherited-members:

.. autoclass:: can.BusState
    :members:
    :undoc-members:

.. autoclass:: can.bus.CanProtocol
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
