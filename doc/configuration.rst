.. _configuration:

Configuration
=============


Usually this library is used with a particular CAN interface, this can be
specified in code, read from configuration files or environment variables.

See :func:`can.util.load_config` for implementation.

In Code
-------

The ``can`` object exposes an ``rc`` dictionary which can be used to set
the **interface** and **channel**.

::

    import can
    can.rc['interface'] = 'socketcan'
    can.rc['channel'] = 'vcan0'
    can.rc['bitrate'] = 500000
    from can.interface import Bus

    bus = Bus()


You can also specify the interface and channel for each Bus instance::

    import can

    bus = can.interface.Bus(bustype='socketcan', channel='vcan0', bitrate=500000)


Configuration File
------------------

On Linux systems the config file is searched in the following paths:

#. ``~/can.conf``
#. ``/etc/can.conf``
#. ``$HOME/.can``
#. ``$HOME/.canrc``

On Windows systems the config file is searched in the following paths:

#. ``%USERPROFILE%/can.conf``
#. ``can.ini`` (current working directory)
#. ``%APPDATA%/can.ini``

The configuration file sets the default interface and channel:

::

    [default]
    interface = <the name of the interface to use>
    channel = <the channel to use by default>
    bitrate = <the bitrate in bits/s to use by default>


The configuration can also contain additional sections (or context):

::

    [default]
    interface = <the name of the interface to use>
    channel = <the channel to use by default>
    bitrate = <the bitrate in bits/s to use by default>

    [HS]
    # All the values from the 'default' section are inherited
    channel = <the channel to use>
    bitrate = <the bitrate in bits/s to use. i.e. 500000>

    [MS]
    # All the values from the 'default' section are inherited
    channel = <the channel to use>
    bitrate = <the bitrate in bits/s to use. i.e. 125000>


::

    from can.interface import Bus

    hs_bus = Bus(context='HS')
    ms_bus = Bus(context='MS')

Environment Variables
---------------------

Configuration can be pulled from these environmental variables:

    * CAN_INTERFACE
    * CAN_CHANNEL
    * CAN_BITRATE
    * CAN_CONFIG

The ``CAN_CONFIG`` environment variable allows to set any bus configuration using JSON.

For example:

``CAN_INTERFACE=socketcan CAN_CONFIG={"receive_own_messages": true, "fd": true}``

.. _interface names:

Interface Names
---------------

Lookup table of interface names:

+---------------------+-------------------------------------+
| Name                | Documentation                       |
+=====================+=====================================+
| ``"canalystii"``    | :doc:`interfaces/canalystii`        |
+---------------------+-------------------------------------+
| ``"cantact"``       | :doc:`interfaces/cantact`           |
+---------------------+-------------------------------------+
| ``"etas"``          | :doc:`interfaces/etas`              |
+---------------------+-------------------------------------+
| ``"gs_usb"``        | :doc:`interfaces/gs_usb`            |
+---------------------+-------------------------------------+
| ``"iscan"``         | :doc:`interfaces/iscan`             |
+---------------------+-------------------------------------+
| ``"ixxat"``         | :doc:`interfaces/ixxat`             |
+---------------------+-------------------------------------+
| ``"kvaser"``        | :doc:`interfaces/kvaser`            |
+---------------------+-------------------------------------+
| ``"neousys"``       | :doc:`interfaces/neousys`           |
+---------------------+-------------------------------------+
| ``"neovi"``         | :doc:`interfaces/neovi`             |
+---------------------+-------------------------------------+
| ``"nican"``         | :doc:`interfaces/nican`             |
+---------------------+-------------------------------------+
| ``"nixnet"``        | :doc:`interfaces/nixnet`            |
+---------------------+-------------------------------------+
| ``"pcan"``          | :doc:`interfaces/pcan`              |
+---------------------+-------------------------------------+
| ``"robotell"``      | :doc:`interfaces/robotell`          |
+---------------------+-------------------------------------+
| ``"seeedstudio"``   | :doc:`interfaces/seeedstudio`       |
+---------------------+-------------------------------------+
| ``"serial"``        | :doc:`interfaces/serial`            |
+---------------------+-------------------------------------+
| ``"slcan"``         | :doc:`interfaces/slcan`             |
+---------------------+-------------------------------------+
| ``"socketcan"``     | :doc:`interfaces/socketcan`         |
+---------------------+-------------------------------------+
| ``"socketcand"``    | :doc:`interfaces/socketcand`        |
+---------------------+-------------------------------------+
| ``"systec"``        | :doc:`interfaces/systec`            |
+---------------------+-------------------------------------+
| ``"udp_multicast"`` | :doc:`interfaces/udp_multicast`     |
+---------------------+-------------------------------------+
| ``"usb2can"``       | :doc:`interfaces/usb2can`           |
+---------------------+-------------------------------------+
| ``"vector"``        | :doc:`interfaces/vector`            |
+---------------------+-------------------------------------+
| ``"virtual"``       | :doc:`interfaces/virtual`           |
+---------------------+-------------------------------------+

Additional interface types can be added via the :ref:`plugin interface`.