neoVI Interface
===============

.. warning::

    This ``neoVI`` documentation is a work in progress. Feedback and revisions
    are most welcome!


Interface to `Intrepid Control Systems <https://www.intrepidcs.com/>`__ neoVI
API range of devices via `pyneovi <http://kempj.co.uk/projects/pyneovi/>`__
wrapper on Windows.

.. note::

    This interface is not supported on Linux, however on Linux neoVI devices
    are supported via :doc:`socketcan` with ICS `Kernel-mode SocketCAN module
    for Intrepid devices
    <https://github.com/intrepidcs/intrepid-socketcan-kernel-module>`__ and
    `icsscand <https://github.com/intrepidcs/icsscand>`__


Installation
------------
This neoVI interface requires the installation of the ICS neoVI DLL and pyneovi
package.

- Download and install the Intrepid Product Drivers
    `Intrepid Product Drivers <https://cdn.intrepidcs.net/updates/files/ICSDrivers.zip>`__

- Install pyneovi using pip and the pyneovi bitbucket repo:
    .. code-block:: bash

        pip install https://bitbucket.org/Kemp_J/pyneovi/get/default.zip


Configuration
-------------

An example `can.ini` file for windows 7:

::

    [default]
    interface = neovi
    channel = 1


Bus
---

.. autoclass:: can.interfaces.neovi_api.NeoVIBus


