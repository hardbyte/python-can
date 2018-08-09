#!/usr/bin/env python
# coding: utf-8

"""
This module works with CAN data in ASCII log files (*.log).
It is is compatible with "candump -L" from the canutils program
(https://github.com/linux-can/can-utils).
"""

from __future__ import absolute_import, division

import time
import datetime
import logging

from can.message import Message
from can.listener import Listener
from .generic import BaseIOHandler


log = logging.getLogger('can.io.canutils')

CAN_MSG_EXT         = 0x80000000
CAN_ERR_FLAG        = 0x20000000
CAN_ERR_BUSERROR    = 0x00000080
CAN_ERR_DLC         = 8


class CanutilsLogReader(BaseIOHandler):
    """
    Iterator over CAN messages from a .log Logging File (candump -L).

    .. note::
        .log-format looks for example like this:

        ``(0.0) vcan0 001#8d00100100820100``
    """

    def __init__(self, file):
        """
        :param file: a path-like object or as file-like object to read from
                     If this is a file-like object, is has to opened in text
                     read mode, not binary read mode.
        """
        super(CanutilsLogReader, self).__init__(file, mode='r')

    def __iter__(self):
        for line in self.file:

            # skip empty lines
            temp = line.strip()
            if not temp:
                continue

            timestamp, channel, frame = temp.split()
            timestamp = float(timestamp[1:-1])
            canId, data = frame.split('#')
            if channel.isdigit():
                channel = int(channel)

            if len(canId) > 3:
                isExtended = True
            else:
                isExtended = False
            canId = int(canId, 16)

            if data and data[0].lower() == 'r':
                isRemoteFrame = True
                if len(data) > 1:
                    dlc = int(data[1:])
                else:
                    dlc = 0
            else:
                isRemoteFrame = False

                dlc = len(data) // 2
                dataBin = bytearray()
                for i in range(0, len(data), 2):
                    dataBin.append(int(data[i:(i + 2)], 16))

            if canId & CAN_ERR_FLAG and canId & CAN_ERR_BUSERROR:
                msg = Message(timestamp=timestamp, is_error_frame=True)
            else:
                msg = Message(timestamp=timestamp, arbitration_id=canId & 0x1FFFFFFF,
                              extended_id=isExtended, is_remote_frame=isRemoteFrame,
                              dlc=dlc, data=dataBin, channel=channel)
            yield msg

        self.stop()


class CanutilsLogWriter(BaseIOHandler, Listener):
    """Logs CAN data to an ASCII log file (.log).
    This class is is compatible with "candump -L".

    If a message has a timestamp smaller than the previous one (or 0 or None),
    it gets assigned the timestamp that was written for the last message.
    It the first message does not have a timestamp, it is set to zero.
    """

    def __init__(self, file, channel="vcan0", append=False):
        """
        :param file: a path-like object or as file-like object to write to
                     If this is a file-like object, is has to opened in text
                     write mode, not binary write mode.
        :param channel: a default channel to use when the message does not
                        have a channel set
        :param bool append: if set to `True` messages are appended to
                            the file, else the file is truncated
        """
        mode = 'a' if append else 'w'
        super(CanutilsLogWriter, self).__init__(file, mode=mode)

        self.channel = channel
        self.last_timestamp = None

    def on_message_received(self, msg):
        # this is the case for the very first message:
        if self.last_timestamp is None:
            self.last_timestamp = (msg.timestamp or 0.0)

        # figure out the correct timestamp
        if msg.timestamp is None or msg.timestamp < self.last_timestamp:
            timestamp = self.last_timestamp
        else:
            timestamp = msg.timestamp

        channel = msg.channel if msg.channel is not None else self.channel

        if msg.is_error_frame:
            self.file.write("(%f) %s %08X#0000000000000000\n" % (timestamp, channel, CAN_ERR_FLAG | CAN_ERR_BUSERROR))

        elif msg.is_remote_frame:
            if msg.is_extended_id:
                self.file.write("(%f) %s %08X#R\n" % (timestamp, channel, msg.arbitration_id))
            else:
                self.file.write("(%f) %s %03X#R\n" % (timestamp, channel, msg.arbitration_id))

        else:
            data = ["{:02X}".format(byte) for byte in msg.data]
            if msg.is_extended_id:
                self.file.write("(%f) %s %08X#%s\n" % (timestamp, channel, msg.arbitration_id, ''.join(data)))
            else:
                self.file.write("(%f) %s %03X#%s\n" % (timestamp, channel, msg.arbitration_id, ''.join(data)))
