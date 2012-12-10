SocketCAN in Native Python
==========================

Python 3.3 added support for socketcan for linux systems.

The socketcan_native interface directly uses Python's socket module to 
access SocketCAN on linux.

createSocket
-------------

.. autofunction:: can.interfaces.socketcan_native.createSocket


bindSocket
-----------

.. autofunction:: can.interfaces.socketcan_native.bindSocket


capturePacket
--------------

.. autofunction:: can.interfaces.socketcan_native.capturePacket
