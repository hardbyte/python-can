#!/usr/bin/env python
# coding: utf-8

"""
This module works with CAN data in ASCII log files (*.log).
It is is compatible with "candump -L" from the canutils program
(https://github.com/linux-can/can-utils).
"""

import time
import datetime
import logging

from can.message import Message
from can.listener import Listener


log = logging.getLogger('can.io.canutils')

CAN_MSG_EXT         = 0x80000000
CAN_ERR_FLAG        = 0x20000000
CAN_ERR_BUSERROR    = 0x00000080
CAN_ERR_DLC         = 8


class CanutilsLogReader(object):
    """
    Iterator over CAN messages from a .log Logging File (candump -L).

    .. note::
        .log-format looks for example like this:

        ``(0.0) vcan0 001#8d00100100820100``
    """

    def __init__(self, filename):
        self.fp = open(filename, 'r')

    def __iter__(self):
        for line in self.fp:
            temp = line.strip()

            if temp:

                (timestamp, channel, frame) = temp.split()
                timestamp = float(timestamp[1:-1])
                (canId, data) = frame.split('#')
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

                    dlc = int(len(data) / 2)
                    dataBin = bytearray()
                    for i in range(0, 2 * dlc, 2):
                        dataBin.append(int(data[i:(i + 2)], 16))

                if canId & CAN_ERR_FLAG and canId & CAN_ERR_BUSERROR:
                    msg = Message(timestamp=timestamp, is_error_frame=True)
                else:
                    msg = Message(timestamp=timestamp, arbitration_id=canId & 0x1FFFFFFF,
                                  extended_id=isExtended, is_remote_frame=isRemoteFrame,
                                  dlc=dlc, data=dataBin, channel=channel)
                yield msg


class CanutilsLogWriter(Listener):
    """Logs CAN data to an ASCII log file (.log).
    This class is is compatible with "candump -L".

    If a message has a timestamp smaller than the previous one (or 0 or None),
    it gets assigned the timestamp that was written for the last message.
    It the first message does not have a timestamp, it is set to zero.
    """

    def __init__(self, filename, channel="vcan0"):
        self.channel = channel
        self.log_file = open(filename, 'w')
        self.last_timestamp = None

    def stop(self):
        """Stops logging and closes the file."""
        if self.log_file is not None:
            self.log_file.close()
            self.log_file = None
        else:
            log.warn("ignoring attempt to colse a already closed file")

    def on_message_received(self, msg):
        if self.log_file is None:
            log.warn("ignoring write attempt to closed file")
            return

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
            self.log_file.write("(%f) %s %08X#0000000000000000\n" % (timestamp, channel, CAN_ERR_FLAG | CAN_ERR_BUSERROR))

        elif msg.is_remote_frame:
            data = []
            if msg.is_extended_id:
                self.log_file.write("(%f) %s %08X#R\n" % (timestamp, channel, msg.arbitration_id))
            else:
                self.log_file.write("(%f) %s %03X#R\n" % (timestamp, channel, msg.arbitration_id))

        else:
            data = ["{:02X}".format(byte) for byte in msg.data]
            if msg.is_extended_id:
                self.log_file.write("(%f) %s %08X#%s\n" % (timestamp, channel, msg.arbitration_id, ''.join(data)))
            else:
                self.log_file.write("(%f) %s %03X#%s\n" % (timestamp, channel, msg.arbitration_id, ''.join(data)))
