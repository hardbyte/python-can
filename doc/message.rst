Message
=======

The :class:`~can.Message` object is used to represent CAN messages. Instantiating
a CAN message (with default values for timestamp, arbitration ID, flags, and 
data) is done as follows:

    >>> from can import Message
    >>> test = Message()
    >>> print(test)
    0.000000        0000    0002    0
    >>> test2 = Message(data=[1,2,3,4,5])
    >>> print(test2)
    0.000000        0000    0002    5    01 02 03 04 05

The fields in the printed message are (in order): 
- timestamp, 
- arbitration ID, 
- flags, 
- dlc, 
- and data. 

The flags field is represented as a four-digit hexadecimal number. The arbitration
ID field as either a four or eight digit hexadecimal number depending on the length 
of the arbitration ID (11-bit or 29-bit). Each of the bytes in the data field (when
present) are represented as two-digit hexadecimal numbers. The following sections 
describe each of the parameters to the Message constructor.

Timestamp
---------

The timestamp field in a CAN message is a floating point number representing when
the message was received since the epoch in seconds. Where possible this will be
timestamped in hardware.


Arbitration ID
--------------

The arbitration ID field in a CAN message may be either 11 bits (standard
addressing, CAN 2.0A) or 29 bits (extended addressing, CAN 2.0B) in length, and
``python-can`` supports this by providing an ``extended_id`` parameter to the
Message constructor. The effect of this parameter is shown below.

The arbitration ID parameter itself can take an integer between 0 and the
maximum value allowed by the extended_id parameter passed to the Message
constructor (either 2\ :sup:`11` - 1 for 11-bit IDs, or 2\ :sup:`29` - 1 for
29-bit identifiers).

    >>> print(Message(extended_id=False))
    0.000000        0000    0002    0

    >>> print(Message(extended_id=True))
    0.000000    00000000    0004    0
    
    >>> print(Message(extended_id=False, arbitration_id=100))
    0.000000        0064    0002    0


is_remote_frame
---------------

This boolean attribute indicates if the message is a remote frame or a data frame, and
modifies the bit in the CAN message's flags field indicating this.

id_type
-------

This parameter controls the length of this CAN message's arbitration ID field.
It is covered in the `Arbitration ID`_ section of this document.


is_error_frame
--------------

This boolean parameter indicates if the message is an error frame or not.

DLC
---

The :abbr:`DLC (Data Link Count)` parameter of a CAN message is an integer
between 0 and 8. Its purpose varies depending on the frame type - for data
frames it represents the amount of data contained in the message, in remote
frames it represents the amount of data being requested from the device the
message is addressed to.

The default behaviour is to use the length of the data passed in.

    >>> print(Message(dlc=1))
    0.000000        0000    0002    1
    >>> print(Message(dlc=5))
    0.000000        0000    0002    5

.. note::
    The DLC value does not necessarily define the number of bytes of data
    in a packet.


Data
----

The data parameter of a CAN message is a **bytearray** (or list of ints) 
with length between 0 and 8.

    >>> example_data = bytearray([1,2,3])
    >>> print(Message(data=example_data))
    0.000000    00000000    0002    3    01 02 03
    >>> print(can.Message(data=[2,2]))
    0.000000    00000000    010    2    02 02
    >>> m = can.Message(data=[3])
    >>> m.data
    bytearray(b'\x03')


.. autoclass:: can.Message
    :members:
