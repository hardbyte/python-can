.. _serial:

CAN over Serial
===============
A text based interface. For example use over serial ports like
``/dev/ttyS1`` or ``/dev/ttyUSB0`` on Linux machines or ``COM1`` on Windows.
Remote ports can be also used via a special URL. Both raw TCP sockets as
also RFC2217 ports are supported: ``socket://192.168.254.254:5000`` or
``rfc2217://192.168.254.254:5000``. In addition a virtual loopback can be
used via ``loop://`` URL.
The interface is a simple implementation that has been used for
recording CAN traces.

.. note::
    The properties **extended_id**, **is_remote_frame** and **is_error_frame**
    from the class:`~can.Message` are not in use. This interface will not
    send or receive flags for this properties.

Bus
---

.. autoclass:: can.interfaces.serial.serial_can.SerialBus

Internals
---------
The frames that will be sent and received over the serial interface consist of
six parts. The start and the stop byte for the frame, the timestamp, DLC,
arbitration ID and the payload. The payload has a variable length of between
0 and 8 bytes, the other parts are fixed. Both, the timestamp and the
arbitration ID will be interpreted as 4 byte unsigned integers. The DLC is
also an unsigned integer with a length of 1 byte.

Serial frame format
^^^^^^^^^^^^^^^^^^^
+-------------------+----------------+-----------------------------------------------+-------------------------------+-------------------------+---------+--------------+
|                   | Start of frame | Timestamp                                     | DLC                           | Arbitration ID          | Payload | End of frame |
+===================+================+==============================+================+===============================+=========================+=========+==============+
| **Length (Byte)** | 1              | 4                                             | 1                             | 4                       | 0 - 8   | 1            |
+-------------------+----------------+-----------------------------------------------+-------------------------------+-------------------------+---------+--------------+
| **Data type**     | Byte           | Unsigned 4 byte integer                       | Unsigned 1 byte integer       | Unsigned 4 byte integer | Byte    | Byte         |
+-------------------+----------------+-----------------------------------------------+-------------------------------+-------------------------+---------+--------------+
| **Byte order**    | \-             | Little-Endian                                 | Little-Endian                 | Little-Endian           | \-      | \-           |
+-------------------+----------------+-----------------------------------------------+-------------------------------+-------------------------+---------+--------------+
| **Description**   | Must be 0xAA   | Usually s, ms or µs since start of the device | Length in byte of the payload | \-                      | \-      | Must be 0xBB |
+-------------------+----------------+-----------------------------------------------+-------------------------------+-------------------------+---------+--------------+

Examples of serial frames
^^^^^^^^^^^^^^^^^^^^^^^^^

.. rubric:: CAN message with 8 byte payload

+----------------+-----------------------------------------+
| CAN message                                              |
+----------------+-----------------------------------------+
| Arbitration ID | Payload                                 |
+================+=========================================+
| 1              | 0x11 0x22 0x33 0x44 0x55 0x66 0x77 0x88 |
+----------------+-----------------------------------------+

+----------------+---------------------+------+---------------------+-----------------------------------------+--------------+
| Serial frame                                                                                                               |
+----------------+---------------------+------+---------------------+-----------------------------------------+--------------+
| Start of frame | Timestamp           | DLC  | Arbitration ID      | Payload                                 | End of frame |
+================+=====================+======+=====================+=========================================+==============+
| 0xAA           | 0x66 0x73 0x00 0x00 | 0x08 | 0x01 0x00 0x00 0x00 | 0x11 0x22 0x33 0x44 0x55 0x66 0x77 0x88 | 0xBB         |
+----------------+---------------------+------+---------------------+-----------------------------------------+--------------+

.. rubric:: CAN message with 1 byte payload

+----------------+---------+
| CAN message              |
+----------------+---------+
| Arbitration ID | Payload |
+================+=========+
| 1              | 0x11    |
+----------------+---------+

+----------------+---------------------+------+---------------------+---------+--------------+
| Serial frame                                                                               |
+----------------+---------------------+------+---------------------+---------+--------------+
| Start of frame | Timestamp           | DLC  | Arbitration ID      | Payload | End of frame |
+================+=====================+======+=====================+=========+==============+
| 0xAA           | 0x66 0x73 0x00 0x00 | 0x01 | 0x01 0x00 0x00 0x00 | 0x11    | 0xBB         |
+----------------+---------------------+------+---------------------+---------+--------------+

.. rubric:: CAN message with 0 byte payload

+----------------+---------+
| CAN message              |
+----------------+---------+
| Arbitration ID | Payload |
+================+=========+
| 1              | None    |
+----------------+---------+

+----------------+---------------------+------+---------------------+--------------+
| Serial frame                                                                     |
+----------------+---------------------+------+---------------------+--------------+
| Start of frame | Timestamp           | DLC  | Arbitration ID      | End of frame |
+================+=====================+======+=====================+==============+
| 0xAA           | 0x66 0x73 0x00 0x00 | 0x00 | 0x01 0x00 0x00 0x00 | 0xBBS        |
+----------------+---------------------+------+---------------------+--------------+
