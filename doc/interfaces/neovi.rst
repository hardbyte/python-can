NEOVI Interface
==================

.. warning::

    This ``ICS NeoVI`` documentation is a work in progress. Feedback and revisions
    are most welcome!


Interface to `Intrepid Control Systems <https://www.intrepidcs.com/>`__ neoVI
API range of devices via `python-ics <https://pypi.python.org/pypi/python-ics/>`__
wrapper on Windows.


Installation
------------
This neovi interface requires the installation of the ICS neoVI DLL and python-ics
package.

- Download and install the Intrepid Product Drivers
    `Intrepid Product Drivers <https://cdn.intrepidcs.net/updates/files/ICSDrivers.zip>`__

- Install python-ics
    .. code-block:: bash

        pip install python-ics


Configuration
-------------

An example `can.ini` file for windows 7:

::

    [default]
    interface = neovi
    channel = 1


Bus
---

.. autoclass:: can.interfaces.ics_neovi.NeoViBus


