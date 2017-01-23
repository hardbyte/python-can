Remote
======

The remote interface works as a networked bridge between the computer running
the application and the computer owning the physical CAN interface.

Multiple clients may connect to the same server simultaneously. Each client
will create its own bus instance on the server, so this must be supported by the
real interface.

Server
------

The computer which owns the CAN interface must start a server which accepts
incoming connections. If more than one channel is to be shared, multiple
servers must be started on different ports.

Start a server using default interface and channel::

    $ canserver

Specify interface, channel and port number explicitly::

    $ canserver --interface kvaser --channel 0 --port 54702

It can also be started as a module::

    $ python -m can.interfaces.remote


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
    channel = myhostname:54701


The can_logger.py script could be started like this::

    $ can_logger.py -i remote -c myhostname:54701


Internals
---------

The client uses a standard Bus class to connect to the server.

.. autoclass:: can.interfaces.remote.RemoteBus
.. autoexception:: can.interfaces.remote.CanRemoteError

The server uses the following classes to implement the connections.

.. autoclass:: can.interfaces.remote.RemoteServer

   .. method:: serve_forever(poll_interval=0.5)

      Start listening for incoming connections.

   .. method:: shutdown

      Stops the serve_forever loop.

      Blocks until the loop has finished. This must be called while
      serve_forever() is running in another thread, or it will
      deadlock.

   .. method:: server_close

      Clean-up the server.

.. autoclass:: can.interfaces.remote.server.ClientBusConnection

Protocol
~~~~~~~~

The protocol is a stream of events over a TCP socket.
Each event starts with one byte that represents the event id, followed by
event specific data of arbitrary length in big-endian byte order.

The client start with sending a :class:`~can.interfaces.remote.events.BusRequest`
followed by a :class:`~can.interfaces.remote.events.FilterConfig`.
The server will reply with a :class:`~can.interfaces.remote.events.BusResponse`.

Each event class inherits from the base event class:

.. autoclass:: can.interfaces.remote.events.BaseEvent

The available events that can occurr and their specification is listed below:

.. autoclass:: can.interfaces.remote.events.BusRequest
.. autoclass:: can.interfaces.remote.events.BusResponse
.. autoclass:: can.interfaces.remote.events.CanMessage
.. autoclass:: can.interfaces.remote.events.TransmitSuccess
.. autoclass:: can.interfaces.remote.events.RemoteException
.. autoclass:: can.interfaces.remote.events.FilterConfig
.. autoclass:: can.interfaces.remote.events.ConnectionClosed
