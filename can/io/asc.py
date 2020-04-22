"""
Contains handling of ASC logging files.

Example .asc files:
    - https://bitbucket.org/tobylorenz/vector_asc/src/47556e1a6d32c859224ca62d075e1efcc67fa690/src/Vector/ASC/tests/unittests/data/CAN_Log_Trigger_3_2.asc?at=master&fileviewer=file-view-default
    - under `test/data/logfile.asc`
"""

from datetime import datetime
import time
import logging
import re

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

    # Regex attribute names and their conversion functions
    regex_mappings = {
        "timestamp": "_process_timestamp",
        "channel": "_process_channel",
        "id": "_process_abr_id",
        "dir": "_process_tx_rx",
        "canfd": "_process_fd",
        "dlc": "_process_dlc",
        "data_length": "_process_data_length",
        "brs": "_process_brs",
        "esi": "_process_esi",
        "remote": "_process_remote",
        "error_frame": "_process_error_frame",
    }

    # CLASSIC CAN MESSAGES
    regex_classic_msg = re.compile(
        r"^(?P<timestamp>[\d.]+)\s+"
        r"(?P<channel>\d+)\s+"
        r"(?P<id>[\da-f]+x?)\s+"
        r"(?P<dir>Tx|Rx|TxRq)\s+"
        r"d\s+"
        r"(?P<dlc>[0-9a-f]{1,2})"
        r"(?:\s+(?P<data>([0-9a-f]{2}\s)*[0-9a-f]{2}))?"
        r"(?:$|\s+.*$)",
        re.IGNORECASE,
    )
    regex_classic_remote = re.compile(
        r"^(?P<timestamp>[\d.]+)\s+"
        r"(?P<channel>\d+)\s+"
        r"(?P<id>[\da-f]+x?)\s+"
        r"(?P<dir>Tx|Rx|TxRq)\s+"
        r"(?P<remote>r)"
        r"(?:$|(?:\s+(?P<dlc>[0-9a-f]+)(?:$\s+.*$))|(\s+.*$))",
        re.IGNORECASE,
    )
    regex_classic_error_frame = re.compile(
        r"^(?P<timestamp>[\d.]+)\s+"
        r"(?P<channel>\d+)\s+"
        r"(?P<error_frame>ErrorFrame)",
        re.IGNORECASE,
    )

    # CAN FD MESSAGES
    regex_fd_msg = re.compile(
        r"^(?P<timestamp>[\d.]+)\s+"
        r"(?P<canfd>CANFD)\s+"
        r"(?P<channel>\d+)\s+"
        r"(?P<dir>Tx|Rx|TxRq)\s+"
        r"(?P<id>[\da-f]+x?)\s+"
        r"(?:(?P<id_name>[a-z]\w+)\s+)?"
        r"(?P<brs>[01])\s+"
        r"(?P<esi>[01])\s+"
        r"(?P<dlc>[0-9a-f]{1,2})\s+"
        r"(?P<data_length>\d+)\s+"
        r"(?P<data>([0-9a-f]{2}\s)*[0-9a-f]{2})\s+\S",
        re.IGNORECASE,
    )
    regex_fd_remote = re.compile(
        r"^(?P<timestamp>[\d.]+)\s+"
        r"(?P<canfd>CANFD)\s+"
        r"(?P<channel>\d+)\s+"
        r"(?P<dir>Tx|Rx|TxRq)\s+"
        r"(?P<id>[\da-f]+x?)\s+"
        r"(?:(?P<id_name>[a-z]\w+)\s+)?"
        r"(?P<brs>[01])\s+"
        r"(?P<esi>[01])\s+"
        r"(?P<dlc>[0-9a-f]{1,2})\s+"
        r"(?P<remote>0)\s+",
        re.IGNORECASE,
    )
    all_regex = (
        regex_classic_msg,
        regex_fd_msg,
        regex_classic_remote,
        regex_fd_remote,
        regex_classic_error_frame,
    )

    # TODO: Add support for the following message types
    regex_fd_error_frame = re.compile(
        r"^(?P<timestamp>[\d.]+)\s+"
        r"(?P<canfd>CANFD)\s+"
        r"(?P<channel>\d+)\s+"
        r"(?P<dir>Tx|Rx|TxRq)\s+"
        r"(?P<error_frame>ErrorFrame)"
        r"(?P<error_text>.*)\s+"
        r"(?P<flags>[0-9a-f]+)\s+"
        r"(?P<code>[0-9a-f]{2})\s+"
        r"(?P<code_ext>[0-9a-f]{4})\s+"
        r"(?P<phase>Arb\.|Data?\.?)\s+"
        r"(?P<position>\d+)\s+"
        r"(?P<id>[\da-f]+x?)\s+"
        r"(?P<brs>[01])\s+"
        r"(?P<esi>[01])\s+"
        r"(?P<dlc>[0-9a-f]{1,2})\s+"
        r"(?P<data_length>\d+)\s+"
        r"(?:(?P<data>(?:[0-9a-f]{2}\s)*[0-9a-f]{2})\s+)?"
        r"\S",
        re.IGNORECASE,
    )
    regex_classic_error_event = re.compile(
        r"^(?P<timestamp>[\d.]+)\s+" r"CAN\s+" r"(?P<channel>\d+)\s+" r"Status:.*$",
        re.IGNORECASE,
    )

    def __init__(self, file, base="hex"):
        """
        :param file: a path-like object or as file-like object to read from
                     If this is a file-like object, is has to opened in text
                     read mode, not binary read mode.
        :param base: Select the base(hex or dec) of id and data.
                     If the header of the asc file contains base information,
                     this value will be overwritten. Default "hex".
        """
        super().__init__(file, mode="r")
        self.base = self._check_base(base)
        self.date = None
        self.timestamps_format = None
        self.internal_events_logged = None

    @staticmethod
    def _process_timestamp(kwargs, timestamp):
        kwargs["timestamp"] = float(timestamp)

    @staticmethod
    def _process_channel(kwargs, channel):
        # See ASCWriter
        kwargs["channel"] = int(channel) - 1

    @staticmethod
    def _process_tx_rx(kwargs, dir):
        if dir == "Rx":
            kwargs["is_rx"] = True
        else:
            kwargs["is_rx"] = False

    @staticmethod
    def _process_fd(kwargs, _):
        kwargs["is_fd"] = True

    @staticmethod
    def _process_esi(kwargs, esi):
        kwargs["error_state_indicator"] = esi == "1"

    @staticmethod
    def _process_brs(kwargs, brs):
        kwargs["bitrate_switch"] = brs == "1"

    def _process_dlc(self, kwargs, dlc):
        kwargs["dlc"] = int(dlc, self.base)

    @staticmethod
    def _process_remote(kwargs, _):
        kwargs["is_remote_frame"] = True

    @staticmethod
    def _process_error_frame(kwargs, _):
        kwargs["is_error_frame"] = True

    @staticmethod
    def _process_data_length(kwargs, data_length):
        kwargs["data_length"] = int(data_length)

    def _process_abr_id(self, kwargs, abr_id):
        if abr_id[-1:].lower() == "x":
            kwargs["arbitration_id"] = int(abr_id[0:-1], self.base)
        else:
            kwargs["arbitration_id"] = int(abr_id, self.base)
            kwargs["is_extended_id"] = False

    def _get_msg_from_regex_match(self, match):
        kwargs = {}
        regex_dict = match.groupdict()
        for key, value in regex_dict.items():
            if key not in ASCReader.regex_mappings or value is None:
                continue
            function_name = ASCReader.regex_mappings[key]
            function = getattr(self, function_name)
            function(kwargs, value)
        if "is_fd" in kwargs and "data_length" in kwargs:
            data_length = kwargs.pop("data_length")
        elif "dlc" in kwargs:
            data_length = kwargs["dlc"]
        else:
            data_length = 0
        frame = bytearray()
        if "data" in regex_dict and regex_dict["data"]:
            data = regex_dict["data"].split()
            for byte in data[0:data_length]:
                frame.append(int(byte, self.base))
        kwargs["data"] = frame
        return Message(**kwargs)

    @staticmethod
    def _check_base(base):
        if base not in ["hex", "dec"]:
            raise ValueError('base should be either "hex" or "dec"')
        return BASE_DEC if base == "dec" else BASE_HEX

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
                self.base = self._check_base(base)
                self.timestamps_format = timestamp_format
            elif lower_case.endswith("internal events logged"):
                if lower_case.startswith("no"):
                    self.internal_events_logged = False
                else:
                    self.internal_events_logged = True
            else:
                return

    def __iter__(self):
        self._extract_header()
        for line in self.file:
            temp = line.strip()
            if not temp or not temp[0].isdigit():
                continue
            for regex in ASCReader.all_regex:
                match = regex.match(temp)
                if match:
                    msg = self._get_msg_from_regex_match(match)
                    yield msg
                    break
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
    FORMAT_DATE = "%a %b %d %I:%M:%S.{} %p %Y"
    FORMAT_EVENT = "{timestamp: 9.6f} {message}\n"

    def __init__(self, file, channel=1):
        """
        :param file: a path-like object or as file-like object to write to
                     If this is a file-like object, is has to opened in text
                     write mode, not binary write mode.
        :param channel: a default channel to use when the message does not
                        have a channel set
        """
        super().__init__(file, mode="w")
        self.channel = channel

        # write start of file header
        now = datetime.now().strftime("%a %b %d %I:%M:%S.%f %p %Y")
        self.file.write("date %s\n" % now)
        self.file.write("base hex  timestamps absolute\n")
        self.file.write("internal events logged\n")

        # the last part is written with the timestamp of the first message
        self.header_written = False
        self.last_timestamp = None
        self.started = None

    def stop(self):
        if not self.file.closed:
            self.file.write("End TriggerBlock\n")
        super().stop()

    def log_event(self, message, timestamp=None):
        """Add a message to the log file.

        :param str message: an arbitrary message
        :param float timestamp: the absolute timestamp of the event
        """

        if not message:  # if empty or None
            logger.debug("ASCWriter: ignoring empty message")
            return
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

    def on_message_received(self, msg):

        if msg.is_error_frame:
            self.log_event("{}  ErrorFrame".format(self.channel), msg.timestamp)
            return
        if msg.is_remote_frame:
            dtype = "r {:x}".format(msg.dlc)  # New after v8.5
            data = []
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
