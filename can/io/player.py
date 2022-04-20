"""
This module contains the generic :class:`LogReader` as
well as :class:`MessageSync` which plays back messages
in the recorded order an time intervals.
"""
import gzip
import pathlib
from time import time, sleep
import typing

from pkg_resources import iter_entry_points

from .generic import MessageReader
from .asc import ASCReader
from .blf import BLFReader
from .canutils import CanutilsLogReader
from .csv import CSVReader
from .sqlite import SqliteReader
from ..typechecking import StringPathLike, FileLike, AcceptedIOType
from ..message import Message


class LogReader(MessageReader):
    """
    Replay logged CAN messages from a file.

    The format is determined from the file suffix which can be one of:
      * .asc
      * .blf
      * .csv
      * .db
      * .log

    Gzip compressed files can be used as long as the original
    files suffix is one of the above (e.g. filename.asc.gz).


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

    fetched_plugins = False
    message_readers: typing.Dict[str, typing.Type[MessageReader]] = {
        ".asc": ASCReader,
        ".blf": BLFReader,
        ".csv": CSVReader,
        ".db": SqliteReader,
        ".log": CanutilsLogReader,
    }

    @staticmethod
    def __new__(  # type: ignore
        cls: typing.Any,
        filename: StringPathLike,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> MessageReader:
        """
        :param filename: the filename/path of the file to read from
        :raises ValueError: if the filename's suffix is of an unknown file type
        """
        if not LogReader.fetched_plugins:
            LogReader.message_readers.update(
                {
                    reader.name: reader.load()
                    for reader in iter_entry_points("can.io.message_reader")
                }
            )
            LogReader.fetched_plugins = True

        suffix = pathlib.PurePath(filename).suffix.lower()

        file_or_filename: AcceptedIOType = filename
        if suffix == ".gz":
            suffix, file_or_filename = LogReader.decompress(filename)
        try:
            return LogReader.message_readers[suffix](file_or_filename, *args, **kwargs)
        except KeyError:
            raise ValueError(
                f'No read support for this unknown log format "{suffix}"'
            ) from None

    @staticmethod
    def decompress(
        filename: StringPathLike,
    ) -> typing.Tuple[str, typing.Union[str, FileLike]]:
        """
        Return the suffix and io object of the decompressed file.
        """
        real_suffix = pathlib.Path(filename).suffixes[-2].lower()
        mode = "rb" if real_suffix == ".blf" else "rt"

        return real_suffix, gzip.open(filename, mode)

    def __iter__(self) -> typing.Generator[Message, None, None]:
        pass


class MessageSync:  # pylint: disable=too-few-public-methods
    """
    Used to iterate over some given messages in the recorded time.
    """

    def __init__(
        self,
        messages: typing.Iterable[Message],
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

    def __iter__(self) -> typing.Generator[Message, None, None]:
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
