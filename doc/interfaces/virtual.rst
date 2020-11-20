.. _virtual_interface_doc:

Virtual
=======

The virtual interface can be used as a way to write OS and driver independent tests.
Any `VirtualBus` instances connecting to the same channel (from within the same Python
process) will get each others messages.
If messages shall be sent across process or host borders, consider using the :ref:`multicast_ip_doc`.


.. code-block:: python
    
    import can

    bus1 = can.interface.Bus('test', bustype='virtual')
    bus2 = can.interface.Bus('test', bustype='virtual')

    msg1 = can.Message(arbitration_id=0xabcde, data=[1,2,3])
    bus1.send(msg1)
    msg2 = bus2.recv()

    assert msg1 == msg2


Bus class documentation
-----------------------

.. autoclass:: can.interfaces.virtual.VirtualBus
    :members:
