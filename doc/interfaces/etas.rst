ETAS
====

This interface adds support for CAN interfaces by `ETAS`_.
The ETAS BOA_ (Basic Open API) is used.

Installation
------------

Install the "ETAS ECU and Bus Interfaces – Distribution Package".

.. warning::
   Only Windows is supported by this interface.

   The Linux kernel v5.13 (and greater) natively supports ETAS ES581.4, ES582.1 and ES584.1
   USB modules. To use these under Linux, please refer to the :ref:`SocketCAN` interface
   documentation.


Configuration
-------------

The simplest configuration file would be::

    [default]
    interface = etas
    channel = ETAS://ETH/ES910:abcd/CAN:1

Channels are the URIs used by the underlying API.

To find available URIs, use :meth:`~can.detect_available_configs`::

    configs = can.interface.detect_available_configs(interfaces="etas")
    for c in configs:
        print(c)


Bus
---

.. autoclass:: can.interfaces.etas.EtasBus
    :members:


.. _ETAS: https://www.etas.com/
.. _BOA: https://www.etas.com/de/downloadcenter/18102.php
