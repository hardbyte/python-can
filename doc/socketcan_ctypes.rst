.. _sockdoc:

SocketCAN ctypes wrapper
========================

socketcanlib is a ctypes wrapper class around libc. It contains replications
of constants and structures found in various linux header files. With 
Python 3.3, much of the functionaity of this library is likely to be 
in the python socket module.

Bus
---

.. autoclass:: can.interfaces.socketcan_ctypes.Bus


Internals
---------

createSocket
~~~~~~~~~~~~

.. autofunction:: can.interfaces.socketcan_ctypes.createSocket


bindSocket
~~~~~~~~~~

.. autofunction:: can.interfaces.socketcan_ctypes.bindSocket


capturePacket
~~~~~~~~~~~~~

.. autofunction:: can.interfaces.socketcan_ctypes.capturePacket
