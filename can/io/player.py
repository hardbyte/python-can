#!/usr/bin/env python
# coding: utf-8

"""
This module contains the generic :class:`LogReader` as
well as :class:`MessageSync` which plays back messages
in the recorded order an time intervals.
"""

from __future__ import absolute_import

import time
import logging

from .generic import BaseIOHandler
from .asc import ASCReader
from .blf import BLFReader
from .canutils import CanutilsLogReader
from .csv import CSVReader
from .sqlite import SqliteReader

log = logging.getLogger('can.io.player')


class LogReader(BaseIOHandler):
    """
    Replay logged CAN messages from a file.

    The format is determined from the file format which can be one of:
      * .asc
      * .blf
      * .csv
      * .db
      * .log

    Exposes a simple iterator interface, to use simply:

        >>> for msg in LogReader("some/path/to/my_file.log"):
        ...     print(msg)

    .. note::
        There are no time delays, if you want to reproduce the measured
        delays between messages look at the :class:`can.MessageSync` class.

    .. note::
        This class itself is just a dispatcher, and any positional an keyword
        arguments are passed on to the returned instance.
    """

    @staticmethod
    def __new__(cls, filename, *args, **kwargs):
        """
        :param str filename: the filename/path the file to read from
        """
        if filename.endswith(".asc"):
            return ASCReader(filename, *args, **kwargs)
        elif filename.endswith(".blf"):
            return BLFReader(filename, *args, **kwargs)
        elif filename.endswith(".csv"):
            return CSVReader(filename, *args, **kwargs)
        elif filename.endswith(".db"):
            return SqliteReader(filename, *args, **kwargs)
        elif filename.endswith(".log"):
            return CanutilsLogReader(filename, *args, **kwargs)
        else:
            raise NotImplementedError("No read support for this log format: {}".format(filename))


class MessageSync(object):
    """
    Used to iterate over some given messages in the recorded time.
    """

    def __init__(self, messages, timestamps=True, gap=0.0001, skip=60):
        """Creates an new **MessageSync** instance.

        :param messages: An iterable of :class:`can.Message` instances.
        :param bool timestamps: Use the messages' timestamps.
        :param float gap: Minimum time between sent messages in seconds
        :param float skip: Skip periods of inactivity greater than this (in seconds).
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
