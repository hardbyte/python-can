Remote
======

The remote interface works as a networked bridge between the computer running
the application and the computer owning the physical CAN interface.

Server
------

The computer which owns the CAN interface must start a server which accepts
incoming connections. If more than one channel is to be shared, multiple
servers must be started on different ports.

Start a server using default interface and channel::

    $ can_server.py

Specify interface, channel and port number explicitly::

    $ can_server.py --interface kvaser --channel 0 --port 54702

Client
------

The application must specify ``remote`` as interface and ``host:port`` as
channel. The port number can be omitted if default port is used. The bitrate
to use on the CAN bus can also be specified.

.. code-block:: python

    bus = can.interface.Bus('192.168.0.10:54701',
                            bustype='remote',
                            bitrate=500000,
                            can_filters=[
                                {'can_id': 0x11},
                                {'can_mask': 0xff}
                            ])


Alternatively in a .canrc file::

    [default]
    interface = remote
    channel = myhostname

Internals
---------

The client uses a standard Bus class to connect to the server.

.. autoclass:: can.interfaces.remote.RemoteBus
.. autoexception:: can.interfaces.remote.CanRemoteError

The server uses the following classes to implement the connections.

.. autoclass:: can.interfaces.remote.RemoteServer

   .. method:: serve_forever

      Start listening for incoming connections.

   .. method:: shutdown

      Stop the server.


.. autoclass:: can.interfaces.remote.server.ClientBusConnection

Protocol
~~~~~~~~

The protocol is a stream of events over a network socket.
Each event starts with one byte that represents the event id, followed by
event specific data of arbitrary length in big-endian byte order.

The client start with sending a :class:`can.interfaces.remote.events.BusRequest`
followed by a :class:`can.interfaces.remote.events.FilterConfig`.
The server will reply with a :class:`can.interfaces.remote.events.BusResponse`.

Each event class inherits from the base event class:

.. autoclass:: can.interfaces.remote.events.BaseEvent

The available events that can occurr and their specification is listed below:

.. autoclass:: can.interfaces.remote.events.BusRequest
.. autoclass:: can.interfaces.remote.events.BusResponse
.. autoclass:: can.interfaces.remote.events.CanMessage
.. autoclass:: can.interfaces.remote.events.TransmitSuccess
.. autoclass:: can.interfaces.remote.events.TransmitFail
.. autoclass:: can.interfaces.remote.events.RemoteException
.. autoclass:: can.interfaces.remote.events.PeriodicMessageStart
.. autoclass:: can.interfaces.remote.events.FilterConfig
.. autoclass:: can.interfaces.remote.events.ConnectionClosed
