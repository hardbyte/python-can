.. _pcandoc:

PCAN Basic API
==============

.. warning::

    This ``PCAN`` documentation is a work in progress. Feedback and revisions are most welcome!


Interface to `Peak-System <http://www.peak-system.com/>`__'s PCAN-Basic API.

Configuration
-------------

An example `can.ini` file for windows 7:

::

    [default]
    interface = pcan
    channel = PCAN_USBBUS1


Bus
---

.. autoclass:: can.interfaces.pcan.PcanBus

