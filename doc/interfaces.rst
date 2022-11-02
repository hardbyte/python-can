.. _can interface modules:

CAN Interface Modules
---------------------

**python-can** hides the low-level, device-specific interfaces to controller
area network adapters in interface dependant modules. However as each hardware
device is different, you should carefully go through your interface's
documentation.

The available interfaces are:

.. toctree::
   :maxdepth: 1

   interfaces/canalystii
   interfaces/cantact
   interfaces/canine
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
   interfaces/udp_multicast
   interfaces/usb2can
   interfaces/vector
   interfaces/virtual

The *Interface Names* are listed in :doc:`configuration`.


.. _plugin interface:

Plugin Interface
^^^^^^^^^^^^^^^^

External packages can register new interfaces by using the ``can.interface`` entry point
in its project configuration. The format of the entry point depends on your project
configuration format (*pyproject.toml*, *setup.cfg* or *setup.py*).

In the following example ``module`` defines the location of your bus class inside your
package e.g. ``my_package.subpackage.bus_module`` and ``classname`` is the name of
your :class:`can.BusABC` subclass.

.. tab:: pyproject.toml (PEP 621)

   .. code-block:: toml

        # Note the quotes around can.interface in order to escape the dot .
        [project.entry-points."can.interface"]
        interface_name = "module:classname"

.. tab:: setup.cfg

   .. code-block:: ini

        [options.entry_points]
        can.interface =
            interface_name = module:classname

.. tab:: setup.py

   .. code-block:: python

        from setuptools import setup

        setup(
            # ...,
            entry_points = {
                'can.interface': [
                    'interface_name = module:classname'
                ]
            }
        )

The ``interface_name`` can be used to
create an instance of the bus in the **python-can** API:

.. code-block:: python

    import can

    bus = can.Bus(interface="interface_name", channel=0)
