"""
Contains handling of MF4 logging files.

MF4 files represent Measurement Data Format (MDF) version 4 as specified by
the ASAM MDF standard (see https://www.asam.net/standards/detail/mdf/)
"""

import logging
from datetime import datetime
from hashlib import md5
from io import BufferedIOBase, BytesIO
from pathlib import Path
from typing import Any, BinaryIO, Generator, Optional, Union, cast

from ..message import Message
from ..typechecking import StringPathLike
from ..util import channel2int, dlc2len, len2dlc
from .generic import BinaryIOMessageReader, BinaryIOMessageWriter

logger = logging.getLogger("can.io.mf4")

try:
    import asammdf
    import numpy as np
    from asammdf import Signal
    from asammdf.blocks.mdf_v4 import MDF4
    from asammdf.blocks.v4_blocks import SourceInformation
    from asammdf.blocks.v4_constants import BUS_TYPE_CAN, SOURCE_BUS
    from asammdf.mdf import MDF

    STD_DTYPE = np.dtype(
        [
            ("CAN_DataFrame.BusChannel", "<u1"),
            ("CAN_DataFrame.ID", "<u4"),
            ("CAN_DataFrame.IDE", "<u1"),
            ("CAN_DataFrame.DLC", "<u1"),
            ("CAN_DataFrame.DataLength", "<u1"),
            ("CAN_DataFrame.DataBytes", "(64,)u1"),
            ("CAN_DataFrame.Dir", "<u1"),
            ("CAN_DataFrame.EDL", "<u1"),
            ("CAN_DataFrame.BRS", "<u1"),
            ("CAN_DataFrame.ESI", "<u1"),
        ]
    )

    ERR_DTYPE = np.dtype(
        [
            ("CAN_ErrorFrame.BusChannel", "<u1"),
            ("CAN_ErrorFrame.ID", "<u4"),
            ("CAN_ErrorFrame.IDE", "<u1"),
            ("CAN_ErrorFrame.DLC", "<u1"),
            ("CAN_ErrorFrame.DataLength", "<u1"),
            ("CAN_ErrorFrame.DataBytes", "(64,)u1"),
            ("CAN_ErrorFrame.Dir", "<u1"),
            ("CAN_ErrorFrame.EDL", "<u1"),
            ("CAN_ErrorFrame.BRS", "<u1"),
            ("CAN_ErrorFrame.ESI", "<u1"),
        ]
    )

    RTR_DTYPE = np.dtype(
        [
            ("CAN_RemoteFrame.BusChannel", "<u1"),
            ("CAN_RemoteFrame.ID", "<u4"),
            ("CAN_RemoteFrame.IDE", "<u1"),
            ("CAN_RemoteFrame.DLC", "<u1"),
            ("CAN_RemoteFrame.DataLength", "<u1"),
            ("CAN_RemoteFrame.Dir", "<u1"),
        ]
    )
except ImportError:
    asammdf = None


CAN_MSG_EXT = 0x80000000
CAN_ID_MASK = 0x1FFFFFFF


class MF4Writer(BinaryIOMessageWriter):
    """Logs CAN data to an ASAM Measurement Data File v4 (.mf4).

    MF4Writer does not support append mode.

    If a message has a timestamp smaller than the previous one or None,
    it gets assigned the timestamp that was written for the last message.
    It the first message does not have a timestamp, it is set to zero.
    """

    def __init__(
        self,
        file: Union[StringPathLike, BinaryIO],
        database: Optional[StringPathLike] = None,
        compression_level: int = 2,
        **kwargs: Any,
    ) -> None:
        """
        :param file:
            A path-like object or as file-like object to write to.
            If this is a file-like object, is has to be opened in
            binary write mode, not text write mode.
        :param database:
            optional path to a DBC or ARXML file that contains message description.
        :param compression_level:
            compression option as integer (default 2)
            * 0 - no compression
            * 1 - deflate (slower, but produces smaller files)
            * 2 - transposition + deflate (slowest, but produces the smallest files)
        """
        if asammdf is None:
            raise NotImplementedError(
                "The asammdf package was not found. Install python-can with "
                "the optional dependency [mf4] to use the MF4Writer."
            )

        if kwargs.get("append", False):
            raise ValueError(
                f"{self.__class__.__name__} is currently not equipped to "
                f"append messages to an existing file."
            )

        super().__init__(file, mode="w+b")
        now = datetime.now()
        self._mdf = cast(MDF4, MDF(version="4.10"))
        self._mdf.header.start_time = now
        self.last_timestamp = self._start_time = now.timestamp()

        self._compression_level = compression_level

        if database:
            database = Path(database).resolve()
            if database.exists():
                data = database.read_bytes()
                attachment = data, database.name, md5(data).digest()
            else:
                attachment = None
        else:
            attachment = None

        acquisition_source = SourceInformation(
            source_type=SOURCE_BUS, bus_type=BUS_TYPE_CAN
        )

        # standard frames group
        self._mdf.append(
            Signal(
                name="CAN_DataFrame",
                samples=np.array([], dtype=STD_DTYPE),
                timestamps=np.array([], dtype="<f8"),
                attachment=attachment,
                source=acquisition_source,
            )
        )

        # error frames group
        self._mdf.append(
            Signal(
                name="CAN_ErrorFrame",
                samples=np.array([], dtype=ERR_DTYPE),
                timestamps=np.array([], dtype="<f8"),
                attachment=attachment,
                source=acquisition_source,
            )
        )

        # remote frames group
        self._mdf.append(
            Signal(
                name="CAN_RemoteFrame",
                samples=np.array([], dtype=RTR_DTYPE),
                timestamps=np.array([], dtype="<f8"),
                attachment=attachment,
                source=acquisition_source,
            )
        )

        self._std_buffer = np.zeros(1, dtype=STD_DTYPE)
        self._err_buffer = np.zeros(1, dtype=ERR_DTYPE)
        self._rtr_buffer = np.zeros(1, dtype=RTR_DTYPE)

    def file_size(self) -> int:
        """Return an estimate of the current file size in bytes."""
        # TODO: find solution without accessing private attributes of asammdf
        return cast(int, self._mdf._tempfile.tell())  # pylint: disable=protected-access

    def stop(self) -> None:
        self._mdf.save(self.file, compression=self._compression_level)
        self._mdf.close()
        super().stop()

    def on_message_received(self, msg: Message) -> None:
        channel = channel2int(msg.channel)

        timestamp = msg.timestamp
        if timestamp is None:
            timestamp = self.last_timestamp
        else:
            self.last_timestamp = max(self.last_timestamp, timestamp)

        timestamp -= self._start_time

        if msg.is_remote_frame:
            if channel is not None:
                self._rtr_buffer["CAN_RemoteFrame.BusChannel"] = channel

            self._rtr_buffer["CAN_RemoteFrame.ID"] = msg.arbitration_id
            self._rtr_buffer["CAN_RemoteFrame.IDE"] = int(msg.is_extended_id)
            self._rtr_buffer["CAN_RemoteFrame.Dir"] = 0 if msg.is_rx else 1
            self._rtr_buffer["CAN_RemoteFrame.DLC"] = msg.dlc

            sigs = [(np.array([timestamp]), None), (self._rtr_buffer, None)]
            self._mdf.extend(2, sigs)

        elif msg.is_error_frame:
            if channel is not None:
                self._err_buffer["CAN_ErrorFrame.BusChannel"] = channel

            self._err_buffer["CAN_ErrorFrame.ID"] = msg.arbitration_id
            self._err_buffer["CAN_ErrorFrame.IDE"] = int(msg.is_extended_id)
            self._err_buffer["CAN_ErrorFrame.Dir"] = 0 if msg.is_rx else 1
            data = msg.data
            size = len(data)
            self._err_buffer["CAN_ErrorFrame.DataLength"] = size
            self._err_buffer["CAN_ErrorFrame.DataBytes"][0, :size] = data
            if msg.is_fd:
                self._err_buffer["CAN_ErrorFrame.DLC"] = len2dlc(msg.dlc)
                self._err_buffer["CAN_ErrorFrame.ESI"] = int(msg.error_state_indicator)
                self._err_buffer["CAN_ErrorFrame.BRS"] = int(msg.bitrate_switch)
                self._err_buffer["CAN_ErrorFrame.EDL"] = 1
            else:
                self._err_buffer["CAN_ErrorFrame.DLC"] = msg.dlc
                self._err_buffer["CAN_ErrorFrame.ESI"] = 0
                self._err_buffer["CAN_ErrorFrame.BRS"] = 0
                self._err_buffer["CAN_ErrorFrame.EDL"] = 0

            sigs = [(np.array([timestamp]), None), (self._err_buffer, None)]
            self._mdf.extend(1, sigs)

        else:
            if channel is not None:
                self._std_buffer["CAN_DataFrame.BusChannel"] = channel

            self._std_buffer["CAN_DataFrame.ID"] = msg.arbitration_id
            self._std_buffer["CAN_DataFrame.IDE"] = int(msg.is_extended_id)
            self._std_buffer["CAN_DataFrame.Dir"] = 0 if msg.is_rx else 1
            data = msg.data
            size = len(data)
            self._std_buffer["CAN_DataFrame.DataLength"] = size
            self._std_buffer["CAN_DataFrame.DataBytes"][0, :size] = data
            if msg.is_fd:
                self._std_buffer["CAN_DataFrame.DLC"] = len2dlc(msg.dlc)
                self._std_buffer["CAN_DataFrame.ESI"] = int(msg.error_state_indicator)
                self._std_buffer["CAN_DataFrame.BRS"] = int(msg.bitrate_switch)
                self._std_buffer["CAN_DataFrame.EDL"] = 1
            else:
                self._std_buffer["CAN_DataFrame.DLC"] = msg.dlc
                self._std_buffer["CAN_DataFrame.ESI"] = 0
                self._std_buffer["CAN_DataFrame.BRS"] = 0
                self._std_buffer["CAN_DataFrame.EDL"] = 0

            sigs = [(np.array([timestamp]), None), (self._std_buffer, None)]
            self._mdf.extend(0, sigs)

        # reset buffer structure
        self._std_buffer = np.zeros(1, dtype=STD_DTYPE)
        self._err_buffer = np.zeros(1, dtype=ERR_DTYPE)
        self._rtr_buffer = np.zeros(1, dtype=RTR_DTYPE)


class MF4Reader(BinaryIOMessageReader):
    """
    Iterator of CAN messages from a MF4 logging file.

    The MF4Reader only supports MF4 files that were recorded with python-can.
    """

    def __init__(
        self,
        file: Union[StringPathLike, BinaryIO],
        **kwargs: Any,
    ) -> None:
        """
        :param file: a path-like object or as file-like object to read from
                        If this is a file-like object, is has to be opened in
                        binary read mode, not text read mode.
        """
        if asammdf is None:
            raise NotImplementedError(
                "The asammdf package was not found. Install python-can with "
                "the optional dependency [mf4] to use the MF4Reader."
            )

        super().__init__(file, mode="rb")

        self._mdf: MDF4
        if isinstance(file, BufferedIOBase):
            self._mdf = MDF(BytesIO(file.read()))
        else:
            self._mdf = MDF(file)

        self.start_timestamp = self._mdf.header.start_time.timestamp()

        masters = [self._mdf.get_master(i) for i in range(3)]

        masters = [
            np.core.records.fromarrays((master, np.ones(len(master)) * i))
            for i, master in enumerate(masters)
        ]

        self.masters = np.sort(np.concatenate(masters))

    def __iter__(self) -> Generator[Message, None, None]:
        standard_counter = 0
        error_counter = 0
        rtr_counter = 0

        for timestamp, group_index in self.masters:
            # standard frames
            if group_index == 0:
                sample = self._mdf.get(
                    "CAN_DataFrame",
                    group=group_index,
                    raw=True,
                    record_offset=standard_counter,
                    record_count=1,
                )

                try:
                    channel = int(sample["CAN_DataFrame.BusChannel"][0])
                except ValueError:
                    channel = None

                if sample["CAN_DataFrame.EDL"] == 0:
                    is_extended_id = bool(sample["CAN_DataFrame.IDE"][0])
                    arbitration_id = int(sample["CAN_DataFrame.ID"][0])
                    is_rx = int(sample["CAN_DataFrame.Dir"][0]) == 0
                    size = int(sample["CAN_DataFrame.DataLength"][0])
                    dlc = int(sample["CAN_DataFrame.DLC"][0])
                    data = sample["CAN_DataFrame.DataBytes"][0, :size].tobytes()

                    msg = Message(
                        timestamp=timestamp + self.start_timestamp,
                        is_error_frame=False,
                        is_remote_frame=False,
                        is_fd=False,
                        is_extended_id=is_extended_id,
                        channel=channel,
                        is_rx=is_rx,
                        arbitration_id=arbitration_id,
                        data=data,
                        dlc=dlc,
                    )

                else:
                    is_extended_id = bool(sample["CAN_DataFrame.IDE"][0])
                    arbitration_id = int(sample["CAN_DataFrame.ID"][0])
                    is_rx = int(sample["CAN_DataFrame.Dir"][0]) == 0
                    size = int(sample["CAN_DataFrame.DataLength"][0])
                    dlc = dlc2len(sample["CAN_DataFrame.DLC"][0])
                    data = sample["CAN_DataFrame.DataBytes"][0, :size].tobytes()
                    error_state_indicator = bool(sample["CAN_DataFrame.ESI"][0])
                    bitrate_switch = bool(sample["CAN_DataFrame.BRS"][0])

                    msg = Message(
                        timestamp=timestamp + self.start_timestamp,
                        is_error_frame=False,
                        is_remote_frame=False,
                        is_fd=True,
                        is_extended_id=is_extended_id,
                        channel=channel,
                        arbitration_id=arbitration_id,
                        is_rx=is_rx,
                        data=data,
                        dlc=dlc,
                        bitrate_switch=bitrate_switch,
                        error_state_indicator=error_state_indicator,
                    )

                yield msg
                standard_counter += 1

            # error frames
            elif group_index == 1:
                sample = self._mdf.get(
                    "CAN_ErrorFrame",
                    group=group_index,
                    raw=True,
                    record_offset=error_counter,
                    record_count=1,
                )

                try:
                    channel = int(sample["CAN_ErrorFrame.BusChannel"][0])
                except ValueError:
                    channel = None

                if sample["CAN_ErrorFrame.EDL"] == 0:
                    is_extended_id = bool(sample["CAN_ErrorFrame.IDE"][0])
                    arbitration_id = int(sample["CAN_ErrorFrame.ID"][0])
                    is_rx = int(sample["CAN_ErrorFrame.Dir"][0]) == 0
                    size = int(sample["CAN_ErrorFrame.DataLength"][0])
                    dlc = int(sample["CAN_ErrorFrame.DLC"][0])
                    data = sample["CAN_ErrorFrame.DataBytes"][0, :size].tobytes()

                    msg = Message(
                        timestamp=timestamp + self.start_timestamp,
                        is_error_frame=True,
                        is_remote_frame=False,
                        is_fd=False,
                        is_extended_id=is_extended_id,
                        channel=channel,
                        arbitration_id=arbitration_id,
                        is_rx=is_rx,
                        data=data,
                        dlc=dlc,
                    )

                else:
                    is_extended_id = bool(sample["CAN_ErrorFrame.IDE"][0])
                    arbitration_id = int(sample["CAN_ErrorFrame.ID"][0])
                    is_rx = int(sample["CAN_ErrorFrame.Dir"][0]) == 0
                    size = int(sample["CAN_ErrorFrame.DataLength"][0])
                    dlc = dlc2len(sample["CAN_ErrorFrame.DLC"][0])
                    data = sample["CAN_ErrorFrame.DataBytes"][0, :size].tobytes()
                    error_state_indicator = bool(sample["CAN_ErrorFrame.ESI"][0])
                    bitrate_switch = bool(sample["CAN_ErrorFrame.BRS"][0])

                    msg = Message(
                        timestamp=timestamp + self.start_timestamp,
                        is_error_frame=True,
                        is_remote_frame=False,
                        is_fd=True,
                        is_extended_id=is_extended_id,
                        channel=channel,
                        arbitration_id=arbitration_id,
                        is_rx=is_rx,
                        data=data,
                        dlc=dlc,
                        bitrate_switch=bitrate_switch,
                        error_state_indicator=error_state_indicator,
                    )

                yield msg
                error_counter += 1

            # remote frames
            else:
                sample = self._mdf.get(
                    "CAN_RemoteFrame",
                    group=group_index,
                    raw=True,
                    record_offset=rtr_counter,
                    record_count=1,
                )

                try:
                    channel = int(sample["CAN_RemoteFrame.BusChannel"][0])
                except ValueError:
                    channel = None

                is_extended_id = bool(sample["CAN_RemoteFrame.IDE"][0])
                arbitration_id = int(sample["CAN_RemoteFrame.ID"][0])
                is_rx = int(sample["CAN_RemoteFrame.Dir"][0]) == 0
                dlc = int(sample["CAN_RemoteFrame.DLC"][0])

                msg = Message(
                    timestamp=timestamp + self.start_timestamp,
                    is_error_frame=False,
                    is_remote_frame=True,
                    is_fd=False,
                    is_extended_id=is_extended_id,
                    channel=channel,
                    arbitration_id=arbitration_id,
                    is_rx=is_rx,
                    dlc=dlc,
                )

                yield msg

                rtr_counter += 1

        self.stop()

    def stop(self) -> None:
        self._mdf.close()
        super().stop()
