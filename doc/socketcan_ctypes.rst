SocketCAN (ctypes)
==================

`socketcan_ctypes.py` is a ctypes wrapper class around libc. It contains replications
of constants and structures found in various linux header files. With 
Python 3.3, much of the functionality of this library is likely to be
available natively in the Python socket module.



Bus
----

.. autoclass:: can.interfaces.socketcan_ctypes.Bus



Broadcast-Manager
-----------------

The ``socketcan_ctypes`` interface implements thin wrappers to the linux `broadcast manager`
socket api. This allows the cyclic transmission of CAN messages at given intervals.
The overhead for periodic message sending is extremely low as all the heavy lifting occurs
within the linux kernel.

send_periodic()
~~~~~~~~~~~~~~~

An example that uses the send_periodic is included in ``python-can/examples/cyclic.py``

The object returned can be used to halt, alter or cancel the periodic message task.

.. autoclass:: can.interfaces.socketcan_ctypes.CyclicSendTask


Internals
---------

createSocket
~~~~~~~~~~~~

.. autofunction:: can.interfaces.socketcan_ctypes.createSocket


bindSocket
~~~~~~~~~~

.. autofunction:: can.interfaces.socketcan_ctypes.bindSocket

connectSocket

.. autofunction:: can.interfaces.socketcan_ctypes.connectSocket

capturePacket
~~~~~~~~~~~~~

.. autofunction:: can.interfaces.socketcan_ctypes.capturePacket
