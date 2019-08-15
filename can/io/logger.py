# coding: utf-8

"""
See the :class:`Logger` class.
"""

import pathlib
import typing

import can.typechecking

from ..listener import Listener
from .generic import BaseIOHandler
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

    @staticmethod
    def __new__(
        cls, filename: typing.Optional[can.typechecking.StringPathLike], *args, **kwargs
    ):
        """
        :param filename: the filename/path of the file to write to,
                         may be a path-like object or None to
                         instantiate a :class:`~can.Printer`
        :raises ValueError: if the filename's suffix is of an unknown file type
        """
        if filename is None:
            return Printer(*args, **kwargs)

        lookup = {
            ".asc": ASCWriter,
            ".blf": BLFWriter,
            ".csv": CSVWriter,
            ".db": SqliteWriter,
            ".log": CanutilsLogWriter,
            ".txt": Printer,
        }
        suffix = pathlib.PurePath(filename).suffix
        try:
            return lookup[suffix](filename, *args, **kwargs)
        except KeyError:
            raise ValueError(
                f'No write support for this unknown log format "{suffix}"'
            ) from None
