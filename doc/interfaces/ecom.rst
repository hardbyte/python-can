.. _ecomdoc:

ECOM CAN Interface
==================

Interface to `Econtrols ECOM <https://www.cancapture.com/ecom>`__ device. Developed for
`Driver V3.5.0.0 <https://www.cancapture.com/sites/default/files/Driver_Setup_V3.5.0.0.exe>`__
with the
`ECOM Developer's API Reference Guide <https://www.cancapture.com/sites/default/files/ER000092C-_00.pdf>`__
Rev. C.  This has only been tested on Windows.

.. note::
    Currently the following has not yet been implemented:
        * send_periodic - currently uses the default threaded implementation, which does not seem to work.
        * can_filters

Bus
---
.. autoclass:: can.interfaces.ecom.EcomBus
    :members:

Configuration File
------------------
The simplest configuration file would be::

    [default]
    interface = ecom

This device only has a single channel, therefore it is not necessary to specify a channel.
It will be ignored.

The following parameters are optional:

* ``bitrate`` (default: 500000) Bit rate for the device. Options are: 125000, 250000, 500000, 1000000
* ``serl_no`` (default: None) Serial number of the device
* ``synchronous`` (default: False) Enables a HW synchronous mode on the device.  Not recommended, very slow.


Filtering
---------
.. note::
    Not yet implemented.

List Available Devices
----------------------
In the case where multiple devices are connected, they must be selected by their serial number or only the first
device found will be used.  If that device is already connected to, an error will be thrown.

The serial numbers can be retrieved from the physical device itself or by using the provided ``get_ecom_devices()``
function.  See an example use below:

    >>> from can.interfaces.ecom import get_ecom_devices
    >>> for serl_no in get_ecom_devices():
    ...     print(f"Found ECOM with serial number: {serl_no}")

Internals
---------
TBD
