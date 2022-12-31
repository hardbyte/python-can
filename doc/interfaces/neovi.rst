Intrepid Control Systems neoVI
==============================

.. note::

    This ``ICS neoVI`` documentation is a work in progress. Feedback and revisions
    are most welcome!


Interface to `Intrepid Control Systems <https://www.intrepidcs.com/>`__ neoVI
API range of devices via `python-ics <https://pypi.python.org/pypi/python-ics/>`__
wrapper on Windows.


Installation
------------
This neoVI interface requires the installation of the ICS neoVI DLL and ``python-ics``
package.

- Download and install the Intrepid Product Drivers
    `Intrepid Product Drivers <https://cdn.intrepidcs.net/updates/files/ICSDrivers.zip>`__

- Install ``python-can`` with the ``neovi`` extras:
    .. code-block:: bash

        pip install python-ics[neovi]


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
.. autoexception:: can.interfaces.ics_neovi.ICSApiError
.. autoexception:: can.interfaces.ics_neovi.ICSInitializationError
.. autoexception:: can.interfaces.ics_neovi.ICSOperationError
