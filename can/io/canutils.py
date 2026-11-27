"""
This module works with CAN data in ASCII log files (*.log).
It is is compatible with "candump -L" from the canutils program
(https://github.com/linux-can/can-utils).
"""

import logging
from collections.abc import Generator
from typing import Any, TextIO

from can.message import Message

from ..typechecking import StringPathLike
from .generic import TextIOMessageReader, TextIOMessageWriter

log = logging.getLogger("can.io.canutils")

CAN_MSG_EXT = 0x80000000
CAN_ERR_FLAG = 0x20000000
CAN_ERR_BUSERROR = 0x00000080
CAN_ERR_DLC = 8
CAN_MAX_DLEN = 8
CAN_MAX_RAW_DLC = 15
# separates an 8-byte Classical CAN frame from its raw DLC (9 to 15)
CC_DLC_DELIM = "_"

CANFD_BRS = 0x01
CANFD_ESI = 0x02


def _classic_dlc(length: int, raw_dlc: str) -> int:
    """Return the raw DLC written after an 8-byte length, else the length.

    Like can-utils, only the first digit after the delimiter counts, and only
    when it is 9 to F.
    """
    digit = raw_dlc[:1]
    if length == CAN_MAX_DLEN and digit and digit in "9ABCDEFabcdef":
        return int(digit, 16)
    return length


class CanutilsLogReader(TextIOMessageReader):
    """
    Iterator over CAN messages from a .log Logging File (candump -L).

    .. note::
        .log-format looks for example like this:

        ``(0.0) vcan0 001#8d00100100820100``
    """

    def __init__(
        self,
        file: StringPathLike | TextIO,
        **kwargs: Any,
    ) -> None:
        """
        :param file: a path-like object or as file-like object to read from
                     If this is a file-like object, is has to opened in text
                     read mode, not binary read mode.
        """
        super().__init__(file, mode="r")

    def __iter__(self) -> Generator[Message, None, None]:
        for line in self.file:
            # skip empty lines
            temp = line.strip()
            if not temp:
                continue

            channel_string: str
            if temp[-2:].lower() in (" r", " t"):
                timestamp_string, channel_string, frame, is_rx_string = temp.split()
                is_rx = is_rx_string.strip().lower() == "r"
            else:
                timestamp_string, channel_string, frame = temp.split()
                is_rx = True
            timestamp = float(timestamp_string[1:-1])
            can_id_string, data = frame.split("#", maxsplit=1)

            channel: int | str
            if channel_string.isdigit():
                channel = int(channel_string)
            else:
                channel = channel_string

            is_extended = len(can_id_string) > 3
            can_id = int(can_id_string, 16)

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
                is_remote_frame = True

                length, _, raw_dlc = data[1:].partition(CC_DLC_DELIM)
                dlc = _classic_dlc(int(length), raw_dlc) if length else 0

                data_bin = None
            else:
                is_remote_frame = False

                # the delimiter is only valid right after 8 data bytes
                raw_dlc = ""
                end = 2 * CAN_MAX_DLEN
                if not is_fd and data[end : end + 1] == CC_DLC_DELIM:
                    data, raw_dlc = data[:end], data[end + 1 :]
                dlc = _classic_dlc(len(data) // 2, raw_dlc)
                data_bin = bytearray()
                for i in range(0, len(data), 2):
                    data_bin.append(int(data[i : (i + 2)], 16))

            # error frames carry their error class bits in the identifier
            yield Message(
                timestamp=timestamp,
                arbitration_id=can_id & 0x1FFFFFFF,
                is_extended_id=is_extended,
                is_remote_frame=is_remote_frame,
                is_error_frame=bool(can_id & CAN_ERR_FLAG),
                is_fd=is_fd,
                is_rx=is_rx,
                bitrate_switch=brs,
                error_state_indicator=esi,
                dlc=dlc,
                data=data_bin,
                channel=channel,
            )

        self.stop()


class CanutilsLogWriter(TextIOMessageWriter):
    """Logs CAN data to an ASCII log file (.log).
    This class is is compatible with "candump -L".

    If a message has a timestamp smaller than the previous one (or 0 or None),
    it gets assigned the timestamp that was written for the last message.
    It the first message does not have a timestamp, it is set to zero.
    """

    def __init__(
        self,
        file: StringPathLike | TextIO,
        channel: str = "vcan0",
        append: bool = False,
        **kwargs: Any,
    ):
        """
        :param file: a path-like object or as file-like object to write to
                     If this is a file-like object, is has to opened in text
                     write mode, not binary write mode.
        :param channel: a default channel to use when the message does not
                        have a channel set
        :param bool append: if set to `True` messages are appended to
                            the file, else the file is truncated
        """
        super().__init__(file, mode="a" if append else "w")

        self.channel = channel
        self.last_timestamp: float | None = None

    def on_message_received(self, msg: Message) -> None:
        # this is the case for the very first message:
        if self.last_timestamp is None:
            self.last_timestamp = msg.timestamp or 0.0

        # figure out the correct timestamp
        if msg.timestamp is None or msg.timestamp < self.last_timestamp:
            timestamp = self.last_timestamp
        else:
            timestamp = msg.timestamp

        channel = msg.channel if msg.channel is not None else self.channel
        if isinstance(channel, int) or (isinstance(channel, str) and channel.isdigit()):
            channel = f"can{channel}"

        framestr = f"({timestamp:f}) {channel}"

        if msg.is_error_frame:
            error_class = msg.arbitration_id & 0x1FFFFFFF
            if not error_class:
                # no SocketCAN error class bits: write CAN_ERR_BUSERROR,
                # so older readers still recognise the line as an error frame
                error_class = CAN_ERR_BUSERROR
            framestr += f" {CAN_ERR_FLAG | error_class:08X}#"
        elif msg.is_extended_id:
            framestr += f" {msg.arbitration_id:08X}#"
        else:
            framestr += f" {msg.arbitration_id:03X}#"

        if msg.is_error_frame:
            eol = "\n"
        else:
            eol = " R\n" if msg.is_rx else " T\n"

        # an 8-byte Classical CAN frame may carry a raw DLC of 9 to 15
        raw_dlc = ""
        if not msg.is_fd and CAN_MAX_DLEN < msg.dlc <= CAN_MAX_RAW_DLC:
            raw_dlc = f"{CC_DLC_DELIM}{msg.dlc:X}"

        if msg.is_remote_frame:
            if 0 < msg.dlc <= CAN_MAX_DLEN:
                remote_dlc = str(msg.dlc)
            elif raw_dlc:
                remote_dlc = f"{CAN_MAX_DLEN}{raw_dlc}"
            else:
                remote_dlc = ""
            framestr += f"R{remote_dlc}{eol}"
        else:
            if msg.is_fd:
                fd_flags = 0
                if msg.bitrate_switch:
                    fd_flags |= CANFD_BRS
                if msg.error_state_indicator:
                    fd_flags |= CANFD_ESI
                framestr += f"#{fd_flags:X}"
            framestr += msg.data.hex().upper()
            if len(msg.data) == CAN_MAX_DLEN:
                framestr += raw_dlc
            framestr += eol

        self.file.write(framestr)
