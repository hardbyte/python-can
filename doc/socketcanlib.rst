.. _sockdoc:

Documentation: socketcanlib.py
=================================

socketcanlib is a ctypes wrapper class around libc. It contains replications
of constants and structures found in various linux header files. With 
Python 3.3, much of the functionaity of this library is likely to be 
in the python socket module.

createSocket
-------------

.. autofunction:: pycanlib.socketcanlib.createSocket

bindSocket
-----------

.. autofunction:: pycanlib.socketcanlib.bindSocket

capturePacket
--------------

.. autofunction:: pycanlib.socketcanlib.capturePacket
