# coding: utf-8

"""
Contains handling of MF4 logging files.

MF4 files represent Measurement Data Format (MDF) version 4 as specified by
the ASAM MDF standard (see https://www.asam.net/standards/detail/mdf/)

"""

from __future__ import absolute_import

from datetime import datetime
from pathlib import Path
import logging

import numpy as np

from ..message import Message
from ..listener import Listener
from ..util import channel2int
from .generic import BaseIOHandler

try:
    from asammdf import MDF, Signal

    CAN_MSG_EXT = 0x80000000
    CAN_ID_MASK = 0x1FFFFFFF

    DTYPE = np.dtype(
        [
            ('BusChannel', '<u1'),
            ('ID', '<u4'),
            ('IDE', '<u1'),
            ('DLC', '<u1'),
            ('DataLength', '<u1'),
            ('DataBytes', '(64,)u1'),
            ('Dir', '<u1'),
            ('EDL', '<u1'),
            ('BRS', '<u1'),
            ('ESI', '<u1'),
        ]
    )

    RTR_DTYPE = np.dtype(
        [
            ('BusChannel', '<u1'),
            ('ID', '<u4'),
            ('IDE', '<u1'),
            ('DLC', '<u1'),
            ('Dir', '<u1'),
        ]
    )

    FD_LEN2DLC = {
        12: 9,
        16: 10,
        20: 11,
        24: 12,
        32: 13,
        48: 14,
        64: 15,
    }

    FD_DLC2LEN = {
        value: key
        for key, value in FD_LEN2DLC.items()
    }

    logger = logging.getLogger('can.io.mf4')


    class MF4Writer(BaseIOHandler, Listener):
        """Logs CAN data to an ASAM Measurement Data File v4 (.mf4).

        If a message has a timestamp smaller than the previous one or None,
        it gets assigned the timestamp that was written for the last message.
        It the first message does not have a timestamp, it is set to zero.
        """

        def __init__(self, file, database=None):
            """
            :param file: a path-like object or as file-like object to write to
                         If this is a file-like object, is has to opened in
                         binary write mode, not text write mode.
            :param database: optional path to a DBC or ARXML file that contains
                             message description.
            """
            super(MF4Writer, self).__init__(file, mode='r+b')
            now = datetime.now()
            self._mdf = MDF()
            self._mdf.header.start_time = now
            self.last_timestamp = self._start_time = now.timestamp()

            if database:
                database = Path(database).resolve()
                if database.exists():
                    data = database.read_bytes()
                    attachment = data, database.name
                else:
                    attachment = None
            else:
                attachment = None

            # standard frames group
            self._mdf.append(
                Signal(
                    name="CAN_DataFrame",
                    samples=np.array([], dtype=DTYPE),
                    timestamps=np.array([], dtype='<f8'),
                    attachment=attachment,
                )
            )

            # error frames group
            self._mdf.append(
                Signal(
                    name="CAN_ErrorFrame",
                    samples=np.array([], dtype=DTYPE),
                    timestamps=np.array([], dtype='<f8'),
                    attachment=attachment,
                )
            )

            # remote frames group
            self._mdf.append(
                Signal(
                    name="CAN_DataFrame",
                    samples=np.array([], dtype=RTR_DTYPE),
                    timestamps=np.array([], dtype='<f8'),
                    attachment=attachment,
                )
            )

            self._buffer = np.zeros(1, dtype=DTYPE)
            self._rtr_buffer = np.zeros(1, dtype=RTR_DTYPE)

        def stop(self):
            self._mdf.save(self.file, compression=2)
            self._mdf.close()
            super(MF4Writer, self).stop()

        def on_message_received(self, msg):

            channel = channel2int(msg.channel)

            buffer = self._buffer
            rtr_buffer = self._rtr_buffer

            if msg.is_remote_frame:
                if channel is not None:
                    rtr_buffer['BusChannel'] = channel

                rtr_buffer['ID'] = msg.arbitration_id
                rtr_buffer['IDE'] = int(msg.is_extended_id)
                rtr_buffer['DLC'] = msg.dlc

            else:
                if channel is not None:
                    buffer['BusChannel'] = channel

                buffer['ID'] = msg.arbitration_id
                buffer['IDE'] = int(msg.is_extended_id)
                data = msg.data
                size = len(data)
                buffer['DataLength'] = size
                buffer['DataBytes'][0, :size] = data
                if msg.is_fd:
                    buffer['DLC'] = FD_LEN2DLC[size]
                    buffer['ESI'] = int(msg.error_state_indicator)
                    buffer['BRS'] = int(msg.bitrate_switch)
                    buffer['EDL'] = 1
                else:
                    buffer['DLC'] = size
                    buffer['ESI'] = 0
                    buffer['BRS'] = 0
                    buffer['EDL'] = 0

            timestamp = msg.timestamp
            if timestamp is None:
                timestamp = self.last_timestamp
            else:
                self.last_timestamp = max(
                    self.last_timestamp,
                    timestamp,
                )

            if msg.is_remote_frame:
                sigs = [
                    ([self.last_timestamp], None)
                    (rtr_buffer, None)
                ]
            else:
                sigs = [
                    ([self.last_timestamp], None)
                    (buffer, None)
                ]

            if msg.is_remote_frame:
                self._mdf.extend(2, sigs)
            elif msg.is_error_frame:
                self._mdf.extend(1, sigs)
            else:
                self._mdf.extend(0, sigs)


    class MF4Reader(BaseIOHandler):
        """
        Iterator of CAN messages from a MF4 logging file.

        """

        def __init__(self, file):
            """
            :param file: a path-like object or as file-like object to read from
                         If this is a file-like object, is has to opened in
                         binary read mode, not text read mode.
            """
            self.start_timestamp = datetime.now().timestamp()
            super(MF4Reader, self).__init__(file, mode='rb')

            self._mdf = MDF(file)

            masters = [
                self._mdf.get_master(i, copy_master=False)
                for i in range(3)
            ]

            masters = [
                np.core.records.fromarrays(
                    (master, np.ones(len(master)))
                )
                for master in masters
            ]

            self.masters = np.sort(masters)

        def __iter__(self):
            standard_counter = 0
            error_counter = 0
            rtr_counter = 0

            for timestamp, group_index in self.masters:

                # standard frames
                if group_index == 0:
                    sample = self._mdf.get(
                        'CAN_DataFrame',
                        group=group_index,
                        raw=True,
                        record_offset=standard_counter,
                        record_count=1,
                    )

                    if sample['CAN_DataFrame.EDL'] == 0:

                        is_extended_id = bool(sample['CAN_DataFrame.IDE'])
                        channel = sample['CAN_DataFrame.ID']
                        arbitration_id = int(sample['CAN_DataFrame.ID'])
                        size = int(sample['CAN_DataFrame.DataLength'])
                        dlc = int(sample['CAN_DataFrame.DLC'])
                        data = sample['CAN_DataFrame.DataBytes'][:size].tobytes()

                        msg = Message(
                            timestamp=timestamp + self.start_timestamp,
                            is_error_frame=False,
                            is_remote_frame=False,
                            if_fd=False,
                            is_extended_id=is_extended_id,
                            channel=channel,
                            arbitration_id=arbitration_id,
                            data=data,
                            dlc=dlc,
                        )

                    else:
                        is_extended_id = bool(sample['CAN_DataFrame.IDE'])
                        channel = sample['CAN_DataFrame.ID']
                        arbitration_id = int(sample['CAN_DataFrame.ID'])
                        size = int(sample['CAN_DataFrame.DataLength'])
                        dlc = FD_DLC2LEN(sample['CAN_DataFrame.DLC'])
                        data = sample['CAN_DataFrame.DataBytes'][:size].tobytes()
                        error_state_indicator = int(sample['CAN_DataFrame.ESI'])
                        bitrate_switch = int(sample['CAN_DataFrame.BRS'])

                        msg = Message(
                            timestamp=timestamp + self.start_timestamp,
                            is_error_frame=False,
                            is_remote_frame=False,
                            if_fd=True,
                            is_extended_id=is_extended_id,
                            channel=channel,
                            arbitration_id=arbitration_id,
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
                        'CAN_ErrorFrame',
                        group=group_index,
                        raw=True,
                        record_offset=error_counter,
                        record_count=1,
                    )

                    if sample['CAN_ErrorFrame.EDL'] == 0:

                        is_extended_id = bool(sample['CAN_ErrorFrame.IDE'])
                        channel = sample['CAN_ErrorFrame.ID']
                        arbitration_id = int(sample['CAN_ErrorFrame.ID'])
                        size = int(sample['CAN_ErrorFrame.DataLength'])
                        dlc = int(sample['CAN_ErrorFrame.DLC'])
                        data = sample['CAN_ErrorFrame.DataBytes'][:size].tobytes()

                        msg = Message(
                            timestamp=timestamp + self.start_timestamp,
                            is_error_frame=True,
                            is_remote_frame=False,
                            if_fd=False,
                            is_extended_id=is_extended_id,
                            channel=channel,
                            arbitration_id=arbitration_id,
                            data=data,
                            dlc=dlc,
                        )

                    else:
                        is_extended_id = bool(sample['CAN_ErrorFrame.IDE'])
                        channel = sample['CAN_ErrorFrame.ID']
                        arbitration_id = int(sample['CAN_ErrorFrame.ID'])
                        size = int(sample['CAN_ErrorFrame.DataLength'])
                        dlc = FD_DLC2LEN(sample['CAN_ErrorFrame.DLC'])
                        data = sample['CAN_ErrorFrame.DataBytes'][:size].tobytes()
                        error_state_indicator = int(sample['CAN_ErrorFrame.ESI'])
                        bitrate_switch = int(sample['CAN_ErrorFrame.BRS'])

                        msg = Message(
                            timestamp=timestamp + self.start_timestamp,
                            is_error_frame=True,
                            is_remote_frame=False,
                            if_fd=True,
                            is_extended_id=is_extended_id,
                            channel=channel,
                            arbitration_id=arbitration_id,
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
                        'CAN_DataFrame',
                        group=group_index,
                        raw=True,
                        record_offset=rtr_counter,
                        record_count=1,
                    )

                    if sample['CAN_DataFrame.EDL'] == 0:

                        is_extended_id = bool(sample['CAN_DataFrame.IDE'])
                        channel = sample['CAN_DataFrame.ID']
                        arbitration_id = int(sample['CAN_DataFrame.ID'])
                        dlc = int(sample['CAN_DataFrame.DLC'])

                        msg = Message(
                            timestamp=timestamp + self.start_timestamp,
                            is_error_frame=False,
                            is_remote_frame=True,
                            if_fd=False,
                            is_extended_id=is_extended_id,
                            channel=channel,
                            arbitration_id=arbitration_id,
                            dlc=dlc,
                        )

                        yield msg

                    else:
                        logger.warning("CAN FD does not have remote frames")

                    rtr_counter += 1

            self.stop()

        def stop(self):
            self._mdf.close()
            super(MF4Writer, self).stop()

    ASAMMDF_AVAILABLE = True

except ImportError:
    ASAMMDF_AVAILABLE = False
