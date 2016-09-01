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

To use the PCAN-Basic API as the backend (which has only been tested
with Python 2.7):

1. Download the latest version of the `PCAN-Basic
   API <http://www.peak-system.com/Downloads.76.0.html?>`__.

2. Extract ``PCANBasic.dll`` from the Win32 subfolder of the archive or
   the x64 subfolder depending on whether you have a 32-bit or 64-bit
   installation of Python.

3. Copy ``PCANBasic.dll`` into the working directory where you will be
   running your python script. There is probably a way to install the
   dll properly, but I'm not certain how to do that.

Note that PCANBasic API timestamps count seconds from system startup. To
convert these to epoch times, the uptime library is used. If it is not
available, the times are returned as number of seconds from system
startup. To install the uptime library, run ``pip install uptime``.

IXXAT
~~~~~

To install ``python-can`` using the IXXAT VCI V3 SDK as the backend:

1. Install `IXXAT's latest Windows VCI V3 SDK
   drivers <http://www.ixxat.com/support/file-and-documents-download/drivers/vci-v3-driver-download>`__.

2. Test that IXXAT's own tools (i.e. MiniMon) work to ensure the driver
   is properly installed and that the hardware is working.


Installing python-can in development mode
-----------------------------------------

A "development" install of this package allows you to make changes locally
or pull updates from the Mercurial repository and use them without having to
reinstall. Download or clone the source repository then:

::

    python setup.py develop


