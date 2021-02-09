"""
Contains handling of ASC logging files.

Example .asc files:
    - https://bitbucket.org/tobylorenz/vector_asc/src/47556e1a6d32c859224ca62d075e1efcc67fa690/src/Vector/ASC/tests/unittests/data/CAN_Log_Trigger_3_2.asc?at=master&fileviewer=file-view-default
    - under `test/data/logfile.asc`
"""

from typing import cast, Any, Generator, IO, List, Optional, Union, Dict
from can import typechecking

from datetime import datetime
import time
import logging

from ..message import Message
from ..listener import Listener
from ..util import channel2int
from .generic import BaseIOHandler


CAN_MSG_EXT = 0x80000000
CAN_ID_MASK = 0x1FFFFFFF
BASE_HEX = 16
BASE_DEC = 10

logger = logging.getLogger("can.io.asc")


class ASCReader(BaseIOHandler):
    """
    Iterator of CAN messages from a ASC logging file. Meta data (comments,
    bus statistics, J1939 Transport Protocol messages) is ignored.

    TODO: turn relative timestamps back to absolute form
    """

    def __init__(
        self,
        file: Union[typechecking.FileLike, typechecking.StringPathLike],
        base: str = "hex",
    ) -> None:
        """
        :param file: a path-like object or as file-like object to read from
                     If this is a file-like object, is has to opened in text
                     read mode, not binary read mode.
        :param base: Select the base(hex or dec) of id and data.
                     If the header of the asc file contains base information,
                     this value will be overwritten. Default "hex".
        """
        super().__init__(file, mode="r")

        if not self.file:
            raise ValueError("The given file cannot be None")
        self.base = base
        self._converted_base = self._check_base(base)
        self.date = None
        self.timestamps_format = None
        self.internal_events_logged = None

    def _extract_header(self):
        for line in self.file:
            line = line.strip()
            lower_case = line.lower()
            if lower_case.startswith("date"):
                self.date = line[5:]
            elif lower_case.startswith("base"):
                try:
                    _, base, _, timestamp_format = line.split()
                except ValueError:
                    raise Exception("Unsupported header string format: {}".format(line))
                self.base = base
                self._converted_base = self._check_base(self.base)
                self.timestamps_format = timestamp_format
            elif lower_case.endswith("internal events logged"):
                self.internal_events_logged = not lower_case.startswith("no")
                # Currently the last line in the header which is parsed
                break
            else:
                break

    def _extract_can_id(self, str_can_id: str, msg_kwargs: Dict[str, Any]) -> None:
        if str_can_id[-1:].lower() == "x":
            msg_kwargs["is_extended_id"] = True
            can_id = int(str_can_id[0:-1], self._converted_base)
        else:
            msg_kwargs["is_extended_id"] = False
            can_id = int(str_can_id, self._converted_base)
        msg_kwargs["arbitration_id"] = can_id

    @staticmethod
    def _check_base(base: str) -> int:
        if base not in ["hex", "dec"]:
            raise ValueError('base should be either "hex" or "dec"')
        return BASE_DEC if base == "dec" else BASE_HEX

    def _process_data_string(
        self, data_str: str, data_length: int, msg_kwargs: Dict[str, Any]
    ) -> None:
        frame = bytearray()
        data = data_str.split()
        for byte in data[:data_length]:
            frame.append(int(byte, self._converted_base))
        msg_kwargs["data"] = frame

    def _process_classic_can_frame(
        self, line: str, msg_kwargs: Dict[str, Any]
    ) -> Message:

        # CAN error frame
        if line.strip()[0:10].lower() == "errorframe":
            # Error Frame
            msg_kwargs["is_error_frame"] = True
        else:
            abr_id_str, dir, rest_of_message = line.split(None, 2)
            msg_kwargs["is_rx"] = dir == "Rx"
            self._extract_can_id(abr_id_str, msg_kwargs)

            if rest_of_message[0].lower() == "r":
                # CAN Remote Frame
                msg_kwargs["is_remote_frame"] = True
                remote_data = rest_of_message.split()
                if len(remote_data) > 1:
                    dlc_str = remote_data[1]
                    if dlc_str.isdigit():
                        msg_kwargs["dlc"] = int(dlc_str, self._converted_base)
            else:
                # Classic CAN Message
                try:
                    # There is data after DLC
                    _, dlc_str, data = rest_of_message.split(None, 2)
                except ValueError:
                    # No data after DLC
                    _, dlc_str = rest_of_message.split(None, 1)
                    data = ""

                dlc = int(dlc_str, self._converted_base)
                msg_kwargs["dlc"] = dlc
                self._process_data_string(data, dlc, msg_kwargs)

        return Message(**msg_kwargs)

    def _process_fd_can_frame(self, line: str, msg_kwargs: Dict[str, Any]) -> Message:
        channel, dir, rest_of_message = line.split(None, 2)
        # See ASCWriter
        msg_kwargs["channel"] = int(channel) - 1
        msg_kwargs["is_rx"] = dir == "Rx"

        # CAN FD error frame
        if rest_of_message.strip()[:10].lower() == "errorframe":
            # Error Frame
            # TODO: maybe use regex to parse BRS, ESI, etc?
            msg_kwargs["is_error_frame"] = True
        else:
            can_id_str, frame_name_or_brs, rest_of_message = rest_of_message.split(
                None, 2
            )

            if frame_name_or_brs.isdigit():
                brs = frame_name_or_brs
                esi, dlc_str, data_length_str, data = rest_of_message.split(None, 3)
            else:
                brs, esi, dlc_str, data_length_str, data = rest_of_message.split(
                    None, 4
                )

            self._extract_can_id(can_id_str, msg_kwargs)
            msg_kwargs["bitrate_switch"] = brs == "1"
            msg_kwargs["error_state_indicator"] = esi == "1"
            dlc = int(dlc_str, self._converted_base)
            msg_kwargs["dlc"] = dlc
            data_length = int(data_length_str)

            # CAN remote Frame
            msg_kwargs["is_remote_frame"] = data_length == 0

            self._process_data_string(data, data_length, msg_kwargs)

        return Message(**msg_kwargs)

    def __iter__(self) -> Generator[Message, None, None]:
        # This is guaranteed to not be None since we raise ValueError in __init__
        self.file = cast(IO[Any], self.file)
        self._extract_header()

        for line in self.file:
            temp = line.strip()
            if not temp or not temp[0].isdigit():
                # Could be a comment
                continue
            msg_kwargs = {}
            try:
                timestamp, channel, rest_of_message = temp.split(None, 2)
                timestamp = float(timestamp)
                msg_kwargs["timestamp"] = timestamp
                if channel == "CANFD":
                    msg_kwargs["is_fd"] = True
                elif channel.isdigit():
                    # See ASCWriter
                    msg_kwargs["channel"] = int(channel) - 1
                else:
                    # Not a CAN message. Possible values include "statistic", J1939TP
                    continue
            except ValueError:
                # Some other unprocessed or unknown format
                continue

            if "is_fd" not in msg_kwargs:
                msg = self._process_classic_can_frame(rest_of_message, msg_kwargs)
            else:
                msg = self._process_fd_can_frame(rest_of_message, msg_kwargs)
            if msg is not None:
                yield msg

        self.stop()


class ASCWriter(BaseIOHandler, Listener):
    """Logs CAN data to an ASCII log file (.asc).

    The measurement starts with the timestamp of the first registered message.
    If a message has a timestamp smaller than the previous one or None,
    it gets assigned the timestamp that was written for the last message.
    It the first message does not have a timestamp, it is set to zero.
    """

    FORMAT_MESSAGE = "{channel}  {id:<15} {dir:<4} {dtype} {data}"
    FORMAT_MESSAGE_FD = " ".join(
        [
            "CANFD",
            "{channel:>3}",
            "{dir:<4}",
            "{id:>8}  {symbolic_name:>32}",
            "{brs}",
            "{esi}",
            "{dlc:x}",
            "{data_length:>2}",
            "{data}",
            "{message_duration:>8}",
            "{message_length:>4}",
            "{flags:>8X}",
            "{crc:>8}",
            "{bit_timing_conf_arb:>8}",
            "{bit_timing_conf_data:>8}",
            "{bit_timing_conf_ext_arb:>8}",
            "{bit_timing_conf_ext_data:>8}",
        ]
    )
    FORMAT_START_OF_FILE_DATE = "%a %b %d %I:%M:%S.%f %p %Y"
    FORMAT_DATE = "%a %b %d %I:%M:%S.{} %p %Y"
    FORMAT_EVENT = "{timestamp: 9.6f} {message}\n"

    def __init__(
        self,
        file: Union[typechecking.FileLike, typechecking.StringPathLike],
        channel: int = 1,
    ) -> None:
        """
        :param file: a path-like object or as file-like object to write to
                     If this is a file-like object, is has to opened in text
                     write mode, not binary write mode.
        :param channel: a default channel to use when the message does not
                        have a channel set
        """
        super().__init__(file, mode="w")
        if not self.file:
            raise ValueError("The given file cannot be None")

        self.channel = channel

        # write start of file header
        now = datetime.now().strftime(self.FORMAT_START_OF_FILE_DATE)
        self.file.write("date %s\n" % now)
        self.file.write("base hex  timestamps absolute\n")
        self.file.write("internal events logged\n")

        # the last part is written with the timestamp of the first message
        self.header_written = False
        self.last_timestamp = 0.0
        self.started = 0.0

    def stop(self) -> None:
        # This is guaranteed to not be None since we raise ValueError in __init__
        self.file = cast(IO[Any], self.file)
        if not self.file.closed:
            self.file.write("End TriggerBlock\n")
        super().stop()

    def log_event(self, message: str, timestamp: Optional[float] = None) -> None:
        """Add a message to the log file.

        :param message: an arbitrary message
        :param timestamp: the absolute timestamp of the event
        """

        if not message:  # if empty or None
            logger.debug("ASCWriter: ignoring empty message")
            return
        # This is guaranteed to not be None since we raise ValueError in __init__
        self.file = cast(IO[Any], self.file)

        # this is the case for the very first message:
        if not self.header_written:
            self.last_timestamp = timestamp or 0.0
            self.started = self.last_timestamp
            mlsec = repr(self.last_timestamp).split(".")[1][:3]
            formatted_date = time.strftime(
                self.FORMAT_DATE.format(mlsec), time.localtime(self.last_timestamp)
            )
            self.file.write("Begin Triggerblock %s\n" % formatted_date)
            self.header_written = True
            self.log_event("Start of measurement")  # caution: this is a recursive call!
        # Use last known timestamp if unknown
        if timestamp is None:
            timestamp = self.last_timestamp
        # turn into relative timestamps if necessary
        if timestamp >= self.started:
            timestamp -= self.started
        line = self.FORMAT_EVENT.format(timestamp=timestamp, message=message)
        self.file.write(line)

    def on_message_received(self, msg: Message) -> None:

        if msg.is_error_frame:
            self.log_event("{}  ErrorFrame".format(self.channel), msg.timestamp)
            return
        if msg.is_remote_frame:
            dtype = "r {:x}".format(msg.dlc)  # New after v8.5
            data: List[str] = []
        else:
            dtype = "d {:x}".format(msg.dlc)
            data = ["{:02X}".format(byte) for byte in msg.data]
        arb_id = "{:X}".format(msg.arbitration_id)
        if msg.is_extended_id:
            arb_id += "x"
        channel = channel2int(msg.channel)
        if channel is None:
            channel = self.channel
        else:
            # Many interfaces start channel numbering at 0 which is invalid
            channel += 1
        if msg.is_fd:
            flags = 0
            flags |= 1 << 12
            if msg.bitrate_switch:
                flags |= 1 << 13
            if msg.error_state_indicator:
                flags |= 1 << 14
            serialized = self.FORMAT_MESSAGE_FD.format(
                channel=channel,
                id=arb_id,
                dir="Rx" if msg.is_rx else "Tx",
                symbolic_name="",
                brs=1 if msg.bitrate_switch else 0,
                esi=1 if msg.error_state_indicator else 0,
                dlc=msg.dlc,
                data_length=len(data),
                data=" ".join(data),
                message_duration=0,
                message_length=0,
                flags=flags,
                crc=0,
                bit_timing_conf_arb=0,
                bit_timing_conf_data=0,
                bit_timing_conf_ext_arb=0,
                bit_timing_conf_ext_data=0,
            )
        else:
            serialized = self.FORMAT_MESSAGE.format(
                channel=channel,
                id=arb_id,
                dir="Rx" if msg.is_rx else "Tx",
                dtype=dtype,
                data=" ".join(data),
            )
        self.log_event(serialized, msg.timestamp)
