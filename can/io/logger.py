#!/usr/bin/env python
# coding: utf-8

"""
See the :class:`Logger` class.
"""

import logging

from .asc import ASCWriter
from .blf import BLFWriter
from .csv import CSVWriter
from .log import CanutilsLogWriter
from .sqlite import SqliteWriter
from .stdout import Printer

log = logging.getLogger("can.io.logger")


class Logger(object):
    """
    Logs CAN messages to a file.

    The format is determined from the file format which can be one of:
      * .asc: :class:`can.ASCWriter`
      * .blf :class:`can.BLFWriter`
      * .csv: :class:`can.CSVWriter`
      * .db: :class:`can.SqliteWriter`
      * .log :class:`can.CanutilsLogWriter`
      * other: :class:`can.Printer`

    Note this class itself is just a dispatcher,
    an object that inherits from Listener will
    be created when instantiating this class.
    """

    @classmethod
    def __new__(cls, other, filename):
        if not filename:
            return Printer()
        elif filename.endswith(".asc"):
            return ASCWriter(filename)
        elif filename.endswith(".blf"):
            return BLFWriter(filename)
        elif filename.endswith(".csv"):
            return CSVWriter(filename)
        elif filename.endswith(".db"):
            return SqliteWriter(filename)
        elif filename.endswith(".log"):
            return CanutilsLogWriter(filename)
        else:
            log.info('unknown file type "%s", falling pack to can.Printer', filename)
            return Printer(filename)
