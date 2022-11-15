Vector
======

This interface adds support for CAN controllers by `Vector`_. Only Windows is supported.

Configuration
-------------

By default this library uses the channel configuration for CANalyzer.
To use a different application, open **Vector Hardware Configuration** program and create
a new application and assign the channels you may want to use.
Specify the application name as ``app_name='Your app name'`` when constructing
the bus or in a config file.

Channel should be given as a list of channels starting at 0.

Here is an example configuration file connecting to CAN 1 and CAN 2 for an
application named "python-can"::

    [default]
    interface = vector
    channel = 0, 1
    app_name = python-can



VectorBus
---------

.. autoclass:: can.interfaces.vector.VectorBus
   :show-inheritance:
   :member-order: bysource
   :members:
      set_filters,
      recv,
      send,
      send_periodic,
      stop_all_periodic_tasks,
      flush_tx_buffer,
      reset,
      shutdown,
      popup_vector_hw_configuration,
      get_application_config,
      set_application_config

Exceptions
----------

.. autoexception:: can.interfaces.vector.VectorError
   :show-inheritance:
.. autoexception:: can.interfaces.vector.VectorInitializationError
   :show-inheritance:
.. autoexception:: can.interfaces.vector.VectorOperationError
   :show-inheritance:

Miscellaneous
-------------

.. autofunction:: can.interfaces.vector.get_channel_configs

.. autoclass:: can.interfaces.vector.VectorChannelConfig
   :show-inheritance:
   :class-doc-from: class

.. autoclass:: can.interfaces.vector.canlib.VectorBusParams
   :show-inheritance:
   :class-doc-from: class

.. autoclass:: can.interfaces.vector.canlib.VectorCanParams
   :show-inheritance:
   :class-doc-from: class

.. autoclass:: can.interfaces.vector.canlib.VectorCanFdParams
   :show-inheritance:
   :class-doc-from: class

.. autoclass:: can.interfaces.vector.xldefine.XL_HardwareType
   :show-inheritance:
   :member-order: bysource
   :members:
   :undoc-members:

.. autoclass:: can.interfaces.vector.xldefine.XL_ChannelCapabilities
   :show-inheritance:
   :member-order: bysource
   :members:
   :undoc-members:

.. autoclass:: can.interfaces.vector.xldefine.XL_BusCapabilities
   :show-inheritance:
   :member-order: bysource
   :members:
   :undoc-members:

.. autoclass:: can.interfaces.vector.xldefine.XL_BusTypes
   :show-inheritance:
   :member-order: bysource
   :members:
   :undoc-members:

.. autoclass:: can.interfaces.vector.xldefine.XL_OutputMode
   :show-inheritance:
   :member-order: bysource
   :members:
   :undoc-members:

.. autoclass:: can.interfaces.vector.xldefine.XL_CANFD_BusParams_CanOpMode
   :show-inheritance:
   :member-order: bysource
   :members:
   :undoc-members:

.. autoclass:: can.interfaces.vector.xldefine.XL_Status
   :show-inheritance:
   :member-order: bysource
   :members:
   :undoc-members:

.. _Vector: https://vector.com/
