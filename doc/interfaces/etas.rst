.. _etasdoc:

ETAS Interface
================

Overview
--------

This Interface adds Windows support for the CAN controllers by `ETAS GmbH <https://www.etas.com>`__.
This python-can interface is called ``etas``.

Windows Support
---------------
 
ETAS provides a C language API for third-party integration Software. This API is called BOA (Basic Open API) which is leveraged by this interface to provide support for python-can.

.. _etas-installation:

ETAS BOA Windows install
------------------------

    1. If not done already, install **Python 3** for example by downloading the  `Windows executable installer <https://www.python.org/downloads/windows/>`__.
    2. Download and install the `Basic Open API (BOA) <https://www.etas.com/en/downloadcenter/18102.php>`__ Distribution Packet.
    3. Install the driver for the device you are using with either:

        * **Recommended:** the `Hardware Service Pack (HSP) <https://www.etas.com/en/products/hardware_products-hsp.php>`__ to get the most recent version of the drivers.
        * the CD-Rom you received with the device

    4. *Optional*: if you didn't install BOA in the default installation path: ``C:\Program Files\ETAS\BOA_V2``, you then have to add: ``<installation Path>\Bin\Win32\Dll\Framework`` to your Windows Environment Path variable.

.. warning::

    Some of the older ETAS drivers can only be executed within a 32-bit environment.

    If you have such drivers on your system, we highly recommend you to first use the `Hardware Service Pack (HSP) <https://www.etas.com/en/products/hardware_products-hsp.php>`__ in order to check if more recent versions with 64-bit support exist.

    If no 64 bits version are available, please install the 32-bit version of the `Basic Open API (BOA) <https://www.etas.com/en/downloadcenter/18102.php>`__ and use a 32-bit version of Python.

Interface Specific Items
------------------------

There are a few things to note about this interface:

    1. The shown timestamps are from the time the CAN device is connected to the PC. If two devices or more are connected, their times are probably not synced (unless they have such sync features). However, if a device has several channels, the timestamps of those channels will be synced.

    2. To show Warnings, Bus Events or Error Frames, you can set the ``can.interfaces.etas`` logger level to ``INFO`` by adding the following lines to your code:

        ::

            import logging
            logging.getLogger("can.interfaces.etas").setLevel(logging.INFO)

        For developers you may even want to set the logger level to ``DEBUG``

Configuration
-------------

Here is an example configuration-file for using `one of the CAN-FD capable ES58X interface <https://www.etas.com/en/products/es58x.php>`_:

::

    [default]
    interface = etas
    channel = None
    bitrate = 500000
    data_bitrate = 2000000
    fd = True
    can_filters = None
    
Full parameter description can be found below in the  ``__init__`` function of the interface.

Example
-------

To get you started, please find below a minimal example.

.. code-block:: python

    import can
    from can.interfaces import etas
    import logging

    # In this minimum set up, we are using an ES58X (two channels model) with CAN1 and CAN2 connected together using the Y cable (and 120 ohms resistor of course)
    # We assume that no ETAS devices other than the ES58X are connected (else, the channel numbering should be adjusted accordingly)
    if __name__ == '__main__':
        logging.getLogger("can.interfaces.etas").setLevel(logging.INFO) # Display INFO messages

        # Optional: list the connected devices:
        print("Connected devices: ", can.interfaces.etas.EtasCSI.enumerate_controllers())

        # If you want to test on ES581.4 (or other non-FD interface), set is_fd to False
        is_fd = True
        bus_1 = can.interface.Bus(bustype='etas', channel=0, bitrate=500000, data_bitrate=2000000, fd=is_fd) # Open CAN1
        bus_2 = can.interface.Bus(bustype='etas', channel=1, bitrate=500000, data_bitrate=2000000, fd=is_fd) # Open CAN2

        bus_1.send(can.Message(data=[x for x in range(64 if is_fd else 8)], is_fd=is_fd, bitrate_switch=is_fd)) # Send message on CAN1
        print(bus_2.recv(1)) # Receive it on CAN2 and print it

        bus_1.shutdown()
        bus_2.shutdown()


BusState
--------

.. autoclass:: can.interfaces.etas.BusState
   :members:
   :member-order: bysource


EtasMessage
-----------

.. autoclass:: can.interfaces.etas.EtasMessage


Bus
---

.. autoclass:: can.interfaces.etas.EtasBus
   :exclude-members: time_to_tick, tick_to_time, oci_exec

.. autoexception:: can.interfaces.etas.EtasError


OCI_CANConfiguration and OCI_CANFDConfiguration
-----------------------------------------------

.. autoclass:: can.interfaces.etas.OCI_CANConfiguration
   :exclude-members: get_controller_configuration

.. autoclass:: can.interfaces.etas.OCI_CANFDConfiguration
   :exclude-members: get_controller_fd_configuration
