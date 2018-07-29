#!/usr/bin/env python
# coding: utf-8

"""
See the :class:`Logger` class.
"""

from __future__ import absolute_import

import logging

from ..listener import Listener
from .generic import BaseIOHandler
from .asc import ASCWriter
from .blf import BLFWriter
from .canutils import CanutilsLogWriter
from .csv import CSVWriter
from .sqlite import SqliteWriter
from .printer import Printer

log = logging.getLogger("can.io.logger")


class Logger(BaseIOHandler, Listener):
    """
    Logs CAN messages to a file.

    The format is determined from the file format which can be one of:
      * .asc: :class:`can.ASCWriter`
      * .blf :class:`can.BLFWriter`
      * .csv: :class:`can.CSVWriter`
      * .db: :class:`can.SqliteWriter`
      * .log :class:`can.CanutilsLogWriter`
      * other: :class:`can.Printer`

    .. note::
        This class itself is just a dispatcher, and any positional an keyword
        arguments are passed on to the returned instance.
    """

    @staticmethod
    def __new__(cls, filename, *args, **kwargs):
        """
        :type filename: str or None or path-like
        :param filename: the filename/path the file to write to,
                         may be a path-like object if the target logger supports
                         it, and may be None to instantiate a :class:`~can.Printer`

        """
        if filename:
            if filename.endswith(".asc"):
                return ASCWriter(filename, *args, **kwargs)
            elif filename.endswith(".blf"):
                return BLFWriter(filename, *args, **kwargs)
            elif filename.endswith(".csv"):
                return CSVWriter(filename, *args, **kwargs)
            elif filename.endswith(".db"):
                return SqliteWriter(filename, *args, **kwargs)
            elif filename.endswith(".log"):
                return CanutilsLogWriter(filename, *args, **kwargs)

        # else:
        log.info('unknown file type "%s", falling pack to can.Printer', filename)
        return Printer(filename, *args, **kwargs)
