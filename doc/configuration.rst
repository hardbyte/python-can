Configuration
=============



In Code
-------

The ``can`` object exposes an ``rc`` dictionary which can be used to set the **interface**
before importing from ``can.interfaces``.

::

    import can
    can.rc['interface'] = 'socketcan'
    from can.interfaces.interface import Bus
    can_interface = 'vcan0'
    bus = Bus(can_interface)


Configuration File
------------------

Usually this library is used with a particular CAN interface, this can be specified in
a configuration file.

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

