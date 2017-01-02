"""
Implements support for BLF (Binary Logging Format) which is a proprietary
CAN log format from Vector Informatik GmbH.

No offical specification is available. The file starts with a 144 byte header.
It contains some info that is not known until the log has stopped so it will
have to be written last. The rest is one or more "log containers" which consists
of a header and some zlib compressed data, usually up to 128 kB of uncompressed
data each. This data contains the actual CAN messages.
"""
import logging
import struct
import zlib
import datetime
import time

from can.message import Message
from can.CAN import Listener


logger = logging.getLogger(__name__)


APPLICATION_ID = 5
HEADER_SIZE = 144
# File header consists of:
# signature ("LOGG"), header size,
# application ID, application major, application minor, application build,
# bin log major, bin log minor, bin log build, bin log patch,
# file size, uncompressed size, count of objects, count of objects read,
# time start (SYSTEMTIME), time stop (SYSTEMTIME)
FILE_HEADER_STRUCT = struct.Struct("<4sLBBBBBBBBQQLL8H8H")
# signature ("LOBJ"), header size, header version (1), object size, object type,
# flags, object version, size uncompressed/timestamp
OBJ_HEADER_STRUCT = struct.Struct("<4sHHLLL2xHQ")
# channel, flags, dlc, arbitration id, data
CAN_STRUCT = struct.Struct("<HBBL8s")

LOG_CONTAINER = 10
CAN_MESSAGE = 1
CAN_MSG_EXT = 0x80000000
REMOTE_FLAG = 0x1


def timestamp_to_systemtime(timestamp):
    t = datetime.datetime.fromtimestamp(timestamp)
    return (t.year, t.month, t.isoweekday() % 7, t.day,
            t.hour, t.minute, t.second, t.microsecond // 1000)


def systemtime_to_timestamp(systemtime):
    t = datetime.datetime(
        systemtime[0], systemtime[1], systemtime[3],
        systemtime[4], systemtime[5], systemtime[6], systemtime[7] * 1000)
    return time.mktime(t.timetuple()) + systemtime[7] / 1000.0


class BLFReader(object):
    """
    Iterator of CAN messages from a Binary Logging File.
    """

    def __init__(self, filename):
        self.fp = open(filename, "rb")
        data = self.fp.read(HEADER_SIZE)
        header = FILE_HEADER_STRUCT.unpack_from(data)
        #print(header)
        assert header[0] == b"LOGG", "Unknown file format"
        self.start_timestamp = systemtime_to_timestamp(header[14:22])

    def __iter__(self):
        tail = b""
        while True:
            data = self.fp.read(OBJ_HEADER_STRUCT.size)
            if not data:
                break
            header = OBJ_HEADER_STRUCT.unpack(data)
            #print(header)
            assert header[0] == b"LOBJ", "Parse error"
            obj_type = header[4]
            if obj_type == LOG_CONTAINER:
                compressed_size = header[3] - OBJ_HEADER_STRUCT.size
                uncompressed_size = header[7]
                compressed_data = self.fp.read(compressed_size)
                data = zlib.decompress(compressed_data, 15, uncompressed_size)
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
                    obj_type = header[4]
                    if obj_type == CAN_MESSAGE:
                        timestamp = header[7] / 1000000000.0 + self.start_timestamp
                        channel, flags, dlc, can_id, can_data = CAN_STRUCT.unpack(
                            data[pos + OBJ_HEADER_STRUCT.size:pos + obj_size])
                        yield Message(timestamp=timestamp,
                                      arbitration_id=can_id & 0x1FFFFFFF,
                                      extended_id=bool(can_id & CAN_MSG_EXT),
                                      is_remote_frame=bool(flags & REMOTE_FLAG),
                                      dlc=dlc,
                                      data=can_data[:dlc])
                    pos += obj_size
                    # Add padding bytes
                    pos += obj_size % 4
                # Save remaing data that could not be processed
                tail = data[pos:]
                if compressed_size % 4:
                    self.fp.read(compressed_size % 4)
        self.fp.close()


class BLFWriter(Listener):
    """
    Logs CAN data to a Binary Logging File compatible with Vector's tools.

    The data is stored in a compressed format which makes it very compact.
    """

    #: Max log container size of uncompressed data
    MAX_CACHE_SIZE = 0x20000

    #: ZLIB compression level
    COMPRESSION_LEVEL = 7

    def __init__(self, filename, channel=1):
        self.fp = open(filename, "w+b")
        self.channel = channel
        # Header will be written after log is done
        self.fp.write(b"\x00" * HEADER_SIZE)
        self.cache = []
        self.cache_size = 0
        self.count_of_objects = 0
        self.uncompressed_size = HEADER_SIZE
        self.start_timestamp = None
        self.stop_timestamp = None

    def on_message_received(self, msg):
        if self.start_timestamp is None:
            self.start_timestamp = msg.timestamp
        self.stop_timestamp = msg.timestamp
        timestamp = int((msg.timestamp - self.start_timestamp) * 1000000000)
        header = OBJ_HEADER_STRUCT.pack(
            b"LOBJ", 32, 1, OBJ_HEADER_STRUCT.size + CAN_STRUCT.size,
            CAN_MESSAGE, 2, 0, timestamp)
        flags = REMOTE_FLAG if msg.is_remote_frame else 0
        arb_id = msg.arbitration_id
        if msg.id_type:
            arb_id |= CAN_MSG_EXT
        data = CAN_STRUCT.pack(self.channel, flags, msg.dlc, arb_id,
                               bytes(msg.data))
        self.cache.append(header)
        self.cache.append(data)
        self.cache_size += OBJ_HEADER_STRUCT.size + CAN_STRUCT.size
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
            b"LOBJ", 16, 1, obj_size,
            LOG_CONTAINER, 2, 0, len(uncompressed_data))
        self.fp.write(header)
        self.fp.write(compressed_data)
        # Write padding bytes
        self.fp.write(b"\x00" * (len(compressed_data) % 4))
        self.uncompressed_size += len(uncompressed_data) + OBJ_HEADER_STRUCT.size

    def stop(self):
        self._flush()
        # Write header
        header = [b"LOGG", HEADER_SIZE, APPLICATION_ID, 0, 0, 0, 1, 1, 8, 0]
        # TODO: What is "count of objects read"? Set to 0 for now
        header.extend([self.fp.tell(), self.uncompressed_size,
                       self.count_of_objects, 0])
        now = time.time()
        header.extend(timestamp_to_systemtime(self.start_timestamp or now))
        header.extend(timestamp_to_systemtime(self.stop_timestamp or now))
        self.fp.seek(0)
        self.fp.write(FILE_HEADER_STRUCT.pack(*header))
        self.fp.close()
