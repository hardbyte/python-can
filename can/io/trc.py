"""
Reader and writer for can logging files in peak trc format

See https://www.peak-system.com/produktcd/Pdf/English/PEAK_CAN_TRC_File_Format.pdf
for file format description

Version 1.1 will be implemented as it is most commonly used
"""  # noqa

from datetime import datetime, timedelta
from enum import Enum
import io
import os
import logging
from typing import Generator, Optional, Union, TextIO, Callable, List

from ..message import Message
from ..util import channel2int
from .generic import FileIOMessageWriter, MessageReader
from ..typechecking import StringPathLike


logger = logging.getLogger("can.io.trc")


class TRCFileVersion(Enum):
    UNKNOWN = 0
    V1_0 = 100
    V1_1 = 101
    V1_2 = 102
    V1_3 = 103
    V2_0 = 200
    V2_1 = 201


class TRCReader(MessageReader):
    """
    Iterator of CAN messages from a TRC logging file.
    """

    file: TextIO

    def __init__(
        self,
        file: Union[StringPathLike, TextIO],
    ) -> None:
        """
        :param file: a path-like object or as file-like object to read from
                     If this is a file-like object, is has to opened in text
                     read mode, not binary read mode.
        """
        super().__init__(file, mode="r")
        self.file_version = TRCFileVersion.UNKNOWN

        if not self.file:
            raise ValueError("The given file cannot be None")

        self._parse_cols: Callable[[List[str]], Optional[Message]] = lambda x: None

    def _extract_header(self):
        line = ""
        for line in self.file:
            line = line.strip()
            if line.startswith(";$FILEVERSION"):
                logger.debug("TRCReader: Found file version '%s'", line)
                try:
                    file_version = line.split("=")[1]
                    if file_version == "1.1":
                        self.file_version = TRCFileVersion.V1_1
                    elif file_version == "2.1":
                        self.file_version = TRCFileVersion.V2_1
                    else:
                        self.file_version = TRCFileVersion.UNKNOWN
                except IndexError:
                    logger.debug("TRCReader: Failed to parse version")
            elif line.startswith(";"):
                continue
            else:
                break

        if self.file_version == TRCFileVersion.UNKNOWN:
            logger.info(
                "TRCReader: No file version was found, so version 1.0 is assumed"
            )
            self._parse_cols = self._parse_msg_V1_0
        elif self.file_version == TRCFileVersion.V1_0:
            self._parse_cols = self._parse_msg_V1_0
        elif self.file_version == TRCFileVersion.V1_1:
            self._parse_cols = self._parse_cols_V1_1
        elif self.file_version == TRCFileVersion.V2_1:
            self._parse_cols = self._parse_cols_V2_1
        else:
            raise NotImplementedError("File version not fully implemented for reading")

        return line

    def _parse_msg_V1_0(self, cols: List[str]) -> Optional[Message]:
        arbit_id = cols[2]
        if arbit_id == "FFFFFFFF":
            logger.info("TRCReader: Dropping bus info line")
            return None

        msg = Message()
        msg.timestamp = float(cols[1]) / 1000
        msg.arbitration_id = int(arbit_id, 16)
        msg.is_extended_id = len(arbit_id) > 4
        msg.channel = 1
        msg.dlc = int(cols[3])
        msg.data = bytearray([int(cols[i + 4], 16) for i in range(msg.dlc)])
        return msg

    def _parse_msg_V1_1(self, cols: List[str]) -> Optional[Message]:
        arbit_id = cols[3]

        msg = Message()
        msg.timestamp = float(cols[1]) / 1000
        msg.arbitration_id = int(arbit_id, 16)
        msg.is_extended_id = len(arbit_id) > 4
        msg.channel = 1
        msg.dlc = int(cols[4])
        msg.data = bytearray([int(cols[i + 5], 16) for i in range(msg.dlc)])
        msg.is_rx = cols[2] == "Rx"
        return msg

    def _parse_msg_V2_1(self, cols: List[str]) -> Optional[Message]:
        msg = Message()
        msg.timestamp = float(cols[1]) / 1000
        msg.arbitration_id = int(cols[4], 16)
        msg.is_extended_id = len(cols[4]) > 4
        msg.channel = int(cols[3])
        msg.dlc = int(cols[7])
        msg.data = bytearray([int(cols[i + 8], 16) for i in range(msg.dlc)])
        msg.is_rx = cols[5] == "Rx"
        return msg

    def _parse_cols_V1_1(self, cols: List[str]) -> Optional[Message]:
        dtype = cols[2]
        if dtype in ("Tx", "Rx"):
            return self._parse_msg_V1_1(cols)
        else:
            logger.info("TRCReader: Unsupported type '%s'", dtype)
            return None

    def _parse_cols_V2_1(self, cols: List[str]) -> Optional[Message]:
        dtype = cols[2]
        if dtype == "DT":
            return self._parse_msg_V2_1(cols)
        else:
            logger.info("TRCReader: Unsupported type '%s'", dtype)
            return None

    def _parse_line(self, line: str) -> Optional[Message]:
        logger.debug("TRCReader: Parse '%s'", line)
        try:
            cols = line.split()
            return self._parse_cols(cols)
        except IndexError:
            logger.warning("TRCReader: Failed to parse message '%s'", line)
            return None

    def __iter__(self) -> Generator[Message, None, None]:
        first_line = self._extract_header()

        if first_line is not None:
            msg = self._parse_line(first_line)
            if msg is not None:
                yield msg

        for line in self.file:
            temp = line.strip()
            if temp.startswith(";"):
                # Comment line
                continue

            if len(temp) == 0:
                # Empty line
                continue

            msg = self._parse_line(temp)
            if msg is not None:
                yield msg

        self.stop()


class TRCWriter(FileIOMessageWriter):
    """Logs CAN data to text file (.trc).

    The measurement starts with the timestamp of the first registered message.
    If a message has a timestamp smaller than the previous one or None,
    it gets assigned the timestamp that was written for the last message.
    If the first message does not have a timestamp, it is set to zero.
    """

    file: TextIO
    first_timestamp: Optional[float]

    FORMAT_MESSAGE = (
        "{msgnr:>7} {time:13.3f} DT {channel:>2} {id:>8} {dir:>2} -  {dlc:<4} {data}"
    )
    FORMAT_MESSAGE_V1_0 = "{msgnr:>6}) {time:7.0f} {id:>8} {dlc:<1} {data}"

    def __init__(
        self,
        file: Union[StringPathLike, TextIO],
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
        self.channel = channel

        if isinstance(self.file, io.TextIOWrapper):
            self.file.reconfigure(newline="\r\n")
        else:
            raise TypeError("File must be opened in text mode.")

        self.filepath = os.path.abspath(self.file.name)
        self.header_written = False
        self.msgnr = 0
        self.first_timestamp = None
        self.file_version = TRCFileVersion.V2_1
        self._msg_fmt_string = self.FORMAT_MESSAGE_V1_0
        self._format_message = self._format_message_init

    def _write_header_V1_0(self, start_time: timedelta) -> None:
        lines = [
            ";##########################################################################",
            f";   {self.filepath}",
            ";",
            ";    Generated by python-can TRCWriter",
            f";    Start time: {start_time}",
            ";    PCAN-Net: N/A",
            ";",
            ";    Columns description:",
            ";    ~~~~~~~~~~~~~~~~~~~~~",
            ";    +-current number in actual sample",
            ";    |     +time offset of message (ms",
            ";    |     |        +ID of message (hex",
            ";    |     |        |    +data length code",
            ";    |     |        |    |  +data bytes (hex ...",
            ";    |     |        |    |  |",
            ";----+- ---+--- ----+--- + -+ -- -- ...",
        ]
        self.file.writelines(line + "\n" for line in lines)

    def _write_header_V2_1(self, header_time: timedelta, start_time: datetime) -> None:
        milliseconds = int(
            (header_time.seconds * 1000) + (header_time.microseconds / 1000)
        )
        lines = [
            ";$FILEVERSION=2.1",
            f";$STARTTIME={header_time.days}.{milliseconds}",
            ";$COLUMNS=N,O,T,B,I,d,R,L,D",
            ";",
            f";   {self.filepath}",
            ";",
            f";   Start time: {start_time}",
            ";   Generated by python-can TRCWriter",
            ";-------------------------------------------------------------------------------",
            ";   Bus   Name            Connection               Protocol",
            ";   N/A   N/A             N/A                      N/A",
            ";-------------------------------------------------------------------------------",
            ";   Message   Time    Type    ID     Rx/Tx",
            ";   Number    Offset  |  Bus  [hex]  |  Reserved",
            ";   |         [ms]    |  |    |      |  |  Data Length Code",
            ";   |         |       |  |    |      |  |  |    Data [hex] ...",
            ";   |         |       |  |    |      |  |  |    |",
            ";---+-- ------+------ +- +- --+----- +- +- +--- +- -- -- -- -- -- -- --",
        ]
        self.file.writelines(line + "\n" for line in lines)

    def _format_message_by_format(self, msg, channel):
        if msg.is_extended_id:
            arb_id = f"{msg.arbitration_id:07X}"
        else:
            arb_id = f"{msg.arbitration_id:04X}"

        data = [f"{byte:02X}" for byte in msg.data]

        serialized = self._msg_fmt_string.format(
            msgnr=self.msgnr,
            time=(msg.timestamp - self.first_timestamp) * 1000,
            channel=channel,
            id=arb_id,
            dir="Rx" if msg.is_rx else "Tx",
            dlc=msg.dlc,
            data=" ".join(data),
        )
        return serialized

    def _format_message_init(self, msg, channel):
        if self.file_version == TRCFileVersion.V1_0:
            self._format_message = self._format_message_by_format
            self._msg_fmt_string = self.FORMAT_MESSAGE_V1_0
        elif self.file_version == TRCFileVersion.V2_1:
            self._format_message = self._format_message_by_format
            self._msg_fmt_string = self.FORMAT_MESSAGE
        else:
            raise NotImplementedError("File format is not supported")

        return self._format_message_by_format(msg, channel)

    def write_header(self, timestamp: float) -> None:
        # write start of file header
        ref_time = datetime(year=1899, month=12, day=30)
        start_time = datetime.now() + timedelta(seconds=timestamp)
        header_time = start_time - ref_time

        if self.file_version == TRCFileVersion.V1_0:
            self._write_header_V1_0(header_time)
        elif self.file_version == TRCFileVersion.V2_1:
            self._write_header_V2_1(header_time, start_time)
        else:
            raise NotImplementedError("File format is not supported")
        self.header_written = True

    def log_event(self, message: str, timestamp: float) -> None:
        if not self.header_written:
            self.write_header(timestamp)

        self.file.write(message + "\n")

    def on_message_received(self, msg: Message) -> None:
        if self.first_timestamp is None:
            self.first_timestamp = msg.timestamp

        if msg.is_error_frame:
            logger.warning("TRCWriter: Logging error frames is not implemented")
            return

        if msg.is_remote_frame:
            logger.warning("TRCWriter: Logging remote frames is not implemented")
            return

        channel = channel2int(msg.channel)
        if channel is None:
            channel = self.channel
        else:
            # Many interfaces start channel numbering at 0 which is invalid
            channel += 1

        if msg.is_fd:
            logger.warning("TRCWriter: Logging CAN FD is not implemented")
            return
        else:
            serialized = self._format_message(msg, channel)
            self.msgnr += 1
        self.log_event(serialized, msg.timestamp)
