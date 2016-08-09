Virtual
=======

The virtual interface can be used as a way to write OS and driver independent
tests.

Bus instances connecting to the same channel will share the same messages.


.. code-block:: python
    
    import can

    bus1 = can.interface.Bus('test', bustype='virtual')
    bus2 = can.interface.Bus('test', bustype='virtual')

    msg1 = can.Message(arbitration_id=0xabcde, data=[1,2,3])
    bus1.send(msg1)
    msg2 = bus2.recv()

    assert msg1 == msg2
