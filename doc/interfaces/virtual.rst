.. _virtual_interface_doc:

Virtual
=======

The virtual interface can be used as a way to write OS and driver independent tests.
Any `VirtualBus` instances connecting to the same channel (from within the same Python
process) will get each others messages.

If messages shall be sent across process or host borders, consider using the
:ref:`multicast_ip_doc` and refer to the next section for a comparison of different
virtual interfaces. That section also describes common limitations of current virtual interfaces.

.. _other_virtual_interfaces:

Other Virtual Interfaces
------------------------

There are quite a few implementations for CAN networks that do not require physical
CAN hardware.

Comparison
''''''''''

The following table compares common virtual interfaces:

+--------------------------------------------------+-----------------------------------------------------------------------+---------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------+
| **Name**                                         | **Availability**                                                      |           **Applicability**           |                                                            **Implementation**                                                           |
|                                                  |                                                                       +-----------+-------------+-------------+---------------------+---------------------------------------------+---------------------------------------------------------------------+
|                                                  |                                                                       | **Within  | **Between   | **Via (IP)  | **Requires Central  | **Transport                                 | **Serialization                                                     |
|                                                  |                                                                       | Process** | Processes** | Networks**  | Server**            | Technology**                                | Format**                                                            |
+--------------------------------------------------+-----------------------------------------------------------------------+-----------+-------------+-------------+---------------------+---------------------------------------------+---------------------------------------------------------------------+
| ``virtual`` (this)                               | *included*                                                            | ✓         | ✗           | ✗           | ✗                   | Singleton & Mutex                           | none                                                                |
+--------------------------------------------------+-----------------------------------------------------------------------+-----------+-------------+-------------+---------------------+---------------------------------------------+---------------------------------------------------------------------+
| ``multicast_ip`` (:ref:`doc <multicast_ip_doc>`) | *included*                                                            | ✓         | ✓           | ✓           | ✗                   | UDP via IP multicast                        | custom using `msgpack <https://pypi.org/project/msgpack-python/>`__ |
+--------------------------------------------------+-----------------------------------------------------------------------+-----------+-------------+-------------+---------------------+---------------------------------------------+---------------------------------------------------------------------+
| *christiansandberg/                              | `external <https://github.com/christiansandberg/python-can-remote>`__ | ✓         | ✓           | ✓           | ✓                   | Websockets via TCP/IP                       | custom binary                                                       |
| python-can-remote*                               |                                                                       |           |             |             |                     |                                             |                                                                     |
+--------------------------------------------------+-----------------------------------------------------------------------+-----------+-------------+-------------+---------------------+---------------------------------------------+---------------------------------------------------------------------+
| *windelbouwman/                                  | `external <https://github.com/windelbouwman/virtualcan>`__            | ✓         | ✓           | ✓           | ✓                   | `ZeroMQ <https://zeromq.org/>`__ via TCP/IP | custom binary [#f1]_                                                |
| virtualcan*                                      |                                                                       |           |             |             |                     |                                             |                                                                     |
+--------------------------------------------------+-----------------------------------------------------------------------+-----------+-------------+-------------+---------------------+---------------------------------------------+---------------------------------------------------------------------+

.. [#f1] As the only option in this list, this implements interoperability with other languages out of the box.

Common Limitations
''''''''''''''''''

TODO

Example
-------

.. code-block:: python
    
    import can

    bus1 = can.interface.Bus('test', bustype='virtual')
    bus2 = can.interface.Bus('test', bustype='virtual')

    msg1 = can.Message(arbitration_id=0xabcde, data=[1,2,3])
    bus1.send(msg1)
    msg2 = bus2.recv()

    assert msg1 == msg2


Bus Class Documentation
-----------------------

.. autoclass:: can.interfaces.virtual.VirtualBus
    :members:
