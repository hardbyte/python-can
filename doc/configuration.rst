Configuration
=============


Usually this library is used with a particular CAN interface, this can be
specified in code, read from configuration files or environment variables.

See :func:`can.util.load_config` for implementation.

In Code
-------

The ``can`` object exposes an ``rc`` dictionary which can be used to set
the **interface** and **channel** before importing from ``can.interfaces``.

::

    import can
    can.rc['interface'] = 'socketcan'
    can.rc['channel'] = 'vcan0'
    from can.interfaces.interface import Bus

    bus = Bus()


Configuration File
------------------

On Linux systems the config file is searched in the following paths:

1. ``/etc/can.conf``
2. ``$HOME/.can``
3. ``$HOME/.canrc``

On Windows systems the config file is searched in the following paths:

1. ``can.ini`` (current working directory)
2. ``$APPDATA/can.ini``

The configuration file sets the default interface and channel:

::

    [default]
    interface = <the name of the interface to use>
    channel = <the channel to use by default>


Environment Variables
---------------------

Configuration can be pulled from these environmental variables:

    * CAN_INTERFACE
    * CAN_CHANNEL


Interface Names
---------------

Lookup table of interface names:

+---------------------+-------------------------------------+
| Name                | Documentation                       |
+=====================+=====================================+
| ``"socketcan"``     | :doc:`interfaces/socketcan`         |
+---------------------+-------------------------------------+
| ``"kvaser"``        | :doc:`interfaces/kvaser`            |
+---------------------+-------------------------------------+
| ``"serial"``        | :doc:`interfaces/serial`            |
+---------------------+-------------------------------------+
| ``"ixxat"``         | :doc:`interfaces/ixxat`             |
+---------------------+-------------------------------------+
| ``"pcan"``          | :doc:`interfaces/pcan`              |
+---------------------+-------------------------------------+
| ``"usb2can"``       | :doc:`interfaces/usb2can`           |
+---------------------+-------------------------------------+
| ``"nican"``         | :doc:`interfaces/nican`             |
+---------------------+-------------------------------------+
| ``"neovi"``         | :doc:`interfaces/neovi`             |
+---------------------+-------------------------------------+
| ``"remote"``        | :doc:`interfaces/remote`            |
+---------------------+-------------------------------------+
| ``"virtual"``       | :doc:`interfaces/virtual`           |
+---------------------+-------------------------------------+
