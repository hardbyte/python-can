# coding: utf-8

"""
This module contains the generic :class:`LogReader` as
well as :class:`MessageSync` which plays back messages
in the recorded order an time intervals.
"""

import pathlib
from time import time, sleep
import typing

if typing.TYPE_CHECKING:
    import can

from .generic import BaseIOHandler
from .asc import ASCReader
from .blf import BLFReader
from .canutils import CanutilsLogReader
from .csv import CSVReader
from .sqlite import SqliteReader


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
    def __new__(cls, filename: "can.typechecking.PathLike", *args, **kwargs):
        """
        :param filename: the filename/path of the file to read from
        :raises ValueError: if the filename's suffix is of an unknown file type
        """
        suffix = pathlib.PurePath(filename).suffix

        lookup = {
            ".asc": ASCReader,
            ".blf": BLFReader,
            ".csv": CSVReader,
            ".db": SqliteReader,
            ".log": CanutilsLogReader,
        }
        suffix = pathlib.PurePath(filename).suffix
        try:
            return lookup[suffix](filename, *args, **kwargs)
        except KeyError:
            raise ValueError(
                f'No read support for this unknown log format "{suffix}"'
            ) from None


class MessageSync:  # pylint: disable=too-few-public-methods
    """
    Used to iterate over some given messages in the recorded time.
    """

    def __init__(
        self,
        messages: typing.Iterable["can.Message"],
        timestamps: bool = True,
        gap: float = 0.0001,
        skip: float = 60.0,
    ) -> None:
        """Creates an new **MessageSync** instance.

        :param messages: An iterable of :class:`can.Message` instances.
        :param timestamps: Use the messages' timestamps. If False, uses the *gap* parameter
                           as the time between messages.
        :param gap: Minimum time between sent messages in seconds
        :param skip: Skip periods of inactivity greater than this (in seconds).
        """
        self.raw_messages = messages
        self.timestamps = timestamps
        self.gap = gap
        self.skip = skip

    def __iter__(self) -> typing.Generator["can.Message", None, None]:
        playback_start_time = time()
        recorded_start_time = None

        for message in self.raw_messages:

            # Work out the correct wait time
            if self.timestamps:
                if recorded_start_time is None:
                    recorded_start_time = message.timestamp

                now = time()
                current_offset = now - playback_start_time
                recorded_offset_from_start = message.timestamp - recorded_start_time
                remaining_gap = max(0.0, recorded_offset_from_start - current_offset)

                sleep_period = max(self.gap, min(self.skip, remaining_gap))
            else:
                sleep_period = self.gap

            sleep(sleep_period)

            yield message
