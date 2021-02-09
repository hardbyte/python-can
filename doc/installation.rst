Installation
============


Install ``can`` with ``pip``:
::

    $ pip install python-can


As most likely you will want to interface with some hardware, you may
also have to install platform dependencies. Be sure to check any other
specifics for your hardware in :doc:`interfaces`.


GNU/Linux dependencies
----------------------

Reasonably modern Linux Kernels (2.6.25 or newer) have an implementation
of ``socketcan``. This version of python-can will directly use socketcan
if called with Python 3.3 or greater, otherwise that interface is used
via ctypes.

Windows dependencies
--------------------

Kvaser
~~~~~~

To install ``python-can`` using the Kvaser CANLib SDK as the backend:

1. Install the `latest stable release of
   Python <http://python.org/download/>`__.

2. Install `Kvaser's latest Windows CANLib
   drivers <http://www.kvaser.com/en/downloads.html>`__.

3. Test that Kvaser's own tools work to ensure the driver is properly
   installed and that the hardware is working.

PCAN
~~~~

Download and install the latest driver for your interface from
`PEAK-System's download page <http://www.peak-system.com/Support.55.0.html?&L=1>`__.

Note that PCANBasic API timestamps count seconds from system startup. To
convert these to epoch times, the uptime library is used. If it is not
available, the times are returned as number of seconds from system
startup. To install the uptime library, run ``pip install uptime``.

This library can take advantage of the `Python for Windows Extensions
<https://github.com/mhammond/pywin32>`__ library if installed.
It will be used to get notified of new messages instead of
the CPU intensive polling that will otherwise have be used.

IXXAT
~~~~~

To install ``python-can`` using the IXXAT VCI V3 or V4 SDK as the backend:

1. Install `IXXAT's latest Windows VCI V3 SDK or VCI V4 SDK (Win10)
   drivers <https://www.ixxat.com/technical-support/resources/downloads-and-documentation?ordercode=1.01.0281.12001>`__.

2. Test that IXXAT's own tools (i.e. MiniMon) work to ensure the driver
   is properly installed and that the hardware is working.

NI-CAN
~~~~~~

Download and install the NI-CAN drivers from
`National Instruments <http://www.ni.com/downloads/ni-drivers/>`__.

Currently the driver only supports 32-bit Python on Windows.

neoVI
~~~~~

See :doc:`interfaces/neovi`.

Vector
~~~~~~

To install ``python-can`` using the XL Driver Library as the backend:

1. Install the `latest drivers <https://www.vector.com/latest_driver>`__ for your Vector hardware interface.

2. Install the `XL Driver Library <https://www.vector.com/xl-lib/11/>`__ or copy the ``vxlapi.dll`` and/or
   ``vxlapi64.dll`` into your working directory.

3. Use Vector Hardware Configuration to assign a channel to your application.

CANtact
~~~~~~~

CANtact is supported on Linux, Windows, and macOS. 
To install ``python-can`` using the CANtact driver backend:

``python3 -m pip install "python-can[cantact]"``

If ``python-can`` is already installed, the CANtact backend can be installed separately:

``python3 -m pip install cantact``

Additional CANtact documentation is available at https://cantact.io.

Installing python-can in development mode
-----------------------------------------

A "development" install of this package allows you to make changes locally
or pull updates from the Git repository and use them without having to
reinstall. Download or clone the source repository then:

::

    python setup.py develop


