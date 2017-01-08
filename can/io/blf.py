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
from can.CAN import Listener


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

# channel, length
CAN_ERROR_STRUCT = struct.Struct("<HH4x")

# commented event type, foreground color, background color, relocatable,
# group name length, marker name length, description length
GLOBAL_MARKER_STRUCT = struct.Struct("<LLL3xBLLL12x")


CAN_MESSAGE = 1
CAN_ERROR = 2
LOG_CONTAINER = 10
GLOBAL_MARKER = 96

CAN_MSG_EXT = 0x80000000
REMOTE_FLAG = 0x80


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
        self.start_timestamp = systemtime_to_timestamp(header[14:22])

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
                    header = OBJ_HEADER_STRUCT.unpack(
                        data[pos:pos + OBJ_HEADER_STRUCT.size])
                    #print(header)
                    assert header[0] == b"LOBJ", "Parse error"
                    obj_size = header[3]
                    if pos + obj_size > len(data):
                        # Object continues in next log container
                        break
                    obj_data = data[pos + OBJ_HEADER_STRUCT.size:pos + obj_size]
                    obj_type = header[4]
                    timestamp = header[7] / 1000000000.0 + self.start_timestamp
                    if obj_type == CAN_MESSAGE:
                        (channel, flags, dlc, can_id,
                         can_data) = CAN_MSG_STRUCT.unpack(obj_data)
                        msg = Message(timestamp=timestamp,
                                      arbitration_id=can_id & 0x1FFFFFFF,
                                      extended_id=bool(can_id & CAN_MSG_EXT),
                                      is_remote_frame=bool(flags & REMOTE_FLAG),
                                      dlc=dlc,
                                      data=can_data[:dlc])
                        msg.channel = channel
                        yield msg
                    elif obj_type == CAN_ERROR:
                        channel, length = CAN_ERROR_STRUCT.unpack(obj_data)
                        msg = Message(timestamp=timestamp, is_error_frame=True)
                        msg.channel = channel
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
    COMPRESSION_LEVEL = 7

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
        if self.start_timestamp is None:
            self.start_timestamp = msg.timestamp
        self.stop_timestamp = msg.timestamp
        timestamp = int((msg.timestamp - self.start_timestamp) * 1000000000)
        if not msg.is_error_frame:
            obj_size = OBJ_HEADER_STRUCT.size + CAN_MSG_STRUCT.size
            header = OBJ_HEADER_STRUCT.pack(
                b"LOBJ", OBJ_HEADER_STRUCT.size, 1, obj_size, CAN_MESSAGE,
                2, 0, timestamp)
            flags = REMOTE_FLAG if msg.is_remote_frame else 0
            arb_id = msg.arbitration_id
            if msg.id_type:
                arb_id |= CAN_MSG_EXT
            data = CAN_MSG_STRUCT.pack(self.channel, flags, msg.dlc, arb_id,
                                       bytes(msg.data))
        else:
            obj_size = OBJ_HEADER_STRUCT.size + CAN_ERROR_STRUCT.size
            header = OBJ_HEADER_STRUCT.pack(
                b"LOBJ", OBJ_HEADER_STRUCT.size, 1, obj_size, CAN_ERROR,
                2, 0, timestamp)
            data = CAN_ERROR_STRUCT.pack(self.channel, 0)
        self._add_data(header + data)

    def log_event(self, text, timestamp=None):
        """Add an arbitrary message to the log file as a global marker.

        :param str text:
            The group name of the marker.
        :param float timestamp:
            Absolute timestamp in Unix timestamp format. If not given, the
            marker will be placed along the last message.
        """
        if timestamp is None:
            timestamp = self.stop_timestamp
        if self.start_timestamp is None:
            self.start_timestamp = timestamp
        self.stop_timestamp = timestamp
        try:
            # Only works on Windows
            text = text.encode("mbcs")
        except LookupError:
            text = text.encode("ascii")
        timestamp = int((timestamp - self.start_timestamp) * 1000000000)
        comment = b"Added by python-can"
        marker = b"python-can"
        obj_size = (OBJ_HEADER_STRUCT.size + GLOBAL_MARKER_STRUCT.size +
                    len(text) + len(marker) + len(comment))
        header = OBJ_HEADER_STRUCT.pack(
            b"LOBJ", OBJ_HEADER_STRUCT.size, 1, obj_size, GLOBAL_MARKER,
            2, 0, timestamp)
        data = GLOBAL_MARKER_STRUCT.pack(
            0, 0xFFFFFF, 0xFF3300, 0, len(text), len(marker), len(comment))
        self._add_data(header + data + text + marker + comment)

    def _add_data(self, data):
        if len(data) % 4:
            data = data + b"\x00" * (len(data) % 4)
        self.cache.append(data)
        self.cache_size += len(data)
        self.count_of_objects += 1
        if self.cache_size >= self.MAX_CACHE_SIZE:
            self._flush()

    def _flush(self):
        """Compresses and writes data in the cache to file."""
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
