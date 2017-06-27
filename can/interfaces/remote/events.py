"""
Different events can be sent and transmitted over the network connection.

Examples:
  * Messages
  * Exceptions
  * Transmit success
  * Transmit failure
  * ...
"""

import struct
import logging
import can

logger = logging.getLogger(__name__)

EXTENDED_BIT = 0x80000000


class BaseEvent(object):
    """Events should inherit this class."""

    def encode(self):
        """Convert event data to bytes.

        :return:
            Bytestring representing the event data.
        :rtype: bytes
        """
        return b''

    @classmethod
    def from_buffer(cls, buf):
        """Parse the data and return a new event.

        :param bytes buf:
            Bytestring representing the event data.

        :return:
            Event decoded from buffer.

        :raise can.interfaces.remote.events.NeedMoreDataError:
            If not enough data exists.
        """
        return cls()

    def __len__(self):
        return len(self.encode())

    # Useful for tests
    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.__dict__ == other.__dict__)


class BusRequest(BaseEvent):
    """Request for connecting to CAN bus.

    +--------+-------+--------------------------------------------------------+
    | Byte   | Type  | Contents                                               |
    +========+=======+========================================================+
    | 0      | U8    | Protocol version used by client                        |
    +--------+-------+--------------------------------------------------------+
    | 1 - 4  | S32   | Bitrate in bits/s requested                            |
    +--------+-------+--------------------------------------------------------+
    """

    #: Event ID
    EVENT_ID = 1

    _STRUCT = struct.Struct('>Bl')

    def __init__(self, version, bitrate):
        """
        :param int version:
            Network protocol version
        :param int bitrate:
            Bitrate to use on CAN
        """
        #: Network protocol version
        self.version = version
        #: Bitrate in bits/s
        self.bitrate = bitrate

    def encode(self):
        return self._STRUCT.pack(self.version, self.bitrate)

    @classmethod
    def from_buffer(cls, buf):
        try:
            version, bitrate = cls._STRUCT.unpack_from(buf)
        except struct.error:
            raise NeedMoreDataError()

        return cls(version, bitrate)

    def __len__(self):
        return self._STRUCT.size


class BusResponse(BaseEvent):
    """Response after connected to CAN bus.

    +--------+-------+--------------------------------------------------------+
    | Byte   | Type  | Contents                                               |
    +========+=======+========================================================+
    | 0      | U8    | Length of channel info string                          |
    +--------+-------+--------------------------------------------------------+
    | 1 - x  | STR   | Channel info (UTF-8)                                   |
    +--------+-------+--------------------------------------------------------+
    """

    #: Event ID
    EVENT_ID = 2

    def __init__(self, channel_info):
        """
        :param str channel_info:
            Text describing the channel
        """
        #: Text describing the channel
        self.channel_info = channel_info

    def encode(self):
        data = self.channel_info.encode('utf-8')
        length = struct.pack('B', len(data))
        return length + data

    @classmethod
    def from_buffer(cls, buf):
        try:
            length, = struct.unpack_from('B', buf)
        except struct.error:
            raise NeedMoreDataError()

        if len(buf) < 1 + length:
            raise NeedMoreDataError()

        channel_info = buf[1:1+length].decode('utf-8')
        return cls(channel_info)


class CanMessage(BaseEvent):
    """CAN message being received or transmitted.

    +--------+-------+--------------------------------------------------------+
    | Byte   | Type  | Contents                                               |
    +========+=======+========================================================+
    | 0 - 7  | F64   | Timestamp                                              |
    +--------+-------+--------------------------------------------------------+
    | 8 - 11 | U32   | Arbitration ID                                         |
    +--------+-------+--------------------------------------------------------+
    | 12     | U8    | DLC                                                    |
    +--------+-------+--------------------------------------------------------+
    | 13     | U8    | Flags:                                                 |
    |        |       |  - Bit 0: Extended ID                                  |
    |        |       |  - Bit 1: Remote frame                                 |
    |        |       |  - Bit 2: Error frame                                  |
    +--------+-------+--------------------------------------------------------+
    | 14 - 21| U8    | Data padded to an 8 byte array                         |
    +--------+-------+--------------------------------------------------------+
    """

    #: Event ID
    EVENT_ID = 3

    _STRUCT = struct.Struct('>dlBB8s')
    _EXT_FLAG = 0x1
    _REMOTE_FRAME_FLAG = 0x2
    _ERROR_FRAME_FLAG = 0x4

    def __init__(self, msg):
        """
        :param can.Message msg:
            A Message object.
        """
        #: A :class:`can.Message` instance.
        self.msg = msg

    def encode(self):
        flags = 0
        if self.msg.id_type:
            flags |= self._EXT_FLAG
        if self.msg.is_remote_frame:
            flags |= self._REMOTE_FRAME_FLAG
        if self.msg.is_error_frame:
            flags |= self._ERROR_FRAME_FLAG
        buf = self._STRUCT.pack(self.msg.timestamp,
                                self.msg.arbitration_id,
                                self.msg.dlc,
                                flags,
                                bytes(self.msg.data))
        return buf

    @classmethod
    def from_buffer(cls, buf):
        try:
            timestamp, arb_id, dlc, flags, data = cls._STRUCT.unpack_from(buf)
        except struct.error:
            raise NeedMoreDataError()

        msg = can.Message(timestamp=timestamp,
                          arbitration_id=arb_id,
                          extended_id=bool(flags & cls._EXT_FLAG),
                          is_remote_frame=bool(flags & cls._REMOTE_FRAME_FLAG),
                          is_error_frame=bool(flags & cls._ERROR_FRAME_FLAG),
                          dlc=dlc,
                          data=data[:dlc])
        return cls(msg)

    def __len__(self):
        return self._STRUCT.size


class TransmitSuccess(BaseEvent):
    """A message has been successfully transmitted to CAN."""

    #: Event ID
    EVENT_ID = 4


class TransmitFail(BaseEvent):
    """A message failed to be transmitted to CAN."""

    #: Event ID
    EVENT_ID = 5


class RemoteException(BaseEvent):
    """An exception has occurred on the server.

    +--------+-------+--------------------------------------------------------+
    | Byte   | Type  | Contents                                               |
    +========+=======+========================================================+
    | 0      | U8    | Length of exception string                             |
    +--------+-------+--------------------------------------------------------+
    | 1 - x  | STR   | Exception description (UTF-8)                          |
    +--------+-------+--------------------------------------------------------+
    """

    #: Event ID
    EVENT_ID = 6

    def __init__(self, exc):
        """
        :param Exception exc:
            The exception to send.
        """
        #: The exception
        self.exc = exc

    def encode(self):
        data = str(self.exc).encode('utf-8')
        length = struct.pack('B', len(data))
        return length + data

    @classmethod
    def from_buffer(cls, buf):
        try:
            length, = struct.unpack_from('B', buf)
        except struct.error:
            raise NeedMoreDataError()

        if len(buf) - 1 < length:
            raise NeedMoreDataError()

        text = buf[1:1+length].decode('utf-8')
        return cls(can.CanError(text))


class PeriodicMessageStart(BaseEvent):
    """Start periodic transmission of message.

    +--------+-------+--------------------------------------------------------+
    | Byte   | Type  | Contents                                               |
    +========+=======+========================================================+
    | 0 - 3  | U32   | Period (ms)                                            |
    +--------+-------+--------------------------------------------------------+
    | 4 - 7  | U32   | Duration (ms)                                          |
    +--------+-------+--------------------------------------------------------+
    | 8 - 11 | U32   | Arbitration ID                                         |
    +--------+-------+--------------------------------------------------------+
    | 12     | U8    | DLC                                                    |
    +--------+-------+--------------------------------------------------------+
    | 13     | U8    | Extended ID                                            |
    +--------+-------+--------------------------------------------------------+
    | 14 - 21| U8    | Data padded to an 8 byte array                         |
    +--------+-------+--------------------------------------------------------+
    """

    #: Event ID
    EVENT_ID = 7

    _STRUCT = struct.Struct('>lllBB8s')

    def __init__(self, msg, period, duration=None):
        """
        :param can.Message msg:
            A Message object.
        :param float period:
            Period of message in seconds.
        """
        #: A :class:`can.Message` instance.
        self.msg = msg
        self.period = period
        self.duration = duration

    def encode(self):
        duration = int(self.duration * 1000) if self.duration is not None else 0
        buf = self._STRUCT.pack(int(self.period * 1000),
                                duration,
                                self.msg.arbitration_id,
                                self.msg.dlc,
                                self.msg.id_type,
                                bytes(self.msg.data))
        return buf

    @classmethod
    def from_buffer(cls, buf):
        try:
            (period, duration, arb_id, dlc, extended,
             data) = cls._STRUCT.unpack_from(buf)
        except struct.error:
            raise NeedMoreDataError()

        msg = can.Message(arbitration_id=arb_id,
                          extended_id=extended,
                          dlc=dlc,
                          data=data[:dlc])
        duration = duration / 1000.0 if duration > 0 else None
        return cls(msg, period / 1000.0, duration)

    def __len__(self):
        return self._STRUCT.size


class PeriodicMessageStop(BaseEvent):
    """Stop periodic transmission of a message.

    +--------+-------+--------------------------------------------------------+
    | Byte   | Type  | Contents                                               |
    +========+=======+========================================================+
    | 0 - 4  | U32   | Arbitration ID                                         |
    +--------+-------+--------------------------------------------------------+
    """

    #: Event ID
    EVENT_ID = 8

    _STRUCT = struct.Struct('>l')

    def __init__(self, arbitration_id):
        """
        :param int arbitration_id:
            The CAN-ID of the message to stop sending.
        """
        #: The arbitration ID of the message to stop transmitting
        self.arbitration_id = arbitration_id

    def encode(self):
        return self._STRUCT.pack(self.arbitration_id)

    @classmethod
    def from_buffer(cls, buf):
        try:
            arbitration_id, = cls._STRUCT.unpack_from(buf)
        except struct.error:
            raise NeedMoreDataError()
        return cls(arbitration_id)

    def __len__(self):
        return self._STRUCT.size


class FilterConfig(BaseEvent):
    """CAN filter configuration.

    +--------+-------+--------------------------------------------------------+
    | Byte   | Type  | Contents                                               |
    +========+=======+========================================================+
    | 0      | U8    | Number of filters                                      |
    +--------+-------+--------------------------------------------------------+
    | 1 - 4  | U32   | CAN ID for filter 1 (bit 31 set if extended)           |
    +--------+-------+--------------------------------------------------------+
    | 5 - 8  | U32   | CAN mask for filter 1 (bit 31 set if extended or std)  |
    +--------+-------+--------------------------------------------------------+
    | 9 - 12 | U32   | CAN ID for filter 2                                    |
    +--------+-------+--------------------------------------------------------+
    | 13 - 16| U32   | CAN mask for filter 2                                  |
    +--------+-------+--------------------------------------------------------+
    | ...    | ...   | ...                                                    |
    +--------+-------+--------------------------------------------------------+
    """

    #: Event ID
    EVENT_ID = 10
    _STRUCT = struct.Struct('>LL')

    def __init__(self, can_filters=None):
        """
        :param list can_filters:
            List of CAN filters
        """
        #: A list of CAN filter dictionaries as:
        #: >>    {'can_id': 0x03, 'can_mask': 0xff}
        self.can_filters = can_filters or []

    def encode(self):
        data = [struct.pack('B', len(self.can_filters))]
        for can_filter in self.can_filters:
            can_id = can_filter['can_id']
            can_mask = can_filter['can_mask']
            if 'extended' in can_filter:
                can_mask |= EXTENDED_BIT
                if can_filter['extended']:
                    can_id |= EXTENDED_BIT
            filter_data = self._STRUCT.pack(can_id, can_mask)
            data.append(filter_data)
        return b''.join(data)

    @classmethod
    def from_buffer(cls, buf):
        can_filters = []
        try:
            nof_filters, = struct.unpack_from('B', buf)
            for i in range(nof_filters):
                offset = 1 + i * cls._STRUCT.size
                can_id, can_mask = cls._STRUCT.unpack_from(buf, offset)
                can_filter = {
                    'can_id': can_id & 0x1FFFFFFF,
                    'can_mask': can_mask & 0x1FFFFFFF
                }
                if can_mask & EXTENDED_BIT:
                    can_filter['extended'] = bool(can_id & EXTENDED_BIT)
                can_filters.append(can_filter)
        except struct.error:
            raise NeedMoreDataError()

        return cls(can_filters)

    def __len__(self):
        return 1 + self._STRUCT.size * len(self.can_filters)

class ConnectionClosed(BaseEvent):
    """Connection closed by peer.

    Will be automatically emitted if the socket is closed.
    """

    #: Event ID
    EVENT_ID = 255


class NeedMoreDataError(Exception):
    """There is not enough data yet."""
    pass
