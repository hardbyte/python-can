"""
Implements support for BLF (Binary Logging Format) which is a proprietary
CAN log format from Vector Informatik GmbH.

No official specification of the binary logging format is available.
This implementation is based on Toby Lorenz' C++ library "Vector BLF" which is
licenced under GPLv3. https://bitbucket.org/tobylorenz/vector_blf.
The file starts with a header. The rest is one or more "log containers"
which consists of a header and some zlib compressed data, usually up to 128 kB
of uncompressed data each. This data contains the actual CAN messages and other
objects types.
"""

import struct
import zlib
import datetime
import time

from can.message import Message
from can.listener import Listener


# 0 = unknown, 2 = CANoe
APPLICATION_ID = 5

# Header must be 144 bytes in total
# signature ("LOGG"), header size,
# application ID, application major, application minor, application build,
# bin log major, bin log minor, bin log build, bin log patch,
# file size, uncompressed size, count of objects, count of objects read,
# time start (SYSTEMTIME), time stop (SYSTEMTIME)
FILE_HEADER_STRUCT = struct.Struct("<4sLBBBBBBBBQQLL8H8H72x")

# signature ("LOBJ"), header size, header version (1), object size, object type,
# flags, object version, size uncompressed or timestamp
OBJ_HEADER_STRUCT = struct.Struct("<4sHHLLL2xHQ")

# channel, flags, dlc, arbitration id, data
CAN_MSG_STRUCT = struct.Struct("<HBBL8s")

# channel, flags, dlc, arbitration id, frame length, bit count, FD flags,
# valid data bytes, data
CAN_FD_MSG_STRUCT = struct.Struct("<HBBLLBBB5x64s")

# channel, length
CAN_ERROR_STRUCT = struct.Struct("<HH4x")

# commented event type, foreground color, background color, relocatable,
# group name length, marker name length, description length
GLOBAL_MARKER_STRUCT = struct.Struct("<LLL3xBLLL12x")


CAN_MESSAGE = 1
CAN_ERROR = 2
LOG_CONTAINER = 10
GLOBAL_MARKER = 96
CAN_FD_MESSAGE = 100

CAN_MSG_EXT = 0x80000000
REMOTE_FLAG = 0x80
EDL = 0x1
BRS = 0x2
ESI = 0x4


def timestamp_to_systemtime(timestamp):
    if timestamp is None or timestamp < 631152000:
        # Probably not a Unix timestamp
        return (0, 0, 0, 0, 0, 0, 0, 0)
    t = datetime.datetime.fromtimestamp(timestamp)
    return (t.year, t.month, t.isoweekday() % 7, t.day,
            t.hour, t.minute, t.second, int(round(t.microsecond / 1000.0)))


def systemtime_to_timestamp(systemtime):
    try:
        t = datetime.datetime(
            systemtime[0], systemtime[1], systemtime[3],
            systemtime[4], systemtime[5], systemtime[6], systemtime[7] * 1000)
        return time.mktime(t.timetuple()) + systemtime[7] / 1000.0
    except ValueError:
        return 0


class BLFReader(object):
    """
    Iterator of CAN messages from a Binary Logging File.

    Only CAN messages and error frames are supported. Other object types are
    silently ignored.
    """

    def __init__(self, filename):
        self.fp = open(filename, "rb")
        data = self.fp.read(FILE_HEADER_STRUCT.size)
        header = FILE_HEADER_STRUCT.unpack(data)
        #print(header)
        assert header[0] == b"LOGG", "Unknown file format"
        self.file_size = header[10]
        self.uncompressed_size = header[11]
        self.object_count = header[12]
        self.start_timestamp = systemtime_to_timestamp(header[14:22])
        self.stop_timestamp = systemtime_to_timestamp(header[22:30])

    def __iter__(self):
        tail = b""
        while True:
            data = self.fp.read(OBJ_HEADER_STRUCT.size)
            if not data:
                # EOF
                break
            header = OBJ_HEADER_STRUCT.unpack(data)
            #print(header)
            assert header[0] == b"LOBJ", "Parse error"
            obj_type = header[4]
            obj_data_size = header[3] - OBJ_HEADER_STRUCT.size
            obj_data = self.fp.read(obj_data_size)
            # Read padding bytes
            self.fp.read(obj_data_size % 4)
            if obj_type == LOG_CONTAINER:
                uncompressed_size = header[7]
                data = zlib.decompress(obj_data, 15, uncompressed_size)
                if tail:
                    data = tail + data
                pos = 0
                while pos + OBJ_HEADER_STRUCT.size < len(data):
                    header = OBJ_HEADER_STRUCT.unpack_from(data, pos)
                    #print(header)
                    assert header[0] == b"LOBJ", "Parse error"
                    obj_size = header[3]
                    if pos + obj_size > len(data):
                        # Object continues in next log container
                        break
                    obj_type = header[4]
                    timestamp = header[7] / 1000000000.0 + self.start_timestamp
                    if obj_type == CAN_MESSAGE:
                        assert obj_size == OBJ_HEADER_STRUCT.size + CAN_MSG_STRUCT.size
                        (channel, flags, dlc, can_id,
                         can_data) = CAN_MSG_STRUCT.unpack_from(
                             data, pos + OBJ_HEADER_STRUCT.size)
                        msg = Message(timestamp=timestamp,
                                      arbitration_id=can_id & 0x1FFFFFFF,
                                      extended_id=bool(can_id & CAN_MSG_EXT),
                                      is_remote_frame=bool(flags & REMOTE_FLAG),
                                      dlc=dlc,
                                      data=can_data[:dlc],
                                      channel=channel)
                        yield msg
                    elif obj_type == CAN_FD_MESSAGE:
                        assert obj_size == OBJ_HEADER_STRUCT.size + CAN_FD_MSG_STRUCT.size
                        (channel, flags, dlc, can_id, _, _, fd_flags,
                         valid_bytes, can_data) = CAN_FD_MSG_STRUCT.unpack_from(
                             data, pos + OBJ_HEADER_STRUCT.size)
                        msg = Message(timestamp=timestamp,
                                      arbitration_id=can_id & 0x1FFFFFFF,
                                      extended_id=bool(can_id & CAN_MSG_EXT),
                                      is_remote_frame=bool(flags & REMOTE_FLAG),
                                      is_fd=bool(fd_flags & EDL),
                                      bitrate_switch=bool(fd_flags & BRS),
                                      error_state_indicator=bool(fd_flags & ESI),
                                      dlc=dlc,
                                      data=can_data[:valid_bytes],
                                      channel=channel)
                        yield msg
                    elif obj_type == CAN_ERROR:
                        assert obj_size == OBJ_HEADER_STRUCT.size + CAN_ERROR_STRUCT.size
                        channel, length = CAN_ERROR_STRUCT.unpack_from(
                            data, pos + OBJ_HEADER_STRUCT.size)
                        msg = Message(timestamp=timestamp, is_error_frame=True,
                                      channel=channel)
                        yield msg
                    pos += obj_size
                    # Add padding bytes
                    pos += obj_size % 4
                # Save remaing data that could not be processed
                tail = data[pos:]
        self.fp.close()


class BLFWriter(Listener):
    """
    Logs CAN data to a Binary Logging File compatible with Vector's tools.
    """

    #: Max log container size of uncompressed data
    MAX_CACHE_SIZE = 0x20000

    #: ZLIB compression level
    COMPRESSION_LEVEL = 9

    def __init__(self, filename, channel=1):
        self.fp = open(filename, "wb")
        self.channel = channel
        # Header will be written after log is done
        self.fp.write(b"\x00" * FILE_HEADER_STRUCT.size)
        self.cache = []
        self.cache_size = 0
        self.count_of_objects = 0
        self.uncompressed_size = FILE_HEADER_STRUCT.size
        self.start_timestamp = None
        self.stop_timestamp = None

    def on_message_received(self, msg):
        channel = msg.channel if isinstance(msg.channel, int) else self.channel
        if msg.is_error_frame:
            data = CAN_ERROR_STRUCT.pack(channel, 0)
            self._add_object(CAN_ERROR, data, msg.timestamp)
        else:
            flags = REMOTE_FLAG if msg.is_remote_frame else 0
            arb_id = msg.arbitration_id
            if msg.id_type:
                arb_id |= CAN_MSG_EXT
            if msg.is_fd:
                fd_flags = EDL
                if msg.bitrate_switch:
                    fd_flags |= BRS
                if msg.error_state_indicator:
                    fd_flags |= ESI
                data = CAN_FD_MSG_STRUCT.pack(channel, flags, msg.dlc, arb_id,
                                              0, 0, fd_flags, msg.dlc,
                                              bytes(msg.data))
                self._add_object(CAN_FD_MESSAGE, data, msg.timestamp)
            else:
                data = CAN_MSG_STRUCT.pack(channel, flags, msg.dlc, arb_id,
                                           bytes(msg.data))
                self._add_object(CAN_MESSAGE, data, msg.timestamp)

    def log_event(self, text, timestamp=None):
        """Add an arbitrary message to the log file as a global marker.

        :param str text:
            The group name of the marker.
        :param float timestamp:
            Absolute timestamp in Unix timestamp format. If not given, the
            marker will be placed along the last message.
        """
        try:
            # Only works on Windows
            text = text.encode("mbcs")
        except LookupError:
            text = text.encode("ascii")
        comment = b"Added by python-can"
        marker = b"python-can"
        data = GLOBAL_MARKER_STRUCT.pack(
            0, 0xFFFFFF, 0xFF3300, 0, len(text), len(marker), len(comment))
        self._add_object(GLOBAL_MARKER, data + text + marker + comment, timestamp)

    def _add_object(self, obj_type, data, timestamp=None):
        if timestamp is None:
            timestamp = self.stop_timestamp or time.time()
        if self.start_timestamp is None:
            self.start_timestamp = timestamp
        self.stop_timestamp = timestamp
        timestamp = int((timestamp - self.start_timestamp) * 1000000000)
        obj_size = OBJ_HEADER_STRUCT.size + len(data)
        header = OBJ_HEADER_STRUCT.pack(
            b"LOBJ", OBJ_HEADER_STRUCT.size, 1, obj_size, obj_type,
            2, 0, max(timestamp, 0))
        self.cache.append(header)
        self.cache.append(data)
        padding_size = len(data) % 4
        if padding_size:
            self.cache.append(b"\x00" * padding_size)
        self.cache_size += obj_size + padding_size
        self.count_of_objects += 1
        if self.cache_size >= self.MAX_CACHE_SIZE:
            self._flush()

    def _flush(self):
        """Compresses and writes data in the cache to file."""
        if self.fp.closed:
            return
        cache = b"".join(self.cache)
        if not cache:
            # Nothing to write
            return
        uncompressed_data = cache[:self.MAX_CACHE_SIZE]
        # Save data that comes after max size to next round
        tail = cache[self.MAX_CACHE_SIZE:]
        self.cache = [tail]
        self.cache_size = len(tail)
        compressed_data = zlib.compress(uncompressed_data,
                                        self.COMPRESSION_LEVEL)
        obj_size = OBJ_HEADER_STRUCT.size + len(compressed_data)
        header = OBJ_HEADER_STRUCT.pack(
            b"LOBJ", 16, 1, obj_size, LOG_CONTAINER, 2, 0, len(uncompressed_data))
        self.fp.write(header)
        self.fp.write(compressed_data)
        # Write padding bytes
        self.fp.write(b"\x00" * (obj_size % 4))
        self.uncompressed_size += len(uncompressed_data) + OBJ_HEADER_STRUCT.size

    def stop(self):
        """Stops logging and closes the file."""
        if self.fp.closed:
            return
        self._flush()
        filesize = self.fp.tell()
        self.fp.close()

        # Write header in the beginning of the file
        header = [b"LOGG", FILE_HEADER_STRUCT.size,
                  APPLICATION_ID, 0, 0, 0, 2, 6, 8, 1]
        # The meaning of "count of objects read" is unknown
        header.extend([filesize, self.uncompressed_size,
                       self.count_of_objects, 0])
        header.extend(timestamp_to_systemtime(self.start_timestamp))
        header.extend(timestamp_to_systemtime(self.stop_timestamp))
        with open(self.fp.name, "r+b") as f:
            f.write(FILE_HEADER_STRUCT.pack(*header))
