.. _socketcand_doc:

socketcand Interface
====================
`Socketcand <https://github.com/linux-can/socketcand>`__ is part of the 
`Linux-CAN <https://github.com/linux-can>`__ project, providing a 
Network-to-CAN bridge as a Linux damon. It implements a specific
`TCP/IP based communication protocol <https://github.com/linux-can/socketcand/blob/master/doc/protocol.md>`__
to transfer CAN frames and control commands.

The main advantage compared to UDP-based protocols (e.g. virtual interface)
is, that TCP guarantees delivery and that the message order is kept.

Here is a small example dumping all can messages received by a socketcand 
daemon running on a remote Raspberry Pi:

.. code-block:: python

    import can

    bus = can.interface.Bus(bustype='socketcand', host="10.0.16.15", port=29536, channel="can0")

    # loop until Ctrl-C
    try:
      while True:
        msg = bus.recv()
        print(msg)
    except KeyboardInterrupt:
      pass

The output may look like this::

    Timestamp: 1637791111.209224    ID: 000006fd    X Rx                DLC:  8    c4 10 e3 2d 96 ff 25 6b
    Timestamp: 1637791111.233951    ID: 000001ad    X Rx                DLC:  4    4d 47 c7 64
    Timestamp: 1637791111.409415    ID: 000005f7    X Rx                DLC:  8    86 de e6 0f 42 55 5d 39
    Timestamp: 1637791111.434377    ID: 00000665    X Rx                DLC:  8    97 96 51 0f 23 25 fc 28
    Timestamp: 1637791111.609763    ID: 0000031d    X Rx                DLC:  8    16 27 d8 3d fe d8 31 24
    Timestamp: 1637791111.634630    ID: 00000587    X Rx                DLC:  8    4e 06 85 23 6f 81 2b 65

Socketcand Quickstart
---------------------

The following section will show how to get the stuff installed on a Raspberry Pi with a MCP2515-based
CAN interface, e.g. available from `Waveshare <https://www.waveshare.com/rs485-can-hat.htm>`__.
However, it will also work with any other socketcan device.

Install CAN Interface for a MCP2515 based interface on a Raspberry Pi
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add the following lines to ``/boot/config.txt``.
Please take care on the frequency of the crystal on your MCP2515 board::

    dtparam=spi=on
    dtoverlay=mcp2515-can0,oscillator=12000000,interrupt=25,spimaxfrequency=1000000

Reboot after ``/boot/config.txt`` has been modified.


Enable socketcan for can0
~~~~~~~~~~~~~~~~~~~~~~~~~

Create config file for systemd-networkd to start the socketcan interface automatically:

.. code-block:: bash

    cat >/etc/systemd/network/80-can.network <<'EOT'
    [Match]
    Name=can0
    [CAN]
    BitRate=250K
    RestartSec=100ms
    EOT

Enable ``systemd-networkd`` on reboot and start it immediately (if it was not already startet):

.. code-block:: bash

    sudo systemctl enable systemd-networkd
    sudo systemctl start systemd-networkd


Build socketcand from source
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # autoconf is needed to build socketcand
    sudo apt-get install -y autoconf
    # clone & build sources
    git clone https://github.com/linux-can/socketcand.git
    cd socketcand
    ./autogen.sh
    ./configure
    make


Install socketcand
~~~~~~~~~~~~~~~~~~
.. code-block:: bash

    make install


Run socketcand
~~~~~~~~~~~~~~
.. code-block:: bash

    ./socketcand -v -i can0

During start, socketcand will prompt its IP address and port it listens to::

    Verbose output activated

    Using network interface 'eth0'
    Listen adress is 10.0.16.15
    Broadcast adress is 10.0.255.255
    creating broadcast thread...
    binding socket to 10.0.16.15:29536
