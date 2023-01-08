
.. _virtual_interfaces_doc:

Virtual Interfaces
==================

There are quite a few implementations for CAN networks that do not require physical
CAN hardware. The built in virtual interfaces are:

.. toctree::
   :maxdepth: 1

   interfaces/virtual
   interfaces/udp_multicast


Comparison
----------

The following table compares some known virtual interfaces:

+----------------------------------------------------+-----------------------------------------------------------------------+---------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------+
| **Name**                                           | **Availability**                                                      |           **Applicability**           |                                                           **Implementation**                                                           |
|                                                    |                                                                       +-----------+-------------+-------------+--------------------+---------------------------------------------+---------------------------------------------------------------------+
|                                                    |                                                                       | **Within  | **Between   | **Via (IP)  | **Without Central  | **Transport                                 | **Serialization                                                     |
|                                                    |                                                                       | Process** | Processes** | Networks**  | Server**           | Technology**                                | Format**                                                            |
+----------------------------------------------------+-----------------------------------------------------------------------+-----------+-------------+-------------+--------------------+---------------------------------------------+---------------------------------------------------------------------+
| ``virtual`` (this)                                 | *included*                                                            | ✓         | ✗           | ✗           | ✓                  | Singleton & Mutex                           | none                                                                |
|                                                    |                                                                       |           |             |             |                    | (reliable)                                  |                                                                     |
+----------------------------------------------------+-----------------------------------------------------------------------+-----------+-------------+-------------+--------------------+---------------------------------------------+---------------------------------------------------------------------+
| ``udp_multicast`` (:ref:`doc <udp_multicast_doc>`) | *included*                                                            | ✓         | ✓           | ✓           | ✓                  | UDP via IP multicast                        | custom using `msgpack <https://pypi.org/project/msgpack-python/>`__ |
|                                                    |                                                                       |           |             |             |                    | (unreliable)                                |                                                                     |
+----------------------------------------------------+-----------------------------------------------------------------------+-----------+-------------+-------------+--------------------+---------------------------------------------+---------------------------------------------------------------------+
| *christiansandberg/                                | `external <https://github.com/christiansandberg/python-can-remote>`__ | ✓         | ✓           | ✓           | ✗                  | Websockets via TCP/IP                       | custom binary                                                       |
| python-can-remote*                                 |                                                                       |           |             |             |                    | (reliable)                                  |                                                                     |
+----------------------------------------------------+-----------------------------------------------------------------------+-----------+-------------+-------------+--------------------+---------------------------------------------+---------------------------------------------------------------------+
| *windelbouwman/                                    | `external <https://github.com/windelbouwman/virtualcan>`__            | ✓         | ✓           | ✓           | ✗                  | `ZeroMQ <https://zeromq.org/>`__ via TCP/IP | custom binary [#f1]_                                                |
| virtualcan*                                        |                                                                       |           |             |             |                    | (reliable)                                  |                                                                     |
+----------------------------------------------------+-----------------------------------------------------------------------+-----------+-------------+-------------+--------------------+---------------------------------------------+---------------------------------------------------------------------+

.. [#f1]
    The only option in this list that implements interoperability with other languages
    out of the box. For the others (except the first intra-process one), other programs written
    in potentially different languages could effortlessly interface with the bus
    once they mimic the serialization format. The last one, however, has already implemented
    the entire bus functionality in  *C++* and *Rust*, besides the Python variant.

Common Limitations
------------------

**Guaranteed delivery** and **message ordering** is one major point of difference:
While in a physical CAN network, a message is either sent or in queue (or an explicit error occurred),
this may not be the case for virtual networks.
The ``udp_multicast`` bus for example, drops this property for the benefit of lower
latencies by using unreliable UDP/IP instead of reliable TCP/IP (and because normal IP multicast
is inherently unreliable, as the recipients are unknown by design). The other three buses faithfully
model a physical CAN network in this regard: They ensure that all recipients actually receive
(and acknowledge each message), much like in a physical CAN network. They also ensure that
messages are relayed in the order they have arrived at the central server and that messages
arrive at the recipients exactly once. Both is not guaranteed to hold for the best-effort
``udp_multicast`` bus as it uses UDP/IP as a transport layer.

**Central servers** are, however, required by interfaces 3 and 4 (the external tools) to provide
these guarantees of message delivery and message ordering. The central servers receive and distribute
the CAN messages to all other bus participants, unlike in a real physical CAN network.
The first intra-process ``virtual`` interface only runs within one Python process, effectively the
Python instance of :class:`~can.interfaces.virtual.VirtualBus` acts as a central server.
Notably the ``udp_multicast`` bus does not require a central server.

**Arbitration and throughput** are two interrelated functions/properties of CAN networks which
are typically abstracted in virtual interfaces. In all four interfaces, an unlimited amount
of messages can be sent per unit of time (given the computational power of the machines and
networks that are involved). In a real CAN/CAN FD networks, however, throughput is usually much
more restricted and prioritization of arbitration IDs is thus an important feature once the bus
is starting to get saturated. None of the interfaces presented above support any sort of throttling
or ID arbitration under high loads.

