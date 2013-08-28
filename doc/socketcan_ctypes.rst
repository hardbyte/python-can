SocketCAN ctypes wrapper
========================

`socketcan_ctypes.py` is a ctypes wrapper class around libc. It contains replications
of constants and structures found in various linux header files. With 
Python 3.3, much of the functionality of this library is likely to be
available natively in the Python socket module.


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
