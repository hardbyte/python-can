
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

