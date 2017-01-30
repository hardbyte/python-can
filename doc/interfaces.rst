CAN Interface Modules
---------------------

**python-can** hides the low-level, device-specific interfaces to controller
area network adapters in interface dependant modules. However as each hardware
device is different, you should carefully go through your interface's
documentation.

The available interfaces are:

.. toctree::
   :maxdepth: 1

   interfaces/socketcan
   interfaces/kvaser
   interfaces/serial
   interfaces/ixxat
   interfaces/pcan
   interfaces/usb2can
   interfaces/nican
   interfaces/neovi
   interfaces/remote
   interfaces/virtual



The *Interface Names* are listed in :doc:`configuration`.

