neoVI Interface
===============

.. warning::

    This ``neoVI`` documentation is a work in progress. Feedback and revisions are most welcome!


Interface to `Intrepid Control Systems <https://www.intrepidcs.com/>`__ neoVI API via `pyneovi <http://kempj.co.uk/projects/pyneovi/>`__ wrapper.

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


