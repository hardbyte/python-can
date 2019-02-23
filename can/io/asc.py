# coding: utf-8

"""
Contains handling of ASC logging files.

Example .asc files:
    - https://bitbucket.org/tobylorenz/vector_asc/src/47556e1a6d32c859224ca62d075e1efcc67fa690/src/Vector/ASC/tests/unittests/data/CAN_Log_Trigger_3_2.asc?at=master&fileviewer=file-view-default
    - under `test/data/logfile.asc`
"""

from __future__ import absolute_import

from datetime import datetime
import time
import logging

from ..message import Message
from ..listener import Listener
from ..util import channel2int
from .generic import BaseIOHandler


CAN_MSG_EXT = 0x80000000
CAN_ID_MASK = 0x1FFFFFFF

logger = logging.getLogger('can.io.asc')


class ASCReader(BaseIOHandler):
    """
    Iterator of CAN messages from a ASC logging file.

    TODO: turn relative timestamps back to absolute form
    """

    def __init__(self, file):
        """
        :param file: a path-like object or as file-like object to read from
                     If this is a file-like object, is has to opened in text
                     read mode, not binary read mode.
        """
        super(ASCReader, self).__init__(file, mode='r')

    @staticmethod
    def _extract_can_id(str_can_id):
        if str_can_id[-1:].lower() == 'x':
            is_extended = True
            can_id = int(str_can_id[0:-1], 16)
        else:
            is_extended = False
            can_id = int(str_can_id, 16)
        return can_id, is_extended

    def __iter__(self):
        for line in self.file:
            #logger.debug("ASCReader: parsing line: '%s'", line.splitlines()[0])

            temp = line.strip()
            if not temp or not temp[0].isdigit():
                continue

            try:
                timestamp, channel, dummy = temp.split(None, 2) # , frameType, dlc, frameData
            except ValueError:
                # we parsed an empty comment
                continue

            timestamp = float(timestamp)
            try:
                # See ASCWriter
                channel = int(channel) - 1
            except ValueError:
                pass

            if dummy.strip()[0:10].lower() == 'errorframe':
                msg = Message(timestamp=timestamp, is_error_frame=True,
                              channel=channel)
                yield msg

            elif not isinstance(channel, int) or dummy.strip()[0:10].lower() == 'statistic:':
                pass

            elif dummy[-1:].lower() == 'r':
                can_id_str, _ = dummy.split(None, 1)
                can_id_num, is_extended_id = self._extract_can_id(can_id_str)
                msg = Message(timestamp=timestamp,
                              arbitration_id=can_id_num & CAN_ID_MASK,
                              is_extended_id=is_extended_id,
                              is_remote_frame=True,
                              channel=channel)
                yield msg

            else:
                try:
                    # this only works if dlc > 0 and thus data is availabe
                    can_id_str, _, _, dlc, data = dummy.split(None, 4)
                except ValueError:
                    # but if not, we only want to get the stuff up to the dlc
                    can_id_str, _, _, dlc       = dummy.split(None, 3)
                    # and we set data to an empty sequence manually
                    data = ''

                dlc = int(dlc)
                frame = bytearray()
                data = data.split()
                for byte in data[0:dlc]:
                    frame.append(int(byte, 16))

                can_id_num, is_extended_id = self._extract_can_id(can_id_str)

                yield Message(
                    timestamp=timestamp,
                    arbitration_id=can_id_num & CAN_ID_MASK,
                    is_extended_id=is_extended_id,
                    is_remote_frame=False,
                    dlc=dlc,
                    data=frame,
                    channel=channel
                )

        self.stop()


class ASCWriter(BaseIOHandler, Listener):
    """Logs CAN data to an ASCII log file (.asc).

    The measurement starts with the timestamp of the first registered message.
    If a message has a timestamp smaller than the previous one or None,
    it gets assigned the timestamp that was written for the last message.
    It the first message does not have a timestamp, it is set to zero.
    """

    FORMAT_MESSAGE = "{channel}  {id:<15} Rx   {dtype} {data}"
    FORMAT_DATE = "%a %b %m %I:%M:%S.{} %p %Y"
    FORMAT_EVENT = "{timestamp: 9.6f} {message}\n"

    def __init__(self, file, channel=1):
        """
        :param file: a path-like object or as file-like object to write to
                     If this is a file-like object, is has to opened in text
                     write mode, not binary write mode.
        :param channel: a default channel to use when the message does not
                        have a channel set
        """
        super(ASCWriter, self).__init__(file, mode='w')
        self.channel = channel

        # write start of file header
        now = datetime.now().strftime("%a %b %m %I:%M:%S.%f %p %Y")
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
        super(ASCWriter, self).stop()

    def log_event(self, message, timestamp=None):
        """Add a message to the log file.

        :param str message: an arbitrary message
        :param float timestamp: the absolute timestamp of the event
        """

        if not message: # if empty or None
            logger.debug("ASCWriter: ignoring empty message")
            return

        # this is the case for the very first message:
        if not self.header_written:
            self.last_timestamp = (timestamp or 0.0)
            self.started = self.last_timestamp
            mlsec = repr(self.last_timestamp).split('.')[1][:3]
            formatted_date = time.strftime(self.FORMAT_DATE.format(mlsec), time.localtime(self.last_timestamp))
            self.file.write("Begin Triggerblock %s\n" % formatted_date)
            self.header_written = True
            self.log_event("Start of measurement") # caution: this is a recursive call!

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
            dtype = 'r'
            data = []
        else:
            dtype = "d {}".format(msg.dlc)
            data = ["{:02X}".format(byte) for byte in msg.data]

        arb_id = "{:X}".format(msg.arbitration_id)
        if msg.is_extended_id:
            arb_id += 'x'

        channel = channel2int(msg.channel)
        if channel is None:
            channel = self.channel
        else:
            # Many interfaces start channel numbering at 0 which is invalid
            channel += 1

        serialized = self.FORMAT_MESSAGE.format(channel=channel,
                                                id=arb_id,
                                                dtype=dtype,
                                                data=' '.join(data))

        self.log_event(serialized, msg.timestamp)
