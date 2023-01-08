CANalyst-II
===========

CANalyst-II is a USB to CAN Analyzer device produced by Chuangxin Technology.

Install: ``pip install "python-can[canalystii]"``

Supported platform
------------------

Windows, Linux and Mac.

.. note::

   The backend driver depends on `pyusb <https://pyusb.github.io/pyusb/>`_ so a ``pyusb`` backend driver library such as ``libusb`` must be installed. On Windows a tool such as `Zadig <https://zadig.akeo.ie/>`_ can be used to set the Canalyst-II USB device driver to ``libusb-win32``.

Limitations
-----------

Multiple Channels
^^^^^^^^^^^^^^^^^

The USB protocol transfers messages grouped by channel. Messages received on channel 0 and channel 1 may be returned by software out of order between the two channels (although inside each channel, all messages are in order). The timestamp field of each message comes from the hardware and shows the exact time each message was received. To compare ordering of messages on channel 0 vs channel 1, sort the received messages by the timestamp field first.

Backend Driver
--------------

The backend driver module `canalystii <https://pypi.org/project/canalystii>` must be installed to use this interface. This open source driver is unofficial and based on reverse engineering. Earlier versions of python-can required a binary library from the vendor for this functionality.

Bus
---

.. autoclass:: can.interfaces.canalystii.CANalystIIBus

