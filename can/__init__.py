# coding: utf-8

"""
``can`` is an object-orient Controller Area Network (CAN) interface module.
"""

from __future__ import absolute_import

import logging

__version__ = "3.2.0-a0"

log = logging.getLogger('can')

rc = dict()


class CanError(IOError):
    """Indicates an error with the CAN network.

    """
    pass


from .listener import Listener, BufferedReader, RedirectReader
try:
    from .listener import AsyncBufferedReader
except ImportError:
    pass

from .io import Logger, Printer, LogReader, MessageSync
from .io import ASCWriter, ASCReader
from .io import BLFReader, BLFWriter
from .io import CanutilsLogReader, CanutilsLogWriter
from .io import CSVWriter, CSVReader
from .io import SqliteWriter, SqliteReader

from .util import set_logging_level

from .message import Message
from .bus import BusABC, BusState
from .thread_safe_bus import ThreadSafeBus
from .notifier import Notifier
from .interfaces import VALID_INTERFACES
from . import interface
from .interface import Bus, detect_available_configs

from .broadcastmanager import send_periodic, \
    CyclicSendTaskABC, \
    LimitedDurationCyclicSendTaskABC, \
    ModifiableCyclicTaskABC, \
    MultiRateCyclicSendTaskABC, \
    RestartableCyclicTaskABC
