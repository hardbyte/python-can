SocketCAN
=========

The full documentation for socketcan can be found in the kernel docs at
`networking/can.txt <https://www.kernel.org/doc/Documentation/networking/can.txt>`_.


.. note::

    Versions before 2.2 had two different implementations named
    ``socketcan_ctypes`` and ``socketcan_native``. These are now
    deprecated and the aliases to ``socketcan`` will be removed in
    version 4.0.  3.x releases raise a DeprecationWarning.


Socketcan Quickstart
--------------------

The CAN network driver provides a generic
interface to setup, configure and monitor CAN devices. To configure
bit-timing parameters use the program ``ip``.

The virtual CAN driver (vcan)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The virtual CAN interfaces allow the transmission and reception of CAN
frames without real CAN controller hardware. Virtual CAN network devices
are usually named 'vcanX', like vcan0 vcan1 vcan2.

To create a virtual can interface using socketcan run the following:

.. code-block:: bash

    sudo modprobe vcan
    # Create a vcan network interface with a specific name
    sudo ip link add dev vcan0 type vcan
    sudo ip link set vcan0 up

Real Device
~~~~~~~~~~~

``vcan`` should be substituted for ``can`` and ``vcan0`` should be
substituted for ``can0`` if you are using real hardware. Setting the
bitrate can also be done at the same time, for example to enable an
existing ``can0`` interface with a bitrate of 1MB:

.. code-block:: bash

    sudo ip link set can0 up type can bitrate 1000000

.. _socketcan-pcan:

PCAN
~~~~

Kernels >= 3.4 supports the PCAN adapters natively via :doc:`/interfaces/socketcan`, so there is no need to install any drivers. The CAN interface can be brought like so:

::

    sudo modprobe peak_usb
    sudo modprobe peak_pci
    sudo ip link set can0 up type can bitrate 500000

Send Test Message
^^^^^^^^^^^^^^^^^

The `can-utils <https://github.com/linux-can/can-utils>`_ library for linux
includes a script `cansend` which is useful to send known payloads. For
example to send a message on `vcan0`:

.. code-block:: bash

    cansend vcan0 123#DEADBEEF


CAN Errors
^^^^^^^^^^

A device may enter the "bus-off" state if too many errors occurred on
the CAN bus. Then no more messages are received or sent. An automatic
bus-off recovery can be enabled by setting the "restart-ms" to a
non-zero value, e.g.:

.. code-block:: bash

    sudo ip link set canX type can restart-ms 100

Alternatively, the application may realize the "bus-off" condition by
monitoring CAN error frames and do a restart when appropriate with the
command:

.. code-block:: bash

    ip link set canX type can restart

Note that a restart will also create a CAN error frame.

List network interfaces
~~~~~~~~~~~~~~~~~~~~~~~

To reveal the newly created ``can0`` or a ``vcan0`` interface:

.. code-block:: bash

    ifconfig

Display CAN statistics
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    ip -details -statistics link show vcan0

Network Interface Removal
~~~~~~~~~~~~~~~~~~~~~~~~~

To remove the network interface:

.. code-block:: bash

    sudo ip link del vcan0

Wireshark
---------

Wireshark supports socketcan and can be used to debug *python-can*
messages. Fire it up and watch your new interface.

To spam a bus:

.. code-block:: python

    import time
    import can

    bustype = 'socketcan'
    channel = 'vcan0'

    def producer(id):
        """:param id: Spam the bus with messages including the data id."""
        bus = can.interface.Bus(channel=channel, bustype=bustype)
        for i in range(10):
            msg = can.Message(arbitration_id=0xc0ffee, data=[id, i, 0, 1, 3, 1, 4, 1], is_extended_id=False)
            bus.send(msg)
        
        time.sleep(1)

    producer(10)

With debugging turned right up this looks something like this:

.. image:: ../images/wireshark.png
    :width: 100%


The process to follow bus traffic is even easier:

.. code-block:: python

    for message in Bus(can_interface):
        print(message)

Reading and Timeouts
--------------------

Reading a single CAN message off of the bus is simple with the ``bus.recv()``
function:

.. code-block:: python

    import can

    can_interface = 'vcan0'
    bus = can.interface.Bus(can_interface, bustype='socketcan')
    message = bus.recv()

By default, this performs a blocking read, which means ``bus.recv()`` won't
return until a CAN message shows up on the socket. You can optionally perform a
blocking read with a timeout like this:

.. code-block:: python

    message = bus.recv(1.0)  # Timeout in seconds.

    if message is None:
        print('Timeout occurred, no message.')

If you set the timeout to ``0.0``, the read will be executed as non-blocking,
which means ``bus.recv(0.0)`` will return immediately, either with a ``Message``
object or ``None``, depending on whether data was available on the socket.

Filtering
---------

The implementation features efficient filtering of can_id's. That filtering
occurs in the kernel and is much much more efficient than filtering messages
in Python.

Broadcast Manager
-----------------

The ``socketcan`` interface implements thin wrappers to the linux `broadcast manager`
socket api. This allows the cyclic transmission of CAN messages at given intervals.
The overhead for periodic message sending is extremely low as all the heavy lifting occurs
within the linux kernel.

send_periodic()
~~~~~~~~~~~~~~~

An example that uses the send_periodic is included in ``python-can/examples/cyclic.py``

The object returned can be used to halt, alter or cancel the periodic message task.

.. autoclass:: can.interfaces.socketcan.CyclicSendTask


Bus
---

.. autoclass:: can.interfaces.socketcan.SocketcanBus

   .. method:: recv(timeout=None)

      Block waiting for a message from the Bus.

      :param float timeout:
          seconds to wait for a message or None to wait indefinitely

      :rtype: can.Message or None
      :return:
          None on timeout or a :class:`can.Message` object.
      :raises can.CanError:
          if an error occurred while reading
