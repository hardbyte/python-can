SocketCAN (python)
==================

Python 3.3 added support for socketcan for linux systems.

The ``socketcan_native`` interface directly uses Python's socket module to
access SocketCAN on linux. This is the most direct route to the kernel
and should provide the most responsive one.

The implementation features efficient filtering of can_id's. That filtering
occurs in the kernel and is much much more efficient than filtering messages
in Python.

Python 3.4 added support for the Broadcast Connection Manager (BCM)
protocol, which - if enabled - should be used for queueing periodic tasks.

Documentation for the socketcan back end file can be found:

https://www.kernel.org/doc/Documentation/networking/can.txt


Bus
---

.. autoclass:: can.interfaces.socketcan.SocketcanNative_Bus


Internals
---------

create_socket
~~~~~~~~~~~~~

.. autofunction:: can.interfaces.socketcan.socketcan_native.create_socket


bind_socket
~~~~~~~~~~~

.. autofunction:: can.interfaces.socketcan.socketcan_native.bind_socket


capture_message
~~~~~~~~~~~~~~~

.. autofunction:: can.interfaces.socketcan.socketcan_native.capture_message
