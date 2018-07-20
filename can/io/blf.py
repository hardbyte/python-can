#!/usr/bin/env python
# coding: utf-8

"""
Implements support for BLF (Binary Logging Format) which is a proprietary
CAN log format from Vector Informatik GmbH (Germany).

No official specification of the binary logging format is available.
This implementation is based on Toby Lorenz' C++ library "Vector BLF" which is
licensed under GPLv3. https://bitbucket.org/tobylorenz/vector_blf.

The file starts with a header. The rest is one or more "log containers"
which consists of a header and some zlib compressed data, usually up to 128 kB
of uncompressed data each. This data contains the actual CAN messages and other
objects types.
"""

from __future__ import absolute_import

import struct
import zlib
import datetime
import time
import logging

from can.message import Message
from can.listener import Listener
from can.util import len2dlc, dlc2len, channel2int
from .generic import BaseIOHandler


class BLFParseError(Exception):
    """BLF file could not be parsed correctly."""
    pass

LOG = logging.getLogger(__name__)

# 0 = unknown, 2 = CANoe
APPLICATION_ID = 5

# signature ("LOGG"), header size,
# application ID, application major, application minor, application build,
# bin log major, bin log minor, bin log build, bin log patch,
# file size, uncompressed size, count of objects, count of objects read,
# time start (SYSTEMTIME), time stop (SYSTEMTIME)
FILE_HEADER_STRUCT = struct.Struct("<4sLBBBBBBBBQQLL8H8H")

# Pad file header to this size
FILE_HEADER_SIZE = 144

# signature ("LOBJ"), header size, header version, object size, object type
OBJ_HEADER_BASE_STRUCT = struct.Struct("<4sHHLL")

# flags, client index, object version, timestamp
OBJ_HEADER_V1_STRUCT = struct.Struct("<LHHQ")

# flags, timestamp status, object version, timestamp, original timestamp
OBJ_HEADER_V2_STRUCT = struct.Struct("<LBxHQQ")

# compression method, size uncompressed
LOG_CONTAINER_STRUCT = struct.Struct("<H6xL4x")

# channel, flags, dlc, arbitration id, data
CAN_MSG_STRUCT = struct.Struct("<HBBL8s")

# channel, flags, dlc, arbitration id, frame length, bit count, FD flags,
# valid data bytes, data
CAN_FD_MSG_STRUCT = struct.Struct("<HBBLLBBB5x64s")

# channel, length, flags, ecc, position, dlc, frame length, id, flags ext, data
CAN_ERROR_EXT_STRUCT = struct.Struct("<HHLBBBxLLH2x8s")

# commented event type, foreground color, background color, relocatable,
# group name length, marker name length, description length
GLOBAL_MARKER_STRUCT = struct.Struct("<LLL3xBLLL12x")


CAN_MESSAGE = 1
CAN_ERROR = 2
LOG_CONTAINER = 10
CAN_ERROR_EXT = 73
CAN_MESSAGE2 = 86
GLOBAL_MARKER = 96
CAN_FD_MESSAGE = 100

NO_COMPRESSION = 0
ZLIB_DEFLATE = 2

CAN_MSG_EXT = 0x80000000
REMOTE_FLAG = 0x80
EDL = 0x1
BRS = 0x2
ESI = 0x4

TIME_TEN_MICS = 0x00000001
TIME_ONE_NANS = 0x00000002


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


class BLFReader(BaseIOHandler):
    """
    Iterator of CAN messages from a Binary Logging File.

    Only CAN messages and error frames are supported. Other object types are
    silently ignored.
    """

    def __init__(self, file):
        """
        :param file: a path-like object or as file-like object to read from
                     If this is a file-like object, is has to opened in binary
                     read mode, not text read mode.
        """
        super(BLFReader, self).__init__(file, mode='rb')
        data = self.file.read(FILE_HEADER_STRUCT.size)
        header = FILE_HEADER_STRUCT.unpack(data)
        if header[0] != b"LOGG":
            raise BLFParseError("Unexpected file format")
        self.file_size = header[10]
        self.uncompressed_size = header[11]
        self.object_count = header[12]
        self.start_timestamp = systemtime_to_timestamp(header[14:22])
        self.stop_timestamp = systemtime_to_timestamp(header[22:30])
        # Read rest of header
        self.file.read(header[1] - FILE_HEADER_STRUCT.size)

    def __iter__(self):
        tail = b""
        while True:
            data = self.file.read(OBJ_HEADER_BASE_STRUCT.size)
            if not data:
                # EOF
                break

            header = OBJ_HEADER_BASE_STRUCT.unpack(data)
            if header[0] != b"LOBJ":
                raise BLFParseError()
            obj_type = header[4]
            obj_data_size = header[3] - OBJ_HEADER_BASE_STRUCT.size
            obj_data = self.file.read(obj_data_size)
            # Read padding bytes
            self.file.read(obj_data_size % 4)

            if obj_type == LOG_CONTAINER:
                method, uncompressed_size = LOG_CONTAINER_STRUCT.unpack_from(
                    obj_data)
                container_data = obj_data[LOG_CONTAINER_STRUCT.size:]
                if method == NO_COMPRESSION:
                    data = container_data
                elif method == ZLIB_DEFLATE:
                    data = zlib.decompress(container_data, 15, uncompressed_size)
                else:
                    # Unknown compression method
                    LOG.warning("Unknown compression method (%d)", method)
                    continue

                if tail:
                    data = tail + data
                pos = 0
                while pos + OBJ_HEADER_BASE_STRUCT.size < len(data):
                    header = OBJ_HEADER_BASE_STRUCT.unpack_from(data, pos)
                    #print(header)
                    if header[0] != b"LOBJ":
                        raise BLFParseError()

                    obj_size = header[3]
                    # Calculate position of next object
                    next_pos = pos + obj_size + (obj_size % 4)
                    if next_pos > len(data):
                        # Object continues in next log container
                        break
                    pos += OBJ_HEADER_BASE_STRUCT.size

                    # Read rest of header
                    header_version = header[2]
                    if header_version == 1:
                        flags, _, _, timestamp = OBJ_HEADER_V1_STRUCT.unpack_from(data, pos)
                        pos += OBJ_HEADER_V1_STRUCT.size
                    elif header_version == 2:
                        flags, _, _, timestamp, _ = OBJ_HEADER_V2_STRUCT.unpack_from(data, pos)
                        pos += OBJ_HEADER_V2_STRUCT.size
                    else:
                        # Unknown header version
                        LOG.warning("Unknown object header version (%d)", header_version)
                        pos = next_pos
                        continue

                    if flags == TIME_TEN_MICS:
                        factor = 10 * 1e-6
                    else:
                        factor = 1e-9
                    timestamp = timestamp * factor + self.start_timestamp

                    obj_type = header[4]
                    # Both CAN message types have the same starting content
                    if obj_type in (CAN_MESSAGE, CAN_MESSAGE2):
                        (channel, flags, dlc, can_id,
                         can_data) = CAN_MSG_STRUCT.unpack_from(data, pos)
                        msg = Message(timestamp=timestamp,
                                      arbitration_id=can_id & 0x1FFFFFFF,
                                      extended_id=bool(can_id & CAN_MSG_EXT),
                                      is_remote_frame=bool(flags & REMOTE_FLAG),
                                      dlc=dlc,
                                      data=can_data[:dlc],
                                      channel=channel - 1)
                        yield msg
                    elif obj_type == CAN_FD_MESSAGE:
                        (channel, flags, dlc, can_id, _, _, fd_flags,
                         _, can_data) = CAN_FD_MSG_STRUCT.unpack_from(data, pos)
                        length = dlc2len(dlc)
                        msg = Message(timestamp=timestamp,
                                      arbitration_id=can_id & 0x1FFFFFFF,
                                      extended_id=bool(can_id & CAN_MSG_EXT),
                                      is_remote_frame=bool(flags & REMOTE_FLAG),
                                      is_fd=bool(fd_flags & EDL),
                                      bitrate_switch=bool(fd_flags & BRS),
                                      error_state_indicator=bool(fd_flags & ESI),
                                      dlc=length,
                                      data=can_data[:length],
                                      channel=channel - 1)
                        yield msg
                    elif obj_type == CAN_ERROR_EXT:
                        (channel, _, _, _, _, dlc, _, can_id, _,
                         can_data) = CAN_ERROR_EXT_STRUCT.unpack_from(data, pos)
                        msg = Message(timestamp=timestamp,
                                      is_error_frame=True,
                                      extended_id=bool(can_id & CAN_MSG_EXT),
                                      arbitration_id=can_id & 0x1FFFFFFF,
                                      dlc=dlc,
                                      data=can_data[:dlc],
                                      channel=channel - 1)
                        yield msg

                    pos = next_pos

                # save the remaining data that could not be processed
                tail = data[pos:]

        self.stop()


class BLFWriter(BaseIOHandler, Listener):
    """
    Logs CAN data to a Binary Logging File compatible with Vector's tools.
    """

    #: Max log container size of uncompressed data
    MAX_CACHE_SIZE = 128 * 1024

    #: ZLIB compression level
    COMPRESSION_LEVEL = 9

    def __init__(self, file, channel=1):
        """
        :param file: a path-like object or as file-like object to write to
                     If this is a file-like object, is has to opened in binary
                     write mode, not text write mode.
        """
        super(BLFWriter, self).__init__(file, mode='wb')
        self.channel = channel
        # Header will be written after log is done
        self.file.write(b"\x00" * FILE_HEADER_SIZE)
        self.cache = []
        self.cache_size = 0
        self.count_of_objects = 0
        self.uncompressed_size = FILE_HEADER_SIZE
        self.start_timestamp = None
        self.stop_timestamp = None

    def on_message_received(self, msg):
        channel = channel2int(msg.channel)
        if channel is None:
            channel = self.channel
        else:
            # Many interfaces start channel numbering at 0 which is invalid
            channel += 1

        arb_id = msg.arbitration_id
        if msg.id_type:
            arb_id |= CAN_MSG_EXT
        flags = REMOTE_FLAG if msg.is_remote_frame else 0
        data = bytes(msg.data)

        if msg.is_error_frame:
            data = CAN_ERROR_EXT_STRUCT.pack(channel,
                                             0,     # length
                                             0,     # flags
                                             0,     # ecc
                                             0,     # position
                                             len2dlc(msg.dlc),
                                             0,     # frame length
                                             arb_id,
                                             0,     # ext flags
                                             data)
            self._add_object(CAN_ERROR_EXT, data, msg.timestamp)
        elif msg.is_fd:
            fd_flags = EDL
            if msg.bitrate_switch:
                fd_flags |= BRS
            if msg.error_state_indicator:
                fd_flags |= ESI
            data = CAN_FD_MSG_STRUCT.pack(channel, flags, len2dlc(msg.dlc),
                                          arb_id, 0, 0, fd_flags, msg.dlc, data)
            self._add_object(CAN_FD_MESSAGE, data, msg.timestamp)
        else:
            data = CAN_MSG_STRUCT.pack(channel, flags, msg.dlc, arb_id, data)
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
        timestamp = int((timestamp - self.start_timestamp) * 1e9)
        header_size = OBJ_HEADER_BASE_STRUCT.size + OBJ_HEADER_V1_STRUCT.size
        obj_size = header_size + len(data)
        base_header = OBJ_HEADER_BASE_STRUCT.pack(
            b"LOBJ", header_size, 1, obj_size, obj_type)
        obj_header = OBJ_HEADER_V1_STRUCT.pack(TIME_ONE_NANS, 0, 0, max(timestamp, 0))

        self.cache.append(base_header)
        self.cache.append(obj_header)
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
        if self.file.closed:
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
        obj_size = (OBJ_HEADER_V1_STRUCT.size + LOG_CONTAINER_STRUCT.size +
                    len(compressed_data))
        base_header = OBJ_HEADER_BASE_STRUCT.pack(
            b"LOBJ", OBJ_HEADER_BASE_STRUCT.size, 1, obj_size, LOG_CONTAINER)
        container_header = LOG_CONTAINER_STRUCT.pack(
            ZLIB_DEFLATE, len(uncompressed_data))
        self.file.write(base_header)
        self.file.write(container_header)
        self.file.write(compressed_data)
        # Write padding bytes
        self.file.write(b"\x00" * (obj_size % 4))
        self.uncompressed_size += OBJ_HEADER_V1_STRUCT.size + LOG_CONTAINER_STRUCT.size
        self.uncompressed_size += len(uncompressed_data)

    def stop(self):
        """Stops logging and closes the file."""
        self._flush()
        filesize = self.file.tell()
        super(BLFWriter, self).stop()

        # Write header in the beginning of the file
        header = [b"LOGG", FILE_HEADER_SIZE,
                  APPLICATION_ID, 0, 0, 0, 2, 6, 8, 1]
        # The meaning of "count of objects read" is unknown
        header.extend([filesize, self.uncompressed_size,
                       self.count_of_objects, 0])
        header.extend(timestamp_to_systemtime(self.start_timestamp))
        header.extend(timestamp_to_systemtime(self.stop_timestamp))
        with open(self.file.name, "r+b") as f:
            f.write(FILE_HEADER_STRUCT.pack(*header))
