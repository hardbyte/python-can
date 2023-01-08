"""
The ``can`` package provides controller area network support for
Python developers; providing common abstractions to
different hardware devices, and a suite of utilities for sending and receiving
messages on a can bus.
"""

import logging
from typing import Dict, Any

__version__ = "4.1.0"

log = logging.getLogger("can")

rc: Dict[str, Any] = {}

from .listener import Listener, BufferedReader, RedirectReader, AsyncBufferedReader

from .exceptions import (
    CanError,
    CanInterfaceNotImplementedError,
    CanInitializationError,
    CanOperationError,
    CanTimeoutError,
)

from .util import set_logging_level

from .message import Message
from .bus import BusABC, BusState
from .thread_safe_bus import ThreadSafeBus
from .notifier import Notifier
from .interfaces import VALID_INTERFACES
from . import interface
from .interface import Bus, detect_available_configs
from .bit_timing import BitTiming

from .io import Logger, SizedRotatingLogger, Printer, LogReader, MessageSync
from .io import ASCWriter, ASCReader
from .io import BLFReader, BLFWriter
from .io import CanutilsLogReader, CanutilsLogWriter
from .io import CSVWriter, CSVReader
from .io import SqliteWriter, SqliteReader
from .io import TRCReader, TRCWriter, TRCFileVersion

from .broadcastmanager import (
    CyclicSendTaskABC,
    LimitedDurationCyclicSendTaskABC,
    ModifiableCyclicTaskABC,
    MultiRateCyclicSendTaskABC,
    RestartableCyclicTaskABC,
)
