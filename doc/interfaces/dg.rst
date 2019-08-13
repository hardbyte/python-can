DG Interface
================

Interface to `DG Technologies <http://dgtech.com>`__ Beacon


Bus
---

.. autoclass:: can.interfaces.dg.dg.DGBus


Capability
-------------
The ``DGBus`` class implements several python-can methods::

    send, send_periodic, recv, set_filters, flush_tx_buffer, _detect_available_configs, shutdown

The ``Scheduling`` class supports both ``Limited Duration Tasks`` and ``Modifiable Tasks``

The Bus also implements several Bus-Specific methods::

    set_mode, set_bitrate, set_databitr, set_event_rx
