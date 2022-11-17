.. _udp_multicast_doc:

Multicast IP Interface
======================

This module implements transport of CAN and CAN FD messages over UDP via Multicast IPv4 and IPv6.
This virtual interface allows for communication between multiple processes and even hosts.
This differentiates it from the :ref:`virtual_interface_doc` interface,
which can only passes messages within a single process but does not require a network stack.

It runs on UDP to have the lowest possible latency (as opposed to using TCP), and because
normal IP multicast is inherently unreliable, as the recipients are unknown.
This enables ad-hoc networks that do not require a central server but is also a so-called
*unreliable network*. In practice however, local area networks (LANs) should most often be
sufficiently reliable for this interface to function properly.

.. note::
    For an overview over the different virtual buses in this library and beyond, please refer
    to the section :ref:`virtual_interfaces_doc`. It also describes important limitations
    of this interface.

Please refer to the `Bus class documentation`_ below for configuration options and useful resources
for specifying multicast IP addresses.

Supported Platforms
-------------------

It should work on most Unix systems (including Linux with kernel 2.6.22+ and macOS) but currently not on Windows.

Example
-------

This example should print a single line indicating that a CAN message was successfully sent
from ``bus_1`` to ``bus_2``:

.. code-block:: python

        import time
        import can
        from can.interfaces.udp_multicast import UdpMulticastBus

        # The bus can be created using the can.Bus wrapper class or using UdpMulticastBus directly
        with can.Bus(channel=UdpMulticastBus.DEFAULT_GROUP_IPv6, bustype='udp_multicast') as bus_1, \
                UdpMulticastBus(channel=UdpMulticastBus.DEFAULT_GROUP_IPv6) as bus_2:

            # register a callback on the second bus that prints messages to the standard out
            notifier = can.Notifier(bus_2, [can.Printer()])

            # create and send a message with the first bus, which should arrive at the second one
            message = can.Message(arbitration_id=0x123, data=[1, 2, 3])
            bus_1.send(message)

            # give the notifier enough time to get triggered by the second bus
            time.sleep(2.0)


Bus Class Documentation
-----------------------

.. autoclass:: can.interfaces.udp_multicast.UdpMulticastBus
    :members:
    :exclude-members: send
