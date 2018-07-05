#!/usr/bin/env python
# coding: utf-8

"""
See the :class:`Logger` class.
"""

from __future__ import absolute_import

import logging

from .asc import ASCWriter
from .blf import BLFWriter
from .canutils import CanutilsLogWriter
from .csv import CSVWriter
from .sqlite import SqliteWriter
from .printer import Printer

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

    Note this class itself is just a dispatcher, an object that inherits
    from Listener will be created when instantiating this class.
    """

    @staticmethod
    def __new__(cls, filename):
        """
        :param str filename: the filename/path the file to write to
        """
        if filename.endswith(".asc"):
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
