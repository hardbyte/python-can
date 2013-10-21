The **C**ontroller **A**rea **N**etwork is a bus standard designed to 
allow microcontrollers and devices to communicate with each other. It 
has priority based bus arbitration, reliable deterministic 
communication. It is used in cars, trucks, wheelchairs and more. See
[wikipedia][1] for more info.

# python-can

This module provides controller area network support for [Python][4].

## Configuration File

In order to use this library a CAN interface needs to be specified.
A method to do this is to create a configuration file called `can.conf`,
`~/.canrc` or `can.ini`


## Installation

A Controller Area Networking interface is required for `python-can` to do
anything useful. The two primary interfaces are `socketcan` on GNU/Linux 
and [Kvaser][2]'s CANLib SDK for Windows (also available on Linux). A 
third interface available for Windows is [Peak-System][8]'s 
PCAN-Basic API.

Alternatively, before creating a **bus** object the global `can.rc`
dictionary can be modified:

    :::python
    # Interface can be kvaser, socketcan, socketcan_ctypes, socketcan_native, serial
    rc = {
          'default-interface': 'kvaser',
          'interface': 'kvaser'
          }


### GNU/Linux dependencies

Reasonably modern Linux Kernels (2.6.25 or newer) have an implementation of 
``socketcan``. This version of python-can will directly use socketcan
if called with Python 3.3 or greater, otherwise that interface is
used via ctypes.

### Windows dependencies

To install `python-can` using the Kvaser CANLib SDK as the backend:

1. Install the [latest stable release of Python][4].

2. Install [Kvaser's latest Windows CANLib drivers][5].

3. Test that Kvaser's own tools work to ensure the driver is properly 
installed and that the hardware is working.

To use the PCAN-Basic API as the backend (which has only been tested with 
Python 2.7):

1. Download the latest version of the [PCAN-Basic API][9].

2. Extract PCANBasic.dll from the Win32 subfolder of the archive or the x64 
subfolder depending on whether you have a 32-bit or 64-bit installation of 
Python.

3. Copy PCANBasic.dll into the working directory where you will be running 
your python script.  There is probably a way to install the dll properly, 
but I'm not certain how to do that.

Note that PCANBasic API timestamps count seconds from system startup.  To 
convert these to epoch times, the uptime library is used.  If it is not 
available, the times are returned as number of seconds from system startup. 
To install the uptime library, run `pip install uptime`.


## Install python-can

You may need to install [pip][7] first.

Two options, install normally with:

    python setup.py install

Or to do a "development" install of this package to your machine (this allows 
you to make changes locally or pull updates from the Mercurial repository and
use them without having to reinstall):

    python setup.py develop

On linux you will need sudo rights. 


## Documentation

The documentation for python-can has been generated with Sphinx they can be viewed online at
[python-can.readthedocs.org][6]


### Generation

With sphinx installed the documentation can be generated with:

    python setup.py build_sphinx
    
    
[1]: http://en.wikipedia.org/wiki/CAN_bus
[2]: http://www.kvaser.com
[3]: http://www.brownhat.org/docs/socketcan/llcf-api.html
[4]: http://python.org/download/
[5]: http://www.kvaser.com/en/downloads.html
[6]: https://python-can.readthedocs.org/en/latest/
[7]: http://www.pip-installer.org/en/latest/installing.html
[8]: http://www.peak-system.com/
[9]: http://www.peak-system.com/Downloads.76.0.html?