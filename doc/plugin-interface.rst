
.. _plugin interface:

Plugin Interface
================

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



Example Interface Plugins
-------------------------

The table below lists interface drivers that can be added by installing additional packages that utilise the plugin API. These modules are optional dependencies of python-can.

.. note::
   The packages listed below are maintained by other authors. Any issues should be reported in their corresponding repository and **not** in the python-can repository.

+----------------------------+-------------------------------------------------------+
| Name                       | Description                                           |
+============================+=======================================================+
| `python-can-canine`_       | CAN Driver for the CANine CAN interface               |
+----------------------------+-------------------------------------------------------+
| `python-can-cvector`_      | Cython based version of the 'VectorBus'               |
+----------------------------+-------------------------------------------------------+
| `python-can-remote`_       | CAN over network bridge                               |
+----------------------------+-------------------------------------------------------+
| `python-can-sontheim`_     | CAN Driver for Sontheim CAN interfaces (e.g. CANfox)  |
+----------------------------+-------------------------------------------------------+

.. _python-can-canine: https://github.com/tinymovr/python-can-canine
.. _python-can-cvector: https://github.com/zariiii9003/python-can-cvector
.. _python-can-remote: https://github.com/christiansandberg/python-can-remote
.. _python-can-sontheim: https://github.com/MattWoodhead/python-can-sontheim
