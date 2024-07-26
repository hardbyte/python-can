USR-CANET
===========

USR-CANET200 is an Ethernet to CANbus and RS485 converter manufactured by PUSR. This device features 2 CANbus ports with TCP/UDP server or client to relay CANbus over Ethernet. The interface
uses TCP server mode and need to be configured on the web management portal.

The device's official documentation and transparent transmission protocol information can be found `here <https://www.pusr.com/download/CANET/USR-CANET200-User-Manual_V1.0.4.01.pdf>`

Install: ``pip install "python-can[usr_canet]"``

Supported platform
------------------

Windows, Linux and Mac.

Limitations
-----------

This interface has a simplified implementation of timeout and may not work well in high capacity multi-threaded applications.


Bus
---

.. autoclass:: can.interfaces.usr_canet.UsrCanetBus

