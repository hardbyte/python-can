The **C**ontroller **A**rea **N**etwork is a bus standard designed to 
allow microcontrollers and devices to communicate with each other. It 
has priority based bus arbitration, reliable deterministic 
communication. It is used in cars, trucks, wheelchairs and more. See
[wikipedia][1] for more info.

# python-can

This module provides controller area network support for [Python][4].

## Quickstart

On linux to create a virtual can interface using socketcan run the following:

    :::bash
    sudo modprobe vcan
    sudo ip link add dev vcan0 type vcan
    sudo ifconfig vcan0 up

`can0` should be substituted for `vcan` if you are using real hardware.

    :::bash
    ifconfig

should reveal a new `vcan0` interface. Fire up wireshark and watch this
new interface.

Then spam your new bus:

    :::python
    import time
    import can
    can.rc['interface'] = 'socketcan_native'
    from can.interfaces.interface import Bus
    can_interface = 'vcan0'

    def producer(id):
        """:param id: Spam the bus with messages including the data id."""
        bus = Bus(can_interface)
        for i in range(10):
            msg = can.Message(arbitration_id=0xc0ffee, data=[id, i, 0, 1, 3, 1, 4, 1], extended_id=False)
            bus.write(msg)
        # Issue #3: Need to keep running to ensure the writing threads stay alive. ?
        time.sleep(1)

    producer(10)

With debugging turned right up this looks something like this:

![Wireshark Screenshot][7]

The process to follow bus traffic is even easier:

    :::python
    for message in Bus(can_interface):
        print(message)


## Installation

A Controller Area Networking interface is required for `python-can` to do
anything useful. The two primary interfaces are `socketcan` on GNU/Linux 
and [Kvaser][2]'s CANLib SDK for Windows (also available on Linux).

The default interface can be selected at install time with a configuration
script. Alternatively, before creating a **bus** object the global `can.rc`
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


## Install python-can

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
[7]: http://cdn.bitbucket.org/hardbyte/python-can/downloads/wireshark.png