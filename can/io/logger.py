"""
See the :class:`Logger` class.
"""

import pathlib
from typing import Optional, Callable

from pkg_resources import iter_entry_points
import can.typechecking

from ..message import Message
from ..listener import Listener
from .generic import BaseIOHandler, MessageWriter
from .asc import ASCWriter
from .blf import BLFWriter
from .canutils import CanutilsLogWriter
from .csv import CSVWriter
from .sqlite import SqliteWriter
from .printer import Printer


class Logger(BaseIOHandler, Listener):  # pylint: disable=abstract-method
    """
    Logs CAN messages to a file.

    The format is determined from the file format which can be one of:
      * .asc: :class:`can.ASCWriter`
      * .blf :class:`can.BLFWriter`
      * .csv: :class:`can.CSVWriter`
      * .db: :class:`can.SqliteWriter`
      * .log :class:`can.CanutilsLogWriter`
      * .txt :class:`can.Printer`

    The **filename** may also be *None*, to fall back to :class:`can.Printer`.

    The log files may be incomplete until `stop()` is called due to buffering.

    .. note::
        This class itself is just a dispatcher, and any positional and keyword
        arguments are passed on to the returned instance.
    """

    fetched_plugins = False
    message_writers = {
        ".asc": ASCWriter,
        ".blf": BLFWriter,
        ".csv": CSVWriter,
        ".db": SqliteWriter,
        ".log": CanutilsLogWriter,
        ".txt": Printer,
    }

    @staticmethod
    def __new__(
        cls, filename: Optional[can.typechecking.StringPathLike], *args, **kwargs
    ):
        """
        :param filename: the filename/path of the file to write to,
                         may be a path-like object or None to
                         instantiate a :class:`~can.Printer`
        :raises ValueError: if the filename's suffix is of an unknown file type
        """
        if filename is None:
            return Printer(*args, **kwargs)

        if not Logger.fetched_plugins:
            Logger.message_writers.update(
                {
                    writer.name: writer.load()
                    for writer in iter_entry_points("can.io.message_writer")
                }
            )
            Logger.fetched_plugins = True

        suffix = pathlib.PurePath(filename).suffix
        try:
            return Logger.message_writers[suffix](filename, *args, **kwargs)
        except KeyError:
            raise ValueError(
                f'No write support for this unknown log format "{suffix}"'
            ) from None


class RotatingFileLogger(Listener):
    """Log CAN messages to a sequence of files with a given maximum size.

    The log file name and path must be returned by the function`filename_func`
    as a path-like object (e.g. a string). The log file format is defined by
    the suffix of the path-like object.

    The RotatingFileLogger currently supports
      * .asc: :class:`can.ASCWriter`
      * .blf :class:`can.BLFWriter`
      * .csv: :class:`can.CSVWriter`
      * .log :class:`can.CanutilsLogWriter`
      * .txt :class:`can.Printer`

    The log files may be incomplete until `stop()` is called due to buffering.

    Example::

        from can import Notifier
        from can.interfaces.vector import VectorBus
        from can import RotatingFileLogger

        bus = VectorBus(channel=[0], app_name="CANape", fd=True)
        logger = RotatingFileLogger(
            filename_func=lambda idx: f"CAN_Log_{idx:03}.txt",  # filename with three digit counter
            max_bytes=5 * 1024 ** 2,  # =5MB
            initial_file_number=23,  # start with number 23
        )
        notifier = Notifier(bus=bus, listeners=[logger])

    """

    supported_writers = {
        ".asc": ASCWriter,
        ".blf": BLFWriter,
        ".csv": CSVWriter,
        ".log": CanutilsLogWriter,
        ".txt": Printer,
    }

    def __init__(
        self,
        filename_func: Callable[[int], can.typechecking.StringPathLike],
        max_bytes: int,
        initial_file_number: int = 0,
        *args,
        **kwargs,
    ):
        """
        :param filename_func:
            A function or lambda expression that returns the path of the new
            log file e.g. `lambda file_number: f"C:\\my_can_logfile_{file_number:03}.asc"`.
        :param max_bytes:
            The file size threshold in bytes at which a new file is created.
        :param initial_file_number:
            The first log file will start with number `initial_file_number`.
        :raises ValueError:
            The filename's suffix is not supported.
        """
        self.filename_func = filename_func
        self.max_bytes = max_bytes
        self.file_number = initial_file_number

        self.writer_args = args
        self.writer_kwargs = kwargs

        self.writer: MessageWriter = self._get_new_writer()

    def on_message_received(self, msg: Message):
        if self.writer.file is not None and self.writer.file.tell() >= self.max_bytes:
            self.writer.stop()
            self.file_number += 1
            self.writer = self._get_new_writer()

        self.writer.on_message_received(msg)

    def on_error(self, exc: Exception):
        self.writer.on_error(exc)

    def stop(self):
        self.writer.stop()

    def _get_new_writer(self) -> MessageWriter:
        filename = self.filename_func(self.file_number)
        suffix = pathlib.Path(filename).suffix.lower()
        try:
            writer_class = self.supported_writers[suffix]
        except KeyError:
            raise ValueError(
                f'Log format "{suffix} is not supported by RotatingFileLogger."'
            )
        return writer_class(filename, *self.writer_args, **self.writer_kwargs)
