"""
This module contains the generic :class:`LogReader` as
well as :class:`MessageSync` which plays back messages
in the recorded order and time intervals.
"""
import gzip
import pathlib
import time
from typing import Any, Dict, Generator, Iterable, Optional, Tuple, Type, Union, cast

from .._entry_points import read_entry_points
from ..message import Message
from ..typechecking import AcceptedIOType, FileLike, StringPathLike
from .asc import ASCReader
from .blf import BLFReader
from .canutils import CanutilsLogReader
from .csv import CSVReader
from .generic import BinaryIOMessageReader, MessageReader
from .mf4 import MF4Reader
from .sqlite import SqliteReader
from .trc import TRCReader


class LogReader(MessageReader):
    """
    Replay logged CAN messages from a file.

    The format is determined from the file suffix which can be one of:
      * .asc
      * .blf
      * .csv
      * .db
      * .log
      * .mf4 (optional, depends on asammdf)
      * .trc

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
    message_readers: Dict[str, Optional[Type[MessageReader]]] = {
        ".asc": ASCReader,
        ".blf": BLFReader,
        ".csv": CSVReader,
        ".db": SqliteReader,
        ".log": CanutilsLogReader,
        ".mf4": MF4Reader,
        ".trc": TRCReader,
    }

    @staticmethod
    def __new__(  # type: ignore
        cls: Any,
        filename: StringPathLike,
        **kwargs: Any,
    ) -> MessageReader:
        """
        :param filename: the filename/path of the file to read from
        :raises ValueError: if the filename's suffix is of an unknown file type
        """
        if not LogReader.fetched_plugins:
            LogReader.message_readers.update(
                {
                    reader.key: cast(Type[MessageReader], reader.load())
                    for reader in read_entry_points("can.io.message_reader")
                }
            )
            LogReader.fetched_plugins = True

        suffix = pathlib.PurePath(filename).suffix.lower()

        file_or_filename: AcceptedIOType = filename
        if suffix == ".gz":
            reader_type, file_or_filename = LogReader.decompress(filename)
        else:
            reader_type = cls._get_logger_for_suffix(suffix)
        return reader_type(file=file_or_filename, **kwargs)

    @classmethod
    def _get_logger_for_suffix(cls, suffix: str) -> Type[MessageReader]:
        try:
            reader_type = LogReader.message_readers[suffix]
        except KeyError:
            raise ValueError(
                f'No read support for this unknown log format "{suffix}"'
            ) from None
        if reader_type is None:
            raise ImportError(f"failed to import reader for extension {suffix}")
        return reader_type

    @classmethod
    def decompress(
        cls,
        filename: StringPathLike,
    ) -> Tuple[Type[MessageReader], Union[str, FileLike]]:
        """
        Return the suffix and io object of the decompressed file.
        """
        real_suffix = pathlib.Path(filename).suffixes[-2].lower()
        reader_type = cls._get_logger_for_suffix(real_suffix)

        mode = "rb" if issubclass(reader_type, BinaryIOMessageReader) else "rt"

        return reader_type, gzip.open(filename, mode)

    def __iter__(self) -> Generator[Message, None, None]:
        raise NotImplementedError()


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
                t_skipped += sleep_period - self.skip
                sleep_period = self.skip

            if sleep_period > 1e-4:
                time.sleep(sleep_period)

            yield message
