DG Interface
================

Interface to `DG Technologies <http://dgtech.com>`__ Beacon


Bus
---

.. autoclass:: can.interfaces.dg.dg.dgBus


Configuration
-------------
There are 6 parameters accepted by the ``dgBus`` class::

    [default]
    chan = 1
    mode = "CAN"
    ip = "localhost"
    bitrate = 500000
    termination = True
    databitr = 2000000

``chan (int)`` is the channel the bus will be initialized on

``mode (string)`` is either ``"CAN"``, ``"CANFD"``, or ``"CANPREISO"``

``ip (string)`` is the ip address that the beacon is running on

``bitrate (int/long)`` is the bitrate

``termination (bool)`` is either ``True`` (on) or ``False`` (off)

``databitr (int/long)`` is the data bitrate and is only used if ``mode`` is ``"CANFD"`` or ``"CANPREISO"``

Capability
-------------
The ``dgBus`` class implements several python-can methods::

    send, send_periodic, recv, set_filters, flush_tx_buffer, _detect_available_configs, shutdown

The ``Scheduling`` class supports both ``Limited Duration Tasks`` and ``Modifiable Tasks``
