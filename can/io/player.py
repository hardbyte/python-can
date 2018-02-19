from __future__ import print_function
import time
import logging

from .asc import ASCReader
from .log import CanutilsLogReader
from .blf import BLFReader
from .sqlite import SqliteReader

log = logging.getLogger('can.io.player')


class LogReader(object):
    """
    Replay logged CAN messages from a file.

    The format is determined from the file format which can be one of:
      * .asc
      * .blf
      * .csv
      * .db

    Exposes a simple iterator interface, to use simply:

        >>> for m in LogReader(my_file):
        ...     print(m)

    Note there are no time delays, if you want to reproduce
    the measured delays between messages look at the
    :class:`can.util.MessageSync` class.
    """

    @classmethod
    def __new__(cls, other, filename):
        if filename.endswith(".blf"):
            return BLFReader(filename)
        if filename.endswith(".db"):
            return SqliteReader(filename)
        if filename.endswith(".asc"):
            return ASCReader(filename)
        if filename.endswith(".log"):
            return CanutilsLogReader(filename)
        
        raise NotImplementedError("No read support for this log format")


class MessageSync(object):

    def __init__(self, messages, timestamps=True, gap=0.0001, skip=60):
        """

        :param messages: An iterable of :class:`can.Message` instances.
        :param timestamps: Use the messages' timestamps.
        :param gap: Minimum time between sent messages
        :param skip: Skip periods of inactivity greater than this.
        """
        self.raw_messages = messages
        self.timestamps = timestamps
        self.gap = gap
        self.skip = skip

    def __iter__(self):
        log.debug("Iterating over messages at real speed")
        playback_start_time = time.time()
        recorded_start_time = None

        for m in self.raw_messages:
            if recorded_start_time is None:
                recorded_start_time = m.timestamp

            if self.timestamps:
                # Work out the correct wait time
                now = time.time()
                current_offset = now - playback_start_time
                recorded_offset_from_start = m.timestamp - recorded_start_time
                remaining_gap = recorded_offset_from_start - current_offset

                sleep_period = max(self.gap, min(self.skip, remaining_gap))
            else:
                sleep_period = self.gap

            time.sleep(sleep_period)
            yield m
