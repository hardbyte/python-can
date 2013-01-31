SocketCAN in Native Python
==========================

Python 3.3 added support for socketcan for linux systems.

The socketcan_native interface directly uses Python's socket module to 
access SocketCAN on linux. This is the most direct route to the kernel
and should provide the most responsive.

Python 3.4 added support for the Broadcast Connection Manager (BCM)
protocol, whch if enabled should be used for queing periodic tasks. 


Bus
---

.. autoclass:: can.interfaces.socketcan_native.Bus


createSocket
-------------

.. autofunction:: can.interfaces.socketcan_native.createSocket


bindSocket
-----------

.. autofunction:: can.interfaces.socketcan_native.bindSocket


capturePacket
--------------

.. autofunction:: can.interfaces.socketcan_native.capturePacket
