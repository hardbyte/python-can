.. _virtual_interface_doc:

Virtual
=======

The virtual interface can be used as a way to write OS and driver independent tests.
Any `VirtualBus` instances connecting to the same channel (from within the same Python
process) will receive each others messages.

If messages shall be sent across process or host borders, consider using the
:ref:`udp_multicast_doc` and refer to :ref:`virtual_interfaces_doc`
for a comparison and general discussion of different virtual interfaces.

Example
-------

.. code-block:: python

    import can

    bus1 = can.interface.Bus('test', bustype='virtual')
    bus2 = can.interface.Bus('test', bustype='virtual')

    msg1 = can.Message(arbitration_id=0xabcde, data=[1,2,3])
    bus1.send(msg1)
    msg2 = bus2.recv()

    #assert msg1 == msg2
    assert msg1.arbitration_id == msg2.arbitration_id
    assert msg1.data == msg2.data
    assert msg1.timestamp != msg2.timestamp

.. code-block:: python

    import can

    bus1 = can.interface.Bus('test', bustype='virtual', preserve_timestamps=True)
    bus2 = can.interface.Bus('test', bustype='virtual')

    msg1 = can.Message(timestamp=1639740470.051948, arbitration_id=0xabcde, data=[1,2,3])

    # Messages sent on bus1 will have their timestamps preserved when received
    # on bus2
    bus1.send(msg1)
    msg2 = bus2.recv()

    assert msg1.arbitration_id == msg2.arbitration_id
    assert msg1.data == msg2.data
    assert msg1.timestamp == msg2.timestamp

    # Messages sent on bus2 will not have their timestamps preserved when
    # received on bus1
    bus2.send(msg1)
    msg3 = bus1.recv()

    assert msg1.arbitration_id == msg3.arbitration_id
    assert msg1.data == msg3.data
    assert msg1.timestamp != msg3.timestamp


Bus Class Documentation
-----------------------

.. autoclass:: can.interfaces.virtual.VirtualBus
    :members:

    .. automethod:: _detect_available_configs
