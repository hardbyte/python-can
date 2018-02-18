"""
can is an object-orient Controller Area Network interface module.
"""
from __future__ import absolute_import

import logging

__version__ = "2.1.0"

log = logging.getLogger('can')

rc = dict()


class CanError(IOError):
    pass

from can.listener import Listener, BufferedReader, RedirectReader

from can.io import Logger, Printer, LogReader
from can.io import ASCWriter, ASCReader
from can.io import BLFReader, BLFWriter
from can.io import CanutilsLogReader, CanutilsLogWriter
from can.io import CSVWriter
from can.io import SqliteWriter, SqliteReader

from can.util import set_logging_level

from can.message import Message
from can.bus import BusABC
from can.notifier import Notifier
from can.interfaces import VALID_INTERFACES
from . import interface
from .interface import Bus

from can.broadcastmanager import send_periodic, \
    CyclicSendTaskABC, \
    LimitedDurationCyclicSendTaskABC, \
    ModifiableCyclicTaskABC, \
    MultiRateCyclicSendTaskABC, \
    RestartableCyclicTaskABC
