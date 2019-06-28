# coding: utf-8

"""
``can`` is an object-orient Controller Area Network (CAN) interface module.
"""

import logging

__version__ = "3.2.0"

log = logging.getLogger("can")

rc = dict()


class CanError(IOError):
    """Indicates an error with the CAN network.

    """


from .listener import Listener, BufferedReader, RedirectReader, AsyncBufferedReader

from .io import Logger, Printer, LogReader, MessageSync
from .io import ASCWriter, ASCReader
from .io import BLFReader, BLFWriter
from .io import CanutilsLogReader, CanutilsLogWriter
from .io import CSVWriter, CSVReader
from .io import SqliteWriter, SqliteReader
try:
    from .io import MF4Writer, MF4Reader
except ImportError:
    pass

from .util import set_logging_level

from .message import Message
from .bus import BusABC, BusState
from .thread_safe_bus import ThreadSafeBus
from .notifier import Notifier
from .interfaces import VALID_INTERFACES
from . import interface
from .interface import Bus, detect_available_configs
from .bit_timing import BitTiming

from .broadcastmanager import (
    CyclicSendTaskABC,
    LimitedDurationCyclicSendTaskABC,
    ModifiableCyclicTaskABC,
    MultiRateCyclicSendTaskABC,
    RestartableCyclicTaskABC,
)
