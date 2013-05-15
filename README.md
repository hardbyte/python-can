The **C**ontroller **A**rea **N**etwork is a bus standard designed to 
allow microcontrollers and devices to communicate with each other. It 
has priority based bus arbitration, reliable deterministic 
communication. It is used in cars, trucks, wheelchairs and more. See
[wikipedia][1] for more info.

# python-can

This module provides controller area network support for [Python][4].

## Socketcan Quickstart

The full documentation for socketcan can be found in the kernel docs at
[networking/can.txt][8]. The CAN network driver provides a generic 
interface to setup, configure and monitor CAN devices. To configure 
bit-timing parameters use the program `ip`.

### The virtual CAN driver (vcan)

The virtual CAN interfaces allow the transmission and reception of CAN 
frames without real CAN controller hardware. Virtual CAN network devices
are usually named 'vcanX', like vcan0 vcan1 vcan2.

To create a virtual can interface using socketcan run the following:

    :::bash
    sudo modprobe vcan
    # Create a vcan network interface with a specific name
    sudo ip link add dev vcan0 type vcan
    sudo ifconfig vcan0 up


### Real Device
`can0` should be substituted for `vcan` if you are using real hardware.
Setting the bitrate can also be done at the same time, for example to 
enable an existing `can0` interface with a bitrate of 1MB:

    :::bash
    sudo ip link set can0 up type can bitrate 1000000

#### CAN Errors

A device may enter the "bus-off" state if too much errors occurred on
the CAN bus. Then no more messages are received or sent. An automatic
bus-off recovery can be enabled by setting the "restart-ms" to a
non-zero value, e.g.:

    :::bash
    sudo ip link set canX type can restart-ms 100

Alternatively, the application may realize the "bus-off" condition
by monitoring CAN error frames and do a restart when appropriate with
the command:

    :::bash
    ip link set canX type can restart

Note that a restart will also create a CAN error frame.

### List network interfaces

To reveal the newly created `can0` or a `vcan0` interface:

    :::bash
    ifconfig

### Display CAN statistics

    :::bash
    ip -details -statistics link show vcan0

  
### Network Interface Removal

To remove the network interface:

    :::bash
    sudo ip link del vcan0

## Wireshark

Wireshark supports socketcan and can be used to debug *python-can* messages. Fire it
up and watch your new interface.

To spam a bus:

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
[8]: https://www.kernel.org/doc/Documentation/networking/can.txt