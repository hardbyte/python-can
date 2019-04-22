# coding: utf-8

"""
Contains handling of MF4 logging files.

"""

from __future__ import absolute_import

from datetime import datetime
from pathlib import Path
import logging

from ..listener import Listener
from ..util import channel2int
from .generic import BaseIOHandler

import numpy as np

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
            sigs = [
                Signal(
                    name="CAN_DataFrame",
                    samples=np.array([], dtype=DTYPE),
                    timestamps=np.array([], dtype='<f8'),
                    attachment=attachment,
                )
            ]
            self._mdf.append(sigs)

            # error frames group
            sigs = [
                Signal(
                    name="CAN_ErrorFrame",
                    samples=np.array([], dtype=DTYPE),
                    timestamps=np.array([], dtype='<f8'),
                    attachment=attachment,
                )
            ]
            self._mdf.append(sigs)

            # remote frames group
            sigs = [
                Signal(
                    name="CAN_DataFrame",
                    samples=np.array([], dtype=RTR_DTYPE),
                    timestamps=np.array([], dtype='<f8'),
                    attachment=attachment,
                )
            ]
            self._mdf.append(sigs)

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

    ASAMMDF_AVAILABLE = True

except ImportError:
    ASAMMDF_AVAILABLE = False
