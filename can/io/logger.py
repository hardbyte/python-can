"""
See the :class:`Logger` class.
"""

import os
import pathlib
from abc import ABC, abstractmethod
from datetime import datetime
import gzip
from typing import Any, Optional, Callable, Type, Tuple, cast, Dict, Set

from types import TracebackType

from typing_extensions import Literal
from pkg_resources import iter_entry_points

from ..message import Message
from ..listener import Listener
from .generic import BaseIOHandler, FileIOMessageWriter, MessageWriter
from .asc import ASCWriter
from .blf import BLFWriter
from .canutils import CanutilsLogWriter
from .csv import CSVWriter
from .sqlite import SqliteWriter
from .printer import Printer
from .trc import TRCWriter
from ..typechecking import StringPathLike, FileLike, AcceptedIOType


class Logger(MessageWriter):  # pylint: disable=abstract-method
    """
    Logs CAN messages to a file.

    The format is determined from the file suffix which can be one of:
      * .asc: :class:`can.ASCWriter`
      * .blf :class:`can.BLFWriter`
      * .csv: :class:`can.CSVWriter`
      * .db: :class:`can.SqliteWriter`
      * .log :class:`can.CanutilsLogWriter`
      * .trc :class:`can.TRCWriter`
      * .txt :class:`can.Printer`

    Any of these formats can be used with gzip compression by appending
    the suffix .gz (e.g. filename.asc.gz). However, third-party tools might not
    be able to read these files.

    The **filename** may also be *None*, to fall back to :class:`can.Printer`.

    The log files may be incomplete until `stop()` is called due to buffering.

    .. note::
        This class itself is just a dispatcher, and any positional and keyword
        arguments are passed on to the returned instance.
    """

    fetched_plugins = False
    message_writers: Dict[str, Type[MessageWriter]] = {
        ".asc": ASCWriter,
        ".blf": BLFWriter,
        ".csv": CSVWriter,
        ".db": SqliteWriter,
        ".log": CanutilsLogWriter,
        ".trc": TRCWriter,
        ".txt": Printer,
    }

    @staticmethod
    def __new__(  # type: ignore
        cls: Any, filename: Optional[StringPathLike], *args: Any, **kwargs: Any
    ) -> MessageWriter:
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

        suffix = pathlib.PurePath(filename).suffix.lower()

        file_or_filename: AcceptedIOType = filename
        if suffix == ".gz":
            suffix, file_or_filename = Logger.compress(filename, *args, **kwargs)

        try:
            return Logger.message_writers[suffix](file_or_filename, *args, **kwargs)
        except KeyError:
            raise ValueError(
                f'No write support for this unknown log format "{suffix}"'
            ) from None

    @staticmethod
    def compress(
        filename: StringPathLike, *args: Any, **kwargs: Any
    ) -> Tuple[str, FileLike]:
        """
        Return the suffix and io object of the decompressed file.
        File will automatically recompress upon close.
        """
        real_suffix = pathlib.Path(filename).suffixes[-2].lower()
        if real_suffix in (".blf", ".db"):
            raise ValueError(
                f"The file type {real_suffix} is currently incompatible with gzip."
            )
        if kwargs.get("append", False):
            mode = "ab" if real_suffix == ".blf" else "at"
        else:
            mode = "wb" if real_suffix == ".blf" else "wt"

        return real_suffix, gzip.open(filename, mode)

    def on_message_received(self, msg: Message) -> None:
        pass


class BaseRotatingLogger(Listener, BaseIOHandler, ABC):
    """
    Base class for rotating CAN loggers. This class is not meant to be
    instantiated directly. Subclasses must implement the :meth:`should_rollover`
    and :meth:`do_rollover` methods according to their rotation strategy.

    The rotation behavior can be further customized by the user by setting
    the :attr:`namer` and :attr:`rotator` attributes after instantiating the subclass.

    These attributes as well as the methods :meth:`rotation_filename` and :meth:`rotate`
    and the corresponding docstrings are carried over from the python builtin
    :class:`~logging.handlers.BaseRotatingHandler`.

    Subclasses must set the `_writer` attribute upon initialization.
    """

    _supported_formats: Set[str] = set()

    #: If this attribute is set to a callable, the :meth:`~BaseRotatingLogger.rotation_filename`
    #: method delegates to this callable. The parameters passed to the callable are
    #: those passed to :meth:`~BaseRotatingLogger.rotation_filename`.
    namer: Optional[Callable[[StringPathLike], StringPathLike]] = None

    #: If this attribute is set to a callable, the :meth:`~BaseRotatingLogger.rotate` method
    #: delegates to this callable. The parameters passed to the callable are those
    #: passed to :meth:`~BaseRotatingLogger.rotate`.
    rotator: Optional[Callable[[StringPathLike, StringPathLike], None]] = None

    #: An integer counter to track the number of rollovers.
    rollover_count: int = 0

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        Listener.__init__(self)
        BaseIOHandler.__init__(self, None)

        self.writer_args = args
        self.writer_kwargs = kwargs

        # Expected to be set by the subclass
        self._writer: FileIOMessageWriter = None  # type: ignore

    @property
    def writer(self) -> FileIOMessageWriter:
        """This attribute holds an instance of a writer class which manages the actual file IO."""
        return self._writer

    def rotation_filename(self, default_name: StringPathLike) -> StringPathLike:
        """Modify the filename of a log file when rotating.

        This is provided so that a custom filename can be provided.
        The default implementation calls the :attr:`namer` attribute of the
        handler, if it's callable, passing the default name to
        it. If the attribute isn't callable (the default is :obj:`None`), the name
        is returned unchanged.

        :param default_name:
            The default name for the log file.
        """
        if not callable(self.namer):
            return default_name

        return self.namer(default_name)

    def rotate(self, source: StringPathLike, dest: StringPathLike) -> None:
        """When rotating, rotate the current log.

        The default implementation calls the :attr:`rotator` attribute of the
        handler, if it's callable, passing the `source` and `dest` arguments to
        it. If the attribute isn't callable (the default is :obj:`None`), the source
        is simply renamed to the destination.

        :param source:
            The source filename. This is normally the base
            filename, e.g. `"test.log"`
        :param dest:
            The destination filename. This is normally
            what the source is rotated to, e.g. `"test_#001.log"`.
        """
        if not callable(self.rotator):
            if os.path.exists(source):
                os.rename(source, dest)
        else:
            self.rotator(source, dest)

    def on_message_received(self, msg: Message) -> None:
        """This method is called to handle the given message.

        :param msg:
            the delivered message
        """
        if self.should_rollover(msg):
            self.do_rollover()
            self.rollover_count += 1

        self.writer.on_message_received(msg)

    def _get_new_writer(self, filename: StringPathLike) -> FileIOMessageWriter:
        """Instantiate a new writer.

        .. note::
            The :attr:`self.writer` should be closed prior to calling this function.

        :param filename:
            Path-like object that specifies the location and name of the log file.
            The log file format is defined by the suffix of `filename`.
        :return:
            An instance of a writer class.
        """
        suffix = "".join(pathlib.Path(filename).suffixes[-2:]).lower()

        if suffix in self._supported_formats:
            logger = Logger(filename, *self.writer_args, **self.writer_kwargs)
            if isinstance(logger, FileIOMessageWriter):
                return logger
            elif isinstance(logger, Printer) and logger.file is not None:
                return cast(FileIOMessageWriter, logger)

        raise Exception(
            f'The log format "{suffix}" '
            f"is not supported by {self.__class__.__name__}. "
            f"{self.__class__.__name__} supports the following formats: "
            f"{', '.join(self._supported_formats)}"
        )

    def stop(self) -> None:
        """Stop handling new messages.

        Carry out any final tasks to ensure
        data is persisted and cleanup any open resources.
        """
        self.writer.stop()

    def __enter__(self) -> "BaseRotatingLogger":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Literal[False]:
        return self._writer.__exit__(exc_type, exc_val, exc_tb)

    @abstractmethod
    def should_rollover(self, msg: Message) -> bool:
        """Determine if the rollover conditions are met."""

    @abstractmethod
    def do_rollover(self) -> None:
        """Perform rollover."""


class SizedRotatingLogger(BaseRotatingLogger):
    """Log CAN messages to a sequence of files with a given maximum size.

    The logger creates a log file with the given `base_filename`. When the
    size threshold is reached the current log file is closed and renamed
    by adding a timestamp and the rollover count. A new log file is then
    created and written to.

    This behavior can be customized by setting the
    :attr:`~can.io.BaseRotatingLogger.namer` and
    :attr:`~can.io.BaseRotatingLogger.rotator`
    attribute.

    Example::

        from can import Notifier, SizedRotatingLogger
        from can.interfaces.vector import VectorBus

        bus = VectorBus(channel=[0], app_name="CANape", fd=True)

        logger = SizedRotatingLogger(
            base_filename="my_logfile.asc",
            max_bytes=5 * 1024 ** 2,  # =5MB
        )
        logger.rollover_count = 23  # start counter at 23

        notifier = Notifier(bus=bus, listeners=[logger])

    The SizedRotatingLogger currently supports the formats
      * .asc: :class:`can.ASCWriter`
      * .blf :class:`can.BLFWriter`
      * .csv: :class:`can.CSVWriter`
      * .log :class:`can.CanutilsLogWriter`
      * .txt :class:`can.Printer` (if pointing to a file)

    .. note::
        The :class:`can.SqliteWriter` is not supported yet.

    The log files on disk may be incomplete due to buffering until
    :meth:`~can.Listener.stop` is called.
    """

    _supported_formats = {".asc", ".blf", ".csv", ".log", ".txt"}

    def __init__(
        self,
        base_filename: StringPathLike,
        max_bytes: int = 0,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        :param base_filename:
            A path-like object for the base filename. The log file format is defined by
            the suffix of `base_filename`.
        :param max_bytes:
            The size threshold at which a new log file shall be created. If set to 0, no
            rollover will be performed.
        """
        super().__init__(*args, **kwargs)

        self.base_filename = os.path.abspath(base_filename)
        self.max_bytes = max_bytes

        self._writer = self._get_new_writer(self.base_filename)

    def should_rollover(self, msg: Message) -> bool:
        if self.max_bytes <= 0:
            return False

        if self.writer.file_size() >= self.max_bytes:
            return True

        return False

    def do_rollover(self) -> None:
        if self.writer:
            self.writer.stop()

        sfn = self.base_filename
        dfn = self.rotation_filename(self._default_name())
        self.rotate(sfn, dfn)

        self._writer = self._get_new_writer(self.base_filename)

    def _default_name(self) -> StringPathLike:
        """Generate the default rotation filename."""
        path = pathlib.Path(self.base_filename)
        new_name = (
            path.stem.split(".")[0]
            + "_"
            + datetime.now().strftime("%Y-%m-%dT%H%M%S")
            + "_"
            + f"#{self.rollover_count:03}"
            + "".join(path.suffixes[-2:])
        )
        return str(path.parent / new_name)
