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
   interfaces/slcan
   interfaces/ixxat
   interfaces/pcan
   interfaces/usb2can
   interfaces/nican
   interfaces/iscan
   interfaces/neovi
   interfaces/vector
   interfaces/virtual
   interfaces/canalystii
   interfaces/systec

Additional interfaces can be added via a plugin interface. An external package
can register a new interface by using the ``can.interface`` entry point in its setup.py.

The format of the entry point is ``interface_name=module:classname`` where
``classname`` is a concrete :class:`can.BusABC` implementation.

::

 entry_points={
     'can.interface': [
         "interface_name=module:classname",
     ]
 },


The *Interface Names* are listed in :doc:`configuration`.

