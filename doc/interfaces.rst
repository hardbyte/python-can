.. _can interface modules:

Hardware Interfaces
===================

**python-can** hides the low-level, device-specific interfaces to controller
area network adapters in interface dependant modules. However as each hardware
device is different, you should carefully go through your interface's
documentation.

.. note::
   The *Interface Names* are listed in :doc:`configuration`.


The available hardware interfaces are:

.. toctree::
   :maxdepth: 1

   interfaces/canalystii
   interfaces/cantact
   interfaces/etas
   interfaces/gs_usb
   interfaces/iscan
   interfaces/ixxat
   interfaces/kvaser
   interfaces/neousys
   interfaces/neovi
   interfaces/nican
   interfaces/nixnet
   interfaces/pcan
   interfaces/robotell
   interfaces/seeedstudio
   interfaces/serial
   interfaces/slcan
   interfaces/socketcan
   interfaces/socketcand
   interfaces/systec
   interfaces/usb2can
   interfaces/vector

