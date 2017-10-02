"""
can is an object-orient Controller Area Network interface module.
"""
from __future__ import absolute_import

import logging

__version__ = "2.0.0-beta.1"

log = logging.getLogger('can')

rc = dict()


class CanError(IOError):
    pass

from can.listener import Listener, BufferedReader, RedirectReader

from can.formated_io import Logger, Printer, LogReader
from can.formated_io import ASCWriter
from can.formated_io import BLFReader, BLFWriter
from can.formated_io import CSVWriter
from can.formated_io import SqliteWriter, SqlReader

from can.util import set_logging_level

from can.message import Message
from can.bus import BusABC
from can.notifier import Notifier
from can.interfaces import VALID_INTERFACES
from . import interface

from can.broadcastmanager import send_periodic, \
    CyclicSendTaskABC, \
    LimitedDurationCyclicSendTaskABC, \
    ModifiableCyclicTaskABC, \
    MultiRateCyclicSendTaskABC, \
    RestartableCyclicTaskABC
