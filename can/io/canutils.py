"""
This module works with CAN data in ASCII log files (*.log).
It is is compatible with "candump -L" from the canutils program
(https://github.com/linux-can/can-utils).
"""

import logging

from can.message import Message
from can.listener import Listener
from .generic import BaseIOHandler, FileIOMessageWriter
from ..typechecking import AcceptedIOType

log = logging.getLogger("can.io.canutils")

CAN_MSG_EXT = 0x80000000
CAN_ERR_FLAG = 0x20000000
CAN_ERR_BUSERROR = 0x00000080
CAN_ERR_DLC = 8

CANFD_BRS = 0x01
CANFD_ESI = 0x02


class CanutilsLogReader(BaseIOHandler):
    """
    Iterator over CAN messages from a .log Logging File (candump -L).

    .. note::
        .log-format looks for example like this:

        ``(0.0) vcan0 001#8d00100100820100``
    """

    def __init__(self, file: AcceptedIOType) -> None:
        """
        :param file: a path-like object or as file-like object to read from
                     If this is a file-like object, is has to opened in text
                     read mode, not binary read mode.
        """
        super().__init__(file, mode="r")

    def __iter__(self):
        for line in self.file:

            # skip empty lines
            temp = line.strip()
            if not temp:
                continue

            timestamp, channel, frame = temp.split()
            timestamp = float(timestamp[1:-1])
            canId, data = frame.split("#", maxsplit=1)
            if channel.isdigit():
                channel = int(channel)

            isExtended = len(canId) > 3
            canId = int(canId, 16)

            is_fd = False
            brs = False
            esi = False

            if data and data[0] == "#":
                is_fd = True
                fd_flags = int(data[1])
                brs = bool(fd_flags & CANFD_BRS)
                esi = bool(fd_flags & CANFD_ESI)
                data = data[2:]

            if data and data[0].lower() == "r":
                isRemoteFrame = True

                if len(data) > 1:
                    dlc = int(data[1:])
                else:
                    dlc = 0

                dataBin = None
            else:
                isRemoteFrame = False

                dlc = len(data) // 2
                dataBin = bytearray()
                for i in range(0, len(data), 2):
                    dataBin.append(int(data[i : (i + 2)], 16))

            if canId & CAN_ERR_FLAG and canId & CAN_ERR_BUSERROR:
                msg = Message(timestamp=timestamp, is_error_frame=True)
            else:
                msg = Message(
                    timestamp=timestamp,
                    arbitration_id=canId & 0x1FFFFFFF,
                    is_extended_id=isExtended,
                    is_remote_frame=isRemoteFrame,
                    is_fd=is_fd,
                    bitrate_switch=brs,
                    error_state_indicator=esi,
                    dlc=dlc,
                    data=dataBin,
                    channel=channel,
                )
            yield msg

        self.stop()


class CanutilsLogWriter(FileIOMessageWriter, Listener):
    """Logs CAN data to an ASCII log file (.log).
    This class is is compatible with "candump -L".

    If a message has a timestamp smaller than the previous one (or 0 or None),
    it gets assigned the timestamp that was written for the last message.
    It the first message does not have a timestamp, it is set to zero.
    """

    def __init__(self, file: AcceptedIOType, channel="vcan0", append=False):
        """
        :param file: a path-like object or as file-like object to write to
                     If this is a file-like object, is has to opened in text
                     write mode, not binary write mode.
        :param channel: a default channel to use when the message does not
                        have a channel set
        :param bool append: if set to `True` messages are appended to
                            the file, else the file is truncated
        """
        mode = "a" if append else "w"
        super().__init__(file, mode=mode)

        self.channel = channel
        self.last_timestamp = None

    def on_message_received(self, msg):
        # this is the case for the very first message:
        if self.last_timestamp is None:
            self.last_timestamp = msg.timestamp or 0.0

        # figure out the correct timestamp
        if msg.timestamp is None or msg.timestamp < self.last_timestamp:
            timestamp = self.last_timestamp
        else:
            timestamp = msg.timestamp

        channel = msg.channel if msg.channel is not None else self.channel

        framestr = "(%f) %s" % (timestamp, channel)

        if msg.is_error_frame:
            framestr += " %08X#" % (CAN_ERR_FLAG | CAN_ERR_BUSERROR)
        elif msg.is_extended_id:
            framestr += " %08X#" % (msg.arbitration_id)
        else:
            framestr += " %03X#" % (msg.arbitration_id)

        if msg.is_remote_frame:
            framestr += "R\n"
        else:
            if msg.is_fd:
                fd_flags = 0
                if msg.bitrate_switch:
                    fd_flags |= CANFD_BRS
                if msg.error_state_indicator:
                    fd_flags |= CANFD_ESI
                framestr += "#%X" % fd_flags
            framestr += "%s\n" % (msg.data.hex().upper())

        self.file.write(framestr)
