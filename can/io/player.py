"""
This module contains the generic :class:`LogReader` as
well as :class:`MessageSync` which plays back messages
in the recorded order and time intervals.
"""

import gzip
import pathlib
import time
from collections.abc import Generator, Iterable
from typing import (
    Any,
    Final,
)

from .._entry_points import read_entry_points
from ..message import Message
from ..typechecking import StringPathLike
from .asc import ASCReader
from .blf import BLFReader
from .canutils import CanutilsLogReader
from .csv import CSVReader
from .generic import BinaryIOMessageReader, MessageReader, TextIOMessageReader
from .mf4 import MF4Reader
from .sqlite import SqliteReader
from .trc import TRCReader

#: A map of file suffixes to their corresponding
#: :class:`can.io.generic.MessageReader` class
MESSAGE_READERS: Final[dict[str, type[MessageReader]]] = {
    ".asc": ASCReader,
    ".blf": BLFReader,
    ".csv": CSVReader,
    ".db": SqliteReader,
    ".log": CanutilsLogReader,
    ".mf4": MF4Reader,
    ".trc": TRCReader,
}


def _update_reader_plugins() -> None:
    """Update available message reader plugins from entry points."""
    for entry_point in read_entry_points("can.io.message_reader"):
        if entry_point.key in MESSAGE_READERS:
            continue

        reader_class = entry_point.load()
        if issubclass(reader_class, MessageReader):
            MESSAGE_READERS[entry_point.key] = reader_class


def _get_logger_for_suffix(suffix: str) -> type[MessageReader]:
    """Find MessageReader class for given suffix."""
    try:
        return MESSAGE_READERS[suffix]
    except KeyError:
        raise ValueError(f'No read support for unknown log format "{suffix}"') from None


def _decompress(filename: StringPathLike, **kwargs: Any) -> MessageReader:
    """
    Return the suffix and io object of the decompressed file.
    """
    suffixes = pathlib.Path(filename).suffixes
    if len(suffixes) != 2:
        raise ValueError(
            f"No read support for unknown log format \"{''.join(suffixes)}\""
        )

    real_suffix = suffixes[-2].lower()
    reader_type = _get_logger_for_suffix(real_suffix)

    if issubclass(reader_type, TextIOMessageReader):
        return reader_type(gzip.open(filename, mode="rt"), **kwargs)
    elif issubclass(reader_type, BinaryIOMessageReader):
        return reader_type(gzip.open(filename, mode="rb"), **kwargs)

    raise ValueError(f"No read support for unknown log format \"{''.join(suffixes)}\"")


def LogReader(filename: StringPathLike, **kwargs: Any) -> MessageReader:  # noqa: N802
    """Find and return the appropriate :class:`~can.io.generic.MessageReader` instance
    for a given file suffix.

    The format is determined from the file suffix which can be one of:
      * .asc :class:`can.ASCReader`
      * .blf :class:`can.BLFReader`
      * .csv :class:`can.CSVReader`
      * .db :class:`can.SqliteReader`
      * .log :class:`can.CanutilsLogReader`
      * .mf4 :class:`can.MF4Reader`
        (optional, depends on `asammdf <https://github.com/danielhrisca/asammdf>`_)
      * .trc :class:`can.TRCReader`

    Gzip compressed files can be used as long as the original
    files suffix is one of the above (e.g. filename.asc.gz).


    Exposes a simple iterator interface, to use simply::

        for msg in can.LogReader("some/path/to/my_file.log"):
            print(msg)

    :param filename:
        the filename/path of the file to read from
    :raises ValueError:
        if the filename's suffix is of an unknown file type

    .. note::
        There are no time delays, if you want to reproduce the measured
        delays between messages look at the :class:`can.MessageSync` class.

    .. note::
        This function itself is just a dispatcher, and any positional and keyword
        arguments are passed on to the returned instance.
    """

    _update_reader_plugins()

    suffix = pathlib.PurePath(filename).suffix.lower()
    if suffix == ".gz":
        return _decompress(filename)

    reader_type = _get_logger_for_suffix(suffix)
    return reader_type(file=filename, **kwargs)


class MessageSync:
    """
    Used to iterate over some given messages in the recorded time.
    """

    def __init__(
        self,
        messages: Iterable[Message],
        timestamps: bool = True,
        gap: float = 0.0001,
        skip: float = 60.0,
        *,
        skip_gaps: bool = False,
    ) -> None:
        """Creates an new **MessageSync** instance.

        :param messages: An iterable of :class:`can.Message` instances.
        :param timestamps: Use the messages' timestamps. If False, uses the *gap* parameter
                           as the time between messages.
        :param gap: Minimum time between sent messages in seconds
        :param skip: Cap remaining playback waits at this many seconds. Zero
                     disables capping and preserves the recorded delays.
        :param skip_gaps: With recorded timestamps, remove remaining waits greater
                          than *skip* instead of capping them. Defaults to False.
                          Has no effect when *skip* is zero or *timestamps* is False.

        Example::

            import can

            with can.LogReader("my_logfile.asc") as reader, can.Bus(interface="virtual") as bus:
                for msg in can.MessageSync(messages=reader):
                    print(msg)
                    bus.send(msg)

        """
        self.raw_messages = messages
        self.timestamps = timestamps
        self.gap = gap
        self.skip = skip
        self.skip_gaps = skip_gaps

    def __iter__(self) -> Generator[Message, None, None]:
        t_wakeup = playback_start_time = time.perf_counter()
        recorded_start_time = None
        t_skipped = 0.0

        for message in self.raw_messages:
            # Work out the correct wait time
            if self.timestamps:
                if recorded_start_time is None:
                    recorded_start_time = message.timestamp

                t_wakeup = playback_start_time + (
                    message.timestamp - t_skipped - recorded_start_time
                )
            else:
                t_wakeup += self.gap

            sleep_period = t_wakeup - time.perf_counter()

            if self.skip and sleep_period > self.skip:
                delay = 0.0 if self.timestamps and self.skip_gaps else self.skip
                t_skipped += sleep_period - delay
                sleep_period = delay

            if sleep_period > 1e-4:
                time.sleep(sleep_period)

            yield message
