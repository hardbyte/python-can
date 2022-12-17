.. _can interface modules:

Hardware Interfaces
===================

**python-can** hides the low-level, device-specific interfaces to controller
area network adapters in interface dependant modules. However as each hardware
device is different, you should carefully go through your interface's
documentation.

.. note::
   The *Interface Names* are listed in :doc:`configuration`.


The following hardware interfaces are included in python-can:

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


Additional interface types can be added via the :ref:`plugin interface`, or by installing a third party package that utilises the :ref:`plugin interface`.
