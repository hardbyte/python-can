# coding: utf-8

"""
See the :class:`Logger` class.
"""

import logging
import pathlib
import typing

from ..listener import Listener
from .generic import BaseIOHandler
from .asc import ASCWriter
from .blf import BLFWriter
from .canutils import CanutilsLogWriter
from .csv import CSVWriter
from .sqlite import SqliteWriter
from .printer import Printer

import can.typechecking

log = logging.getLogger("can.io.logger")


class Logger(BaseIOHandler, Listener):  # pylint: disable=abstract-method
    """
    Logs CAN messages to a file.

    The format is determined from the file format which can be one of:
      * .asc: :class:`can.ASCWriter`
      * .blf :class:`can.BLFWriter`
      * .csv: :class:`can.CSVWriter`
      * .db: :class:`can.SqliteWriter`
      * .log :class:`can.CanutilsLogWriter`

    The **filename** may also be *None*, to fall back to :class:`can.Printer`.

    The log files may be incomplete until `stop()` is called due to buffering.

    .. note::
        This class itself is just a dispatcher, and any positional and keyword
        arguments are passed on to the returned instance.
    """

    @staticmethod
    def __new__(cls, filename: typing.Optional[can.typechecking.PathLike], *args, **kwargs):
        """
        :param filename: the filename/path of the file to write to,
                         may be a path-like object or None to
                         instantiate a :class:`~can.Printer`
        """
        if filename is None:
            return Printer(*args, **kwargs)

        suffix = pathlib.PurePath(filename).suffix
        if suffix == ".asc":
            return ASCWriter(filename, *args, **kwargs)
        if suffix == ".blf":
            return BLFWriter(filename, *args, **kwargs)
        if suffix == ".csv":
            return CSVWriter(filename, *args, **kwargs)
        if suffix == ".db":
            return SqliteWriter(filename, *args, **kwargs)
        if suffix == ".log":
            return CanutilsLogWriter(filename, *args, **kwargs)

        raise ValueError(f'unknown file type "{filename}"')
