Message
=======

.. module:: can

.. autoclass:: Message

    One can instantiate a :class:`~can.Message` defining data, and optional
    arguments for all attributes such as arbitration ID, flags, and timestamp.

        >>> from can import Message
        >>> test = Message(data=[1, 2, 3, 4, 5])
        >>> test.data
        bytearray(b'\x01\x02\x03\x04\x05')
        >>> test.dlc
        5
        >>> print(test)
        Timestamp:        0.000000    ID: 00000000    010    DLC: 5    01 02 03 04 05


    The :attr:`~can.Message.arbitration_id` field in a CAN message may be either
    11 bits (standard addressing, CAN 2.0A) or 29 bits (extended addressing, CAN
    2.0B) in length, and ``python-can`` exposes this difference with the
    :attr:`~can.Message.is_extended_id` attribute.

    .. attribute:: arbitration_id

        :type: int

        The frame identifier used for arbitration on the bus.

        The arbitration ID can take an int between 0 and the
        maximum value allowed depending on the is_extended_id flag
        (either 2\ :sup:`11` - 1 for 11-bit IDs, or
        2\ :sup:`29` - 1 for 29-bit identifiers).

            >>> print(Message(extended_id=False, arbitration_id=100))
            Timestamp:        0.000000        ID: 0064    000    DLC: 0


    .. attribute:: data

        :type: bytearray

        The data parameter of a CAN message is exposed as a **bytearray**
        with length between 0 and 8.

            >>> example_data = bytearray([1, 2, 3])
            >>> print(Message(data=example_data))
            0.000000    00000000    0002    3    01 02 03

        A :class:`~can.Message` can also be created with bytes, or lists of ints:

            >>> m1 = Message(data=[0x64, 0x65, 0x61, 0x64, 0x62, 0x65, 0x65, 0x66])
            >>> print(m1.data)
            bytearray(b'deadbeef')
            >>> m2 = can.Message(data=b'deadbeef')
            >>> m2.data
            bytearray(b'deadbeef')


    .. attribute:: dlc

        :type: int

        The :abbr:`DLC (Data Link Count)` parameter of a CAN message is an integer
        between 0 and 8 representing the frame payload length.

        >>> m = Message(data=[1, 2, 3])
        >>> m.dlc
        3

        .. note::

            The DLC value does not necessarily define the number of bytes of data
            in a message.

            Its purpose varies depending on the frame type - for data frames it
            represents the amount of data contained in the message, in remote
            frames it represents the amount of data being requested.


    .. attribute:: is_extended_id

        :type: bool

        This flag controls the size of the :attr:`~can.Message.arbitration_id` field.

        >>> print(Message(extended_id=False))
        Timestamp:        0.000000        ID: 0000    000    DLC: 0
        >>> print(Message(extended_id=True))
        Timestamp:        0.000000    ID: 00000000    010    DLC: 0


        Previously this was exposed as `id_type`.


    .. attribute:: is_error_frame

        :type: bool

        This boolean parameter indicates if the message is an error frame or not.


    .. attribute:: is_remote_frame

        :type: boolean

        This boolean attribute indicates if the message is a remote frame or a data frame, and
        modifies the bit in the CAN message's flags field indicating this.


    .. attribute:: timestamp

        :type: float

        The timestamp field in a CAN message is a floating point number representing when
        the message was received since the epoch in seconds. Where possible this will be
        timestamped in hardware.


    .. method:: __str__

        A string representation of a CAN message:

            >>> from can import Message
            >>> test = Message()
            >>> print(test)
            Timestamp:        0.000000    ID: 00000000    010    DLC: 0
            >>> test2 = Message(data=[1, 2, 3, 4, 5])
            >>> print(test2)
            Timestamp:        0.000000    ID: 00000000    010    DLC: 5    01 02 03 04 05

        The fields in the printed message are (in order):

        - timestamp,
        - arbitration ID,
        - flags,
        - dlc,
        - and data.


        The flags field is represented as a four-digit hexadecimal number. The arbitration
        ID field as either a four or eight digit hexadecimal number depending on the length
        of the arbitration ID (11-bit or 29-bit). Each of the bytes in the data field (when
        present) are represented as two-digit hexadecimal numbers.

